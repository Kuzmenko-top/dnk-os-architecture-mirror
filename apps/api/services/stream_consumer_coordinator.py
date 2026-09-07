# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/stream_consumer_coordinator.py"
# purpose: "Stream Consumer Coordinator with Rebalancing and Offset Management (DNK-STREAM-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from apps.api.db.models.stream_consumer_group import StreamConsumerGroup
from apps.api.db.models.stream_message import StreamMessage
from apps.api.services.event_stream_bus import EventStreamBusService


class StreamConsumerCoordinator:
    """
    Coordinates Consumer Groups, Partition Rebalancing, Offset Commits,
    and Consumer Lag Tracking for Event Streams.
    """

    def __init__(self, stream_bus: EventStreamBusService):
        self._bus = stream_bus
        self._groups: Dict[str, StreamConsumerGroup] = {}  # group_id -> StreamConsumerGroup
        self._group_members: Dict[str, Set[str]] = {}  # group_id -> set of member_ids
        self._partition_assignments: Dict[str, Dict[str, List[int]]] = {}  # group_id -> {member_id: [partitions]}
        self._committed_offsets: Dict[str, Dict[int, int]] = {}  # group_id -> {partition: offset}
        self._lock = threading.RLock()

    def register_consumer_group(
        self,
        group_id: str,
        topic_name: str,
        workspace_id: str = "ws-alpha-001",
        auto_offset_reset: str = "earliest",
        strategy: str = "ROUND_ROBIN",
    ) -> StreamConsumerGroup:
        """Registers a new consumer group or retrieves existing."""
        with self._lock:
            if group_id in self._groups:
                return self._groups[group_id]

            group = StreamConsumerGroup(
                id=group_id,
                workspace_id=workspace_id,
                topic_name=topic_name,
                state="STABLE",
                auto_offset_reset=auto_offset_reset,
                rebalance_generation=1,
                members=[],
                committed_offsets={},
                lag_metrics={},
            )
            self._groups[group_id] = group
            self._group_members[group_id] = set()
            self._partition_assignments[group_id] = {}
            self._committed_offsets[group_id] = {}
            return group

    def join_group(self, group_id: str, member_id: Optional[str] = None) -> Dict[str, Any]:
        """Joins a consumer member to a group and triggers rebalance."""
        with self._lock:
            if group_id not in self._groups:
                raise ValueError(f"Consumer group '{group_id}' not found.")

            if not member_id:
                member_id = f"consumer_{uuid.uuid4().hex[:8]}"

            self._group_members[group_id].add(member_id)
            group = self._groups[group_id]
            group.members = list(self._group_members[group_id])
            group.rebalance_generation += 1
            group.state = "REBALANCING"

            # Execute partition assignment
            self._rebalance(group_id)
            group.state = "STABLE"

            return {
                "group_id": group_id,
                "member_id": member_id,
                "generation": group.rebalance_generation,
                "assigned_partitions": self._partition_assignments[group_id].get(member_id, []),
            }

    def leave_group(self, group_id: str, member_id: str) -> bool:
        """Removes a consumer member from a group and rebalances."""
        with self._lock:
            if group_id not in self._groups:
                return False

            if member_id in self._group_members[group_id]:
                self._group_members[group_id].remove(member_id)
                group = self._groups[group_id]
                group.members = list(self._group_members[group_id])
                group.rebalance_generation += 1
                self._rebalance(group_id)
                return True
            return False

    def _rebalance(self, group_id: str) -> None:
        """Assigns topic partitions evenly across all active group members."""
        group = self._groups[group_id]
        topic = self._bus.get_topic(group.topic_name)
        if not topic:
            return

        members = sorted(list(self._group_members[group_id]))
        num_partitions = topic.partitions_count
        assignments: Dict[str, List[int]] = {m: [] for m in members}

        if members:
            # Round-robin assignment strategy
            for p in range(num_partitions):
                member_idx = p % len(members)
                assignments[members[member_idx]].append(p)

        self._partition_assignments[group_id] = assignments

    def poll(
        self,
        group_id: str,
        member_id: str,
        max_records: int = 100,
    ) -> List[StreamMessage]:
        """Polls messages for the partitions assigned to the specific member."""
        with self._lock:
            if group_id not in self._groups:
                raise ValueError(f"Group '{group_id}' not found.")

            assigned_partitions = self._partition_assignments[group_id].get(member_id, [])
            if not assigned_partitions:
                return []

            group = self._groups[group_id]
            topic_name = group.topic_name
            records: List[StreamMessage] = []

            for partition in assigned_partitions:
                # Determine starting offset
                if partition in self._committed_offsets[group_id]:
                    start_offset = self._committed_offsets[group_id][partition] + 1
                else:
                    if group.auto_offset_reset == "earliest":
                        start_offset = 0
                    else:
                        # latest
                        latest_off = self._bus.get_partition_offset(topic_name, partition)
                        start_offset = max(0, latest_off)

                msgs = self._bus.consume(
                    topic_name=topic_name,
                    partition=partition,
                    from_offset=start_offset,
                    limit=max_records - len(records),
                )
                records.extend(msgs)
                if len(records) >= max_records:
                    break

            return records

    def commit_offset(self, group_id: str, partition: int, offset: int) -> Dict[str, Any]:
        """Commits processed offset for a partition."""
        with self._lock:
            if group_id not in self._groups:
                raise ValueError(f"Group '{group_id}' not found.")

            self._committed_offsets[group_id][partition] = offset
            group = self._groups[group_id]
            group.committed_offsets = dict(self._committed_offsets[group_id])

            # Update lag metric for partition
            latest_offset = self._bus.get_partition_offset(group.topic_name, partition)
            lag = max(0, latest_offset - (offset + 1))
            lags: Dict[str, Any] = dict(group.lag_metrics or {})
            lags[f"partition_{partition}"] = {
                "committed_offset": offset,
                "latest_offset": latest_offset,
                "lag": lag,
            }
            group.lag_metrics = lags

            return {
                "group_id": group_id,
                "partition": partition,
                "committed_offset": offset,
                "lag": lag,
            }

    def get_group_lag(self, group_id: str) -> Dict[str, Any]:
        """Calculates total and per-partition consumer lag for a group."""
        with self._lock:
            if group_id not in self._groups:
                raise ValueError(f"Group '{group_id}' not found.")

            group = self._groups[group_id]
            topic = self._bus.get_topic(group.topic_name)
            if not topic:
                return {"total_lag": 0, "partitions": {}}

            total_lag = 0
            partition_lags: Dict[str, Any] = {}

            for p in range(topic.partitions_count):
                latest_offset = self._bus.get_partition_offset(group.topic_name, p)
                committed = self._committed_offsets[group_id].get(p, -1)
                lag = max(0, latest_offset - (committed + 1)) if committed >= 0 else latest_offset
                total_lag += lag
                partition_lags[str(p)] = {
                    "partition": p,
                    "committed_offset": committed,
                    "latest_offset": latest_offset,
                    "lag": lag,
                }

            return {
                "group_id": group_id,
                "topic_name": group.topic_name,
                "total_lag": total_lag,
                "partitions": partition_lags,
                "members_count": len(self._group_members.get(group_id, set())),
            }

    def get_group(self, group_id: str) -> Optional[StreamConsumerGroup]:
        """Returns consumer group metadata."""
        with self._lock:
            return self._groups.get(group_id)

    def list_groups(self, workspace_id: Optional[str] = None) -> List[StreamConsumerGroup]:
        """Lists all consumer groups."""
        with self._lock:
            groups = list(self._groups.values())
            if workspace_id:
                groups = [g for g in groups if g.workspace_id == workspace_id]
            return groups