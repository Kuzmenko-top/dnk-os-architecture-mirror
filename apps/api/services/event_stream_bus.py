# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/event_stream_bus.py"
# purpose: "High-Throughput Partitioned Event Stream Bus Service (DNK-STREAM-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import hashlib
import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from apps.api.db.models.stream_message import StreamMessage
from apps.api.db.models.stream_topic import StreamTopic


class TopicNotFoundError(Exception):
    pass


class EventStreamBusService:
    """Core in-memory partitioned event streaming bus with deduplication and offset tracking."""

    def __init__(self):
        self._topics: Dict[str, StreamTopic] = {}
        # topic_name -> partition_id -> list of StreamMessage
        self._partitions: Dict[str, Dict[int, List[StreamMessage]]] = {}
        # topic_name -> partition_id -> next_offset
        self._offsets: Dict[str, Dict[int, int]] = {}
        # dedup_hash -> timestamp
        self._dedup_cache: Dict[str, datetime] = {}
        self._round_robin_counters: Dict[str, int] = {}
        self._lock = threading.RLock()

    def create_topic(
        self,
        name: str,
        partitions_count: int = 3,
        retention_hours: int = 168,
        cleanup_policy: str = "DELETE",
        schema_id: Optional[str] = None,
        workspace_id: str = "ws-default",
    ) -> StreamTopic:
        """Initializes a new partitioned stream topic."""
        with self._lock:
            if name in self._topics:
                return self._topics[name]

            topic = StreamTopic(
                name=name,
                partitions_count=partitions_count,
                retention_hours=retention_hours,
                cleanup_policy=cleanup_policy,
                schema_id=schema_id,
                workspace_id=workspace_id,
            )
            self._topics[name] = topic
            self._partitions[name] = {p: [] for p in range(partitions_count)}
            self._offsets[name] = {p: 0 for p in range(partitions_count)}
            self._round_robin_counters[name] = 0
            return topic

    def get_topic(self, name: str) -> Optional[StreamTopic]:
        """Gets topic metadata by name."""
        return self._topics.get(name)

    def list_topics(self, workspace_id: str = "ws-default") -> List[StreamTopic]:
        """Lists all active topics for workspace."""
        return [t for t in self._topics.values() if t.workspace_id == workspace_id and t.is_active]

    def _determine_partition(self, topic: StreamTopic, key: Optional[str]) -> int:
        """Determines partition index using key hash or round-robin."""
        if key:
            key_hash = int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16)
            return key_hash % topic.partitions_count

        rr_idx = self._round_robin_counters[topic.name]
        partition = rr_idx % topic.partitions_count
        self._round_robin_counters[topic.name] = (rr_idx + 1) % topic.partitions_count
        return partition

    def _compute_dedup_hash(self, topic_name: str, key: Optional[str], payload: Dict[str, Any]) -> str:
        """Computes deterministic deduplication hash."""
        raw = f"{topic_name}:{key or ''}:{json.dumps(payload, sort_keys=True)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def publish(
        self,
        topic_name: str,
        payload: Dict[str, Any],
        key: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        schema_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        workspace_id: str = "ws-default",
    ) -> Tuple[StreamMessage, bool]:
        """
        Publishes a message to the specified topic.
        Returns (StreamMessage, is_duplicate).
        """
        with self._lock:
            if topic_name not in self._topics:
                # Auto-create topic if not explicitly initialized
                self.create_topic(name=topic_name, workspace_id=workspace_id)

            topic = self._topics[topic_name]
            dedup_hash = idempotency_key or self._compute_dedup_hash(topic_name, key, payload)

            if dedup_hash in self._dedup_cache:
                # Duplicate detected: retrieve existing message if available
                # or return a synthetic envelope indicating duplicate
                partition = self._determine_partition(topic, key)
                existing_messages = self._partitions[topic_name][partition]
                for msg in reversed(existing_messages):
                    if msg.dedup_hash == dedup_hash:
                        return msg, True

            partition = self._determine_partition(topic, key)
            curr_offset = self._offsets[topic_name][partition]
            self._offsets[topic_name][partition] += 1

            msg = StreamMessage(
                workspace_id=workspace_id,
                topic_name=topic_name,
                partition=partition,
                offset=curr_offset,
                key=key,
                payload=payload,
                headers=headers or {},
                schema_id=schema_id or topic.schema_id,
                dedup_hash=dedup_hash,
                trace_id=trace_id,
                timestamp=datetime.now(timezone.utc),
            )

            self._partitions[topic_name][partition].append(msg)
            self._dedup_cache[dedup_hash] = msg.timestamp
            return msg, False

    def fetch_messages(
        self,
        topic_name: str,
        partition: int,
        offset: int = 0,
        max_messages: int = 100,
    ) -> List[StreamMessage]:
        """Fetches messages from a partition starting from the specified offset."""
        with self._lock:
            if topic_name not in self._topics:
                raise TopicNotFoundError(f"Topic '{topic_name}' does not exist.")

            topic = self._topics[topic_name]
            if partition not in self._partitions[topic_name]:
                return []

            partition_messages = self._partitions[topic_name][partition]
            # Filter messages >= offset
            matching = [m for m in partition_messages if m.offset >= offset]
            return matching[:max_messages]

    def get_partition_offsets(self, topic_name: str) -> Dict[int, int]:
        """Returns the latest high watermark offset for each partition."""
        with self._lock:
            if topic_name not in self._topics:
                raise TopicNotFoundError(f"Topic '{topic_name}' does not exist.")
            return dict(self._offsets[topic_name])

    def get_partition_offset(self, topic_name: str, partition: int) -> int:
        """Returns the latest offset in the specified partition."""
        with self._lock:
            if topic_name not in self._topics:
                return 0
            return self._offsets.get(topic_name, {}).get(partition, 0)

    def consume(
        self,
        topic_name: str,
        partition: int,
        from_offset: int = 0,
        limit: int = 100,
    ) -> List[StreamMessage]:
        """Alias for fetch_messages."""
        return self.fetch_messages(
            topic_name=topic_name,
            partition=partition,
            offset=from_offset,
            max_messages=limit,
        )
