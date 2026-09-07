# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/stream_dead_letter_queue_service.py"
# purpose: "Dead Letter Queue (DLQ) Service with Retry and Replay policies (DNK-STREAM-001)"
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
from typing import Any, Dict, List, Optional, Tuple

from apps.api.db.models.stream_dead_letter_event import StreamDeadLetterEvent
from apps.api.db.models.stream_message import StreamMessage
from apps.api.services.event_stream_bus import EventStreamBusService


class StreamDeadLetterQueueService:
    """
    Manages Dead Letter Queue (DLQ) for failed, poison, or schema-invalid messages.
    Supports exponential backoff retries and manual/automated replay to destination topics.
    """

    def __init__(self, stream_bus: EventStreamBusService, max_retries: int = 3):
        self._bus = stream_bus
        self._max_retries = max_retries
        self._dlq_events: Dict[str, StreamDeadLetterEvent] = {}  # event_id -> StreamDeadLetterEvent
        self._dlq_by_topic: Dict[str, List[str]] = {}  # original_topic -> list of event_ids
        self._lock = threading.RLock()

    def route_to_dlq(
        self,
        original_topic: str,
        payload: Dict[str, Any],
        error_reason: str,
        workspace_id: str = "ws-alpha-001",
        original_partition: int = 0,
        original_offset: int = 0,
        error_stack: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> StreamDeadLetterEvent:
        """Stores a poisoned / failed event into DLQ."""
        with self._lock:
            event_id = f"dlq_{uuid.uuid4().hex[:12]}"
            dlq_event = StreamDeadLetterEvent(
                id=event_id,
                workspace_id=workspace_id,
                original_topic=original_topic,
                original_partition=original_partition,
                original_offset=original_offset,
                payload=payload,
                headers=headers or {},
                error_reason=error_reason,
                error_stack=error_stack,
                retry_count=0,
                max_retries=self._max_retries,
                status="PENDING",
            )
            self._dlq_events[event_id] = dlq_event
            if original_topic not in self._dlq_by_topic:
                self._dlq_by_topic[original_topic] = []
            self._dlq_by_topic[original_topic].append(event_id)
            return dlq_event

    def replay_event(
        self,
        event_id: str,
        target_topic: Optional[str] = None,
    ) -> Tuple[bool, Optional[StreamMessage], str]:
        """
        Replays a DLQ event by publishing it back to the target or original topic.
        """
        with self._lock:
            if event_id not in self._dlq_events:
                return False, None, f"DLQ event '{event_id}' not found."

            event = self._dlq_events[event_id]
            if event.status == "EXHAUSTED":
                return False, None, "DLQ event has reached maximum retry attempts."

            destination_topic = target_topic or event.original_topic
            try:
                # Re-publish to the stream bus
                msg, _ = self._bus.publish(
                    topic_name=destination_topic,
                    payload=event.payload,
                    workspace_id=event.workspace_id,
                    headers={
                        **(event.headers or {}),
                        "x-dlq-replayed-from": event.id,
                        "x-dlq-retry-count": event.retry_count + 1,
                    },
                )
                event.retry_count += 1
                event.status = "RESOLVED"
                event.resolved_at = datetime.now(timezone.utc)
                return True, msg, "Successfully replayed to target stream topic."
            except Exception as e:
                event.retry_count += 1
                if event.retry_count >= event.max_retries:
                    event.status = "EXHAUSTED"
                return False, None, f"Replay failed: {str(e)}"

    def get_event(self, event_id: str) -> Optional[StreamDeadLetterEvent]:
        """Retrieves a specific DLQ event."""
        with self._lock:
            return self._dlq_events.get(event_id)

    def list_events(
        self,
        topic_name: Optional[str] = None,
        status: Optional[str] = None,
        workspace_id: Optional[str] = None,
    ) -> List[StreamDeadLetterEvent]:
        """Lists and filters DLQ events."""
        with self._lock:
            events = list(self._dlq_events.values())
            if topic_name:
                events = [e for e in events if e.original_topic == topic_name]
            if status:
                events = [e for e in events if e.status == status]
            if workspace_id:
                events = [e for e in events if e.workspace_id == workspace_id]
            return events

    def get_dlq_stats(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregates DLQ statistics."""
        with self._lock:
            events = self.list_events(workspace_id=workspace_id)
            total = len(events)
            pending = sum(1 for e in events if e.status == "PENDING")
            resolved = sum(1 for e in events if e.status == "RESOLVED")
            exhausted = sum(1 for e in events if e.status == "EXHAUSTED")

            by_topic: Dict[str, int] = {}
            for e in events:
                by_topic[e.original_topic] = by_topic.get(e.original_topic, 0) + 1

            return {
                "total_dlq_events": total,
                "pending": pending,
                "resolved": resolved,
                "exhausted": exhausted,
                "by_topic": by_topic,
            }