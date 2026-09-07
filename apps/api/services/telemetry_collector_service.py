# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/telemetry_collector_service.py"
# purpose: "OpenTelemetry Collector & Exporter Service for Distributed Tracing (DNK-OBSERVE-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import math
import random
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from apps.api.db.models.trace_span import TraceSpan
from apps.api.db.models.trace_service import TraceService
from apps.api.db.models.trace_context import TraceContext
from apps.api.db.models.span_event import SpanEvent
from apps.api.db.models.span_link import SpanLink
from apps.api.db.models.trace_metric_aggregation import TraceMetricAggregation


class TelemetryCollectorService:
    """
    High-performance OpenTelemetry collector and exporter engine.
    Supports OTLP JSON/dictionary ingestion, tail sampling, in-memory micro-batching,
    service topology graph calculation, and metric aggregation.
    """

    def __init__(
        self,
        batch_size: int = 50,
        flush_interval_ms: int = 2000,
        sample_rate: float = 1.0,
        always_sample_errors: bool = True,
        slow_trace_threshold_ms: float = 500.0,
    ):
        self.batch_size = batch_size
        self.flush_interval_ms = flush_interval_ms
        self.sample_rate = sample_rate
        self.always_sample_errors = always_sample_errors
        self.slow_trace_threshold_ms = slow_trace_threshold_ms

        self._buffer: List[TraceSpan] = []
        self._stored_spans: Dict[str, TraceSpan] = {}  # span_id -> TraceSpan
        self._traces_index: Dict[str, List[str]] = {}  # trace_id -> [span_id, ...]
        self._services: Dict[str, TraceService] = {}  # service_name -> TraceService
        self._exporters: Dict[str, Callable[[List[Dict[str, Any]]], None]] = {}
        self._lock = threading.RLock()
        self._last_flush_time = time.time()

        # Default in-memory exporter sink buffer
        self._exported_batches: List[List[Dict[str, Any]]] = []

    # -------------------------------------------------------------------------
    # Service Registry Management
    # -------------------------------------------------------------------------
    def register_service(
        self,
        name: str,
        environment: str = "production",
        version: str = "1.0.0",
        runtime: str = "Python 3.12 / FastAPI",
        health_status: str = "HEALTHY",
        metadata_info: Optional[Dict[str, Any]] = None,
        workspace_id: str = "ws-default",
    ) -> Dict[str, Any]:
        """Registers or updates a microservice/agent in the trace topology registry."""
        with self._lock:
            service = TraceService(
                name=name,
                environment=environment,
                version=version,
                runtime=runtime,
                health_status=health_status,
                metadata_info=metadata_info or {},
                workspace_id=workspace_id,
            )
            self._services[name] = service
            return service.to_dict()

    def get_service(self, name: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            srv = self._services.get(name)
            return srv.to_dict() if srv else None

    def list_services(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [s.to_dict() for s in self._services.values()]

    # -------------------------------------------------------------------------
    # Exporter Registration
    # -------------------------------------------------------------------------
    def register_exporter(self, name: str, exporter_fn: Callable[[List[Dict[str, Any]]], None]) -> None:
        """Registers a sink exporter (e.g. ClickHouse, Jaeger, Tempo, CloudWatch)."""
        with self._lock:
            self._exporters[name] = exporter_fn

    # -------------------------------------------------------------------------
    # Tail Sampling Logic
    # -------------------------------------------------------------------------
    def should_sample(self, span: TraceSpan) -> bool:
        """
        Determines whether a span should be retained based on tail-sampling rules:
        1. All errors (status_code == 'ERROR' or exception event) are sampled if always_sample_errors=True.
        2. All slow traces (> slow_trace_threshold_ms) are sampled.
        3. Probabilistic sampling (sample_rate).
        """
        if self.always_sample_errors and span.status_code == "ERROR":
            return True
        if self.always_sample_errors and any(
            isinstance(e, dict) and (e.get("name") == "exception" or "error" in str(e).lower())
            for e in (span.events or [])
        ):
            return True
        if span.duration_ms >= self.slow_trace_threshold_ms:
            return True
        if self.sample_rate >= 1.0:
            return True
        if self.sample_rate <= 0.0:
            return False
        return random.random() < self.sample_rate

    # -------------------------------------------------------------------------
    # Ingestion Methods
    # -------------------------------------------------------------------------
    def ingest_span(self, span_data: Union[Dict[str, Any], TraceSpan]) -> Dict[str, Any]:
        """Ingests a single span dict or TraceSpan instance, checks sampling, buffers and automatically registers service."""
        with self._lock:
            if isinstance(span_data, TraceSpan):
                span = span_data
            else:
                span = TraceSpan(
                    id=span_data.get("id"),
                    workspace_id=span_data.get("workspace_id", "ws-default"),
                    trace_id=span_data.get("trace_id") or uuid.uuid4().hex[:32],
                    span_id=span_data.get("span_id") or uuid.uuid4().hex[:16],
                    parent_span_id=span_data.get("parent_span_id"),
                    service_name=span_data.get("service_name", "unknown_service"),
                    name=span_data.get("name", "unnamed_operation"),
                    kind=span_data.get("kind", "INTERNAL"),
                    status_code=span_data.get("status_code", "OK"),
                    status_message=span_data.get("status_message"),
                    start_time=span_data.get("start_time") or datetime.now(timezone.utc),
                    end_time=span_data.get("end_time"),
                    duration_ms=float(span_data.get("duration_ms", 0.0)),
                    attributes=span_data.get("attributes") or {},
                    events=span_data.get("events") or [],
                    links=span_data.get("links") or [],
                    is_root=span_data.get("is_root") if span_data.get("is_root") is not None else (span_data.get("parent_span_id") is None),
                )

            # Auto-register service if not present
            if span.service_name not in self._services:
                self.register_service(name=span.service_name, workspace_id=span.workspace_id)

            if not self.should_sample(span):
                return {"status": "dropped_by_sampling", "span_id": span.span_id, "trace_id": span.trace_id}

            self._buffer.append(span)

            if len(self._buffer) >= self.batch_size:
                self.flush()

            return {"status": "buffered", "span_id": span.span_id, "trace_id": span.trace_id}

    def ingest_spans(self, spans_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Batch ingestion of multiple spans."""
        ingested_count = 0
        dropped_count = 0
        for span_data in spans_data:
            res = self.ingest_span(span_data)
            if res.get("status") == "buffered":
                ingested_count += 1
            else:
                dropped_count += 1
        return {
            "total_submitted": len(spans_data),
            "ingested_count": ingested_count,
            "dropped_count": dropped_count,
            "buffer_size": len(self._buffer),
        }

    def ingest_otlp_json(self, otlp_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parses and ingests OpenTelemetry standard JSON payloads:
        {
          "resourceSpans": [
            {
              "resource": { "attributes": [{ "key": "service.name", "value": {"stringValue": "..."}}]},
              "scopeSpans": [
                {
                  "spans": [...]
                }
              ]
            }
          ]
        }
        """
        parsed_spans: List[Dict[str, Any]] = []
        resource_spans = otlp_payload.get("resourceSpans", [])

        for r_span in resource_spans:
            # Extract service name from resource attributes
            service_name = "unknown_service"
            r_attrs = r_span.get("resource", {}).get("attributes", [])
            for attr in r_attrs:
                if attr.get("key") == "service.name":
                    service_name = attr.get("value", {}).get("stringValue", service_name)

            for s_span in r_span.get("scopeSpans", []):
                for sp in s_span.get("spans", []):
                    # Convert timestamps if provided in nanoseconds (OTLP standard)
                    start_nano = int(sp.get("startTimeUnixNano", 0))
                    end_nano = int(sp.get("endTimeUnixNano", 0))
                    duration_ms = 0.0
                    if start_nano and end_nano:
                        duration_ms = (end_nano - start_nano) / 1_000_000.0

                    status_obj = sp.get("status", {})
                    status_code = "OK"
                    if status_obj.get("code") in [2, "STATUS_CODE_ERROR", "ERROR"]:
                        status_code = "ERROR"
                    elif status_obj.get("code") in [0, "STATUS_CODE_UNSET", "UNSET"]:
                        status_code = "UNSET"

                    # Parse attributes
                    attributes = {}
                    for a in sp.get("attributes", []):
                        val_obj = a.get("value", {})
                        val = next(iter(val_obj.values())) if val_obj else None
                        attributes[a.get("key")] = val

                    span_dict = {
                        "trace_id": sp.get("traceId"),
                        "span_id": sp.get("spanId"),
                        "parent_span_id": sp.get("parentSpanId"),
                        "service_name": service_name,
                        "name": sp.get("name", "otlp_operation"),
                        "kind": sp.get("kind", "INTERNAL"),
                        "status_code": status_code,
                        "status_message": status_obj.get("message"),
                        "duration_ms": duration_ms,
                        "attributes": attributes,
                        "events": sp.get("events", []),
                        "links": sp.get("links", []),
                    }
                    parsed_spans.append(span_dict)

        return self.ingest_spans(parsed_spans)

    # -------------------------------------------------------------------------
    # Buffer Flush & Persistence
    # -------------------------------------------------------------------------
    def flush(self) -> int:
        """Flushes buffered spans into internal store and calls registered exporters."""
        with self._lock:
            if not self._buffer:
                return 0

            batch_to_export = self._buffer[:]
            self._buffer.clear()
            self._last_flush_time = time.time()

            # Store spans and update trace index
            for span in batch_to_export:
                self._stored_spans[span.span_id] = span
                if span.trace_id not in self._traces_index:
                    self._traces_index[span.trace_id] = []
                if span.span_id not in self._traces_index[span.trace_id]:
                    self._traces_index[span.trace_id].append(span.span_id)

            # Export serialized batch
            serialized_batch = [s.to_dict() for s in batch_to_export]
            self._exported_batches.append(serialized_batch)

            for exp_name, exp_fn in self._exporters.items():
                try:
                    exp_fn(serialized_batch)
                except Exception:
                    pass  # Keep resilient even if external exporter fails

            return len(batch_to_export)

    # -------------------------------------------------------------------------
    # Query & Analysis API
    # -------------------------------------------------------------------------
    def get_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        """Returns all spans for a trace_id sorted by start_time."""
        with self._lock:
            self.flush()  # Ensure buffer is persisted
            span_ids = self._traces_index.get(trace_id, [])
            spans = [self._stored_spans[sid].to_dict() for sid in span_ids if sid in self._stored_spans]
            spans.sort(key=lambda x: x.get("start_time", ""))
            return spans

    def list_traces(
        self,
        service_name: Optional[str] = None,
        status_code: Optional[str] = None,
        min_duration_ms: Optional[float] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Queries traces matching filters with aggregated trace-level overview."""
        with self._lock:
            self.flush()
            matched_traces: List[Dict[str, Any]] = []

            for trace_id, span_ids in self._traces_index.items():
                spans = [self._stored_spans[sid] for sid in span_ids if sid in self._stored_spans]
                if not spans:
                    continue

                # Check filters
                if service_name and not any(s.service_name == service_name for s in spans):
                    continue
                if status_code and not any(s.status_code == status_code for s in spans):
                    continue
                root_span = next((s for s in spans if s.is_root or not s.parent_span_id), spans[0])
                total_duration = max((s.duration_ms for s in spans), default=0.0)
                if min_duration_ms and total_duration < min_duration_ms:
                    continue

                has_error = any(s.status_code == "ERROR" for s in spans)
                services_involved = list({s.service_name for s in spans})

                matched_traces.append({
                    "trace_id": trace_id,
                    "root_service": root_span.service_name,
                    "root_operation": root_span.name,
                    "span_count": len(spans),
                    "services": services_involved,
                    "duration_ms": total_duration,
                    "has_error": has_error,
                    "start_time": root_span.start_time.isoformat() if isinstance(root_span.start_time, datetime) else str(root_span.start_time or ""),
                })

                if len(matched_traces) >= limit:
                    break

            return matched_traces

    def get_service_topology(self) -> Dict[str, Any]:
        """
        Computes dependency topology graph between services based on parent-child span calls.
        Returns nodes (services) and edges (caller -> callee calls with call counts and latency).
        """
        with self._lock:
            self.flush()
            nodes: Dict[str, Dict[str, Any]] = {}
            edges: Dict[Tuple[str, str], Dict[str, Any]] = {}

            # Populate nodes
            for s_name, s_obj in self._services.items():
                nodes[s_name] = s_obj.to_dict()

            # Inspect span relationships
            for span in self._stored_spans.values():
                if span.service_name not in nodes:
                    nodes[span.service_name] = {
                        "name": span.service_name,
                        "health_status": "HEALTHY",
                        "environment": "production",
                    }

                if span.parent_span_id and span.parent_span_id in self._stored_spans:
                    parent_span = self._stored_spans[span.parent_span_id]
                    if parent_span.service_name != span.service_name:
                        edge_key = (parent_span.service_name, span.service_name)
                        if edge_key not in edges:
                            edges[edge_key] = {
                                "source": parent_span.service_name,
                                "target": span.service_name,
                                "call_count": 0,
                                "error_count": 0,
                                "total_duration_ms": 0.0,
                            }
                        edges[edge_key]["call_count"] += 1
                        edges[edge_key]["total_duration_ms"] += span.duration_ms
                        if span.status_code == "ERROR":
                            edges[edge_key]["error_count"] += 1

            edge_list = []
            for edge_info in edges.values():
                c = edge_info["call_count"]
                edge_info["avg_duration_ms"] = (edge_info["total_duration_ms"] / c) if c > 0 else 0.0
                edge_info["error_rate"] = (edge_info["error_count"] / c) if c > 0 else 0.0
                edge_list.append(edge_info)

            return {
                "nodes": list(nodes.values()),
                "edges": edge_list,
                "total_services": len(nodes),
                "total_dependencies": len(edge_list),
            }

    def compute_aggregations(
        self,
        service_name: Optional[str] = None,
        operation: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calculates p50, p95, p99 percentiles, error rate, and call count per service/operation.
        """
        with self._lock:
            self.flush()
            groups: Dict[Tuple[str, str], List[TraceSpan]] = {}

            for span in self._stored_spans.values():
                if service_name and span.service_name != service_name:
                    continue
                if operation and span.name != operation:
                    continue

                key = (span.service_name, span.name)
                if key not in groups:
                    groups[key] = []
                groups[key].append(span)

            aggregations: List[Dict[str, Any]] = []
            now = datetime.now(timezone.utc)

            for (s_name, op_name), span_list in groups.items():
                durations = sorted([s.duration_ms for s in span_list])
                count = len(durations)
                if count == 0:
                    continue

                errors = sum(1 for s in span_list if s.status_code == "ERROR")
                err_rate = errors / count

                p50 = durations[int(0.50 * count)]
                p95 = durations[min(int(0.95 * count), count - 1)]
                p99 = durations[min(int(0.99 * count), count - 1)]
                min_val = durations[0]
                max_val = durations[-1]
                avg_val = sum(durations) / count

                agg = TraceMetricAggregation(
                    service_name=s_name,
                    operation=op_name,
                    time_bucket=now,
                    call_count=count,
                    error_count=errors,
                    error_rate=err_rate,
                    p50_ms=p50,
                    p95_ms=p95,
                    p99_ms=p99,
                    min_ms=min_val,
                    max_ms=max_val,
                    avg_ms=avg_val,
                )
                aggregations.append(agg.to_dict())

            return aggregations


_default_collector_instance: Optional[TelemetryCollectorService] = None


def get_default_collector() -> TelemetryCollectorService:
    """Retrieve or initialize the default global TelemetryCollectorService singleton."""
    global _default_collector_instance
    if _default_collector_instance is None:
        _default_collector_instance = TelemetryCollectorService()
    return _default_collector_instance


def set_default_collector(collector: Optional[TelemetryCollectorService]):
    """Override or reset the default global TelemetryCollectorService singleton."""
    global _default_collector_instance
    _default_collector_instance = collector

