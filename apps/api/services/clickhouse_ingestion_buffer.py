# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/clickhouse_ingestion_buffer.py"
# purpose: "ClickHouse Ingestion Buffer and Micro-Batch Sink Service (DNK-STREAM-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import json
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from apps.api.db.models.stream_ingestion_sink import StreamIngestionSink
from apps.api.db.models.stream_message import StreamMessage


class ClickHouseIngestionBufferService:
    """Manages micro-batch buffering, batch size thresholds, and simulated ClickHouse bulk ingestion."""

    def __init__(self):
        self._sinks: Dict[str, StreamIngestionSink] = {}
        # sink_id -> list of buffered raw rows
        self._buffers: Dict[str, List[Dict[str, Any]]] = {}
        # sink_id -> list of flushed batch records
        self._flushed_batches: Dict[str, List[List[Dict[str, Any]]]] = {}
        self._lock = threading.RLock()

    def register_sink(
        self,
        name: str,
        source_topic: str,
        target_table: str,
        sink_type: str = "CLICKHOUSE",
        batch_size: int = 1000,
        flush_interval_ms: int = 5000,
        sink_config: Optional[Dict[str, Any]] = None,
        workspace_id: str = "ws-default",
    ) -> StreamIngestionSink:
        """Registers a new analytical ingestion sink."""
        with self._lock:
            sink = StreamIngestionSink(
                name=name,
                source_topic=source_topic,
                target_table=target_table,
                sink_type=sink_type,
                batch_size=batch_size,
                flush_interval_ms=flush_interval_ms,
                sink_config=sink_config or {},
                workspace_id=workspace_id,
            )
            self._sinks[sink.id] = sink
            self._buffers[sink.id] = []
            self._flushed_batches[sink.id] = []
            return sink

    def ingest_message(self, sink_id: str, message: StreamMessage) -> Dict[str, Any]:
        """Ingests a message into the sink buffer, auto-flushing if batch threshold is reached."""
        with self._lock:
            sink = self._sinks.get(sink_id)
            if not sink:
                raise ValueError(f"Sink '{sink_id}' not found.")

            row = {
                "message_id": message.id,
                "topic": message.topic_name,
                "partition": message.partition,
                "offset": message.offset,
                "key": message.key,
                "payload": json.dumps(message.payload),
                "headers": json.dumps(message.headers),
                "timestamp": message.timestamp.isoformat() if message.timestamp else datetime.now(timezone.utc).isoformat(),
            }

            self._buffers[sink_id].append(row)
            stats: Dict[str, Any] = dict(sink.buffer_stats or {})
            stats["buffered_count"] = len(self._buffers[sink_id])
            sink.buffer_stats = stats

            flushed = False
            if len(self._buffers[sink_id]) >= sink.batch_size:
                self._flush_internal(sink)
                flushed = True

            return {
                "sink_id": sink.id,
                "buffered_count": len(self._buffers[sink_id]),
                "flushed": flushed,
            }

    def flush(self, sink_id: str) -> Dict[str, Any]:
        """Explicitly flushes the buffer of a sink."""
        with self._lock:
            sink = self._sinks.get(sink_id)
            if not sink:
                raise ValueError(f"Sink '{sink_id}' not found.")
            batch_count = self._flush_internal(sink)
            return {
                "sink_id": sink.id,
                "flushed_count": batch_count,
                "target_table": sink.target_table,
            }

    def _flush_internal(self, sink: StreamIngestionSink) -> int:
        """Internal flush execution under lock."""
        buffer = self._buffers.get(sink.id, [])
        if not buffer:
            return 0

        batch = list(buffer)
        self._buffers[sink.id] = []
        self._flushed_batches[sink.id].append(batch)

        stats: Dict[str, Any] = dict(sink.buffer_stats or {})
        stats["buffered_count"] = 0
        stats["last_flush_at"] = datetime.now(timezone.utc).isoformat()
        stats["total_flushed"] = int(stats.get("total_flushed", 0)) + len(batch)
        sink.buffer_stats = stats
        return len(batch)

    def get_sink(self, sink_id: str) -> Optional[StreamIngestionSink]:
        return self._sinks.get(sink_id)

    def list_sinks(self, workspace_id: str = "ws-default") -> List[StreamIngestionSink]:
        return [s for s in self._sinks.values() if s.workspace_id == workspace_id]

    def get_flushed_batches(self, sink_id: str) -> List[List[Dict[str, Any]]]:
        return self._flushed_batches.get(sink_id, [])
