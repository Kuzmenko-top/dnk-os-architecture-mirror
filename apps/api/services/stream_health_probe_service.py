# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/stream_health_probe_service.py"
# purpose: "Stream Health Probe and End-to-End Latency Verification Service (DNK-STREAM-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apps.api.services.event_stream_bus import EventStreamBusService
from apps.api.services.stream_consumer_coordinator import StreamConsumerCoordinator


class StreamHealthProbeService:
    """
    Performs end-to-end synthetic heartbeat probes, latency tracking,
    and cluster health evaluation for Event Streaming Platform.
    """

    def __init__(
        self,
        stream_bus: EventStreamBusService,
        coordinator: StreamConsumerCoordinator,
    ):
        self._bus = stream_bus
        self._coordinator = coordinator
        self._probe_history: List[Dict[str, Any]] = []
        self._lock = threading.RLock()

    def run_e2e_probe(
        self,
        topic_name: str = "health.synthetic.probe",
        workspace_id: str = "ws-alpha-001",
    ) -> Dict[str, Any]:
        """
        Executes an end-to-end synthetic probe:
        1. Ensures synthetic topic exists
        2. Produces synthetic heartbeat message with timestamp
        3. Polls/reads message and measures end-to-end round-trip latency
        """
        start_time = time.perf_counter()
        probe_id = f"probe_{uuid.uuid4().hex[:8]}"

        with self._lock:
            # Step 1: Ensure topic exists
            if not self._bus.get_topic(topic_name):
                self._bus.create_topic(
                    name=topic_name,
                    workspace_id=workspace_id,
                    partitions_count=2,
                )

            # Step 2: Produce probe
            sent_timestamp = datetime.now(timezone.utc).isoformat()
            msg, is_dup = self._bus.publish(
                topic_name=topic_name,
                payload={"probe_id": probe_id, "timestamp": sent_timestamp, "kind": "E2E_HEARTBEAT"},
                key=probe_id,
                workspace_id=workspace_id,
            )

            # Step 3: Consume probe
            consumed_msgs = self._bus.consume(
                topic_name=topic_name,
                partition=msg.partition,
                from_offset=msg.offset,
                limit=1,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000.0
            is_success = len(consumed_msgs) > 0 and consumed_msgs[0].id == msg.id

            result = {
                "probe_id": probe_id,
                "topic_name": topic_name,
                "status": "HEALTHY" if is_success else "DEGRADED",
                "round_trip_latency_ms": round(latency_ms, 2),
                "published_offset": msg.offset,
                "partition": msg.partition,
                "success": is_success,
                "timestamp": sent_timestamp,
            }

            self._probe_history.append(result)
            if len(self._probe_history) > 100:
                self._probe_history = self._probe_history[-100:]

            return result

    def get_cluster_health(self, workspace_id: str = "ws-alpha-001") -> Dict[str, Any]:
        """Evaluates aggregate health across topics, consumer groups, and probes."""
        with self._lock:
            topics = self._bus.list_topics(workspace_id=workspace_id)
            groups = self._coordinator.list_groups(workspace_id=workspace_id)

            total_partitions = sum(t.partitions_count for t in topics)
            total_lag = 0
            for g in groups:
                lag_info = self._coordinator.get_group_lag(g.id)
                total_lag += lag_info.get("total_lag", 0)

            last_probe = self._probe_history[-1] if self._probe_history else None

            is_healthy = True
            if last_probe and not last_probe.get("success"):
                is_healthy = False
            if total_lag > 10000:
                is_healthy = False

            return {
                "status": "HEALTHY" if is_healthy else "DEGRADED",
                "topics_count": len(topics),
                "total_partitions": total_partitions,
                "consumer_groups_count": len(groups),
                "total_consumer_lag": total_lag,
                "last_e2e_probe": last_probe,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }