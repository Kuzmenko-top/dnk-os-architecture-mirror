# --- DNK-MRH-HEADER ---
# mrh_id: "tests/observe/test_trace_models.py"
# purpose: "Unit tests for Core ORM Models in Distributed Tracing Platform (DNK-OBSERVE-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone
from apps.api.db.models.trace_span import TraceSpan
from apps.api.db.models.trace_service import TraceService
from apps.api.db.models.trace_context import TraceContext
from apps.api.db.models.span_event import SpanEvent
from apps.api.db.models.span_link import SpanLink
from apps.api.db.models.trace_metric_aggregation import TraceMetricAggregation


class TestTraceModels:
    """Test suite for Phase 1 Tracing ORM Models."""

    def test_trace_span_defaults_and_to_dict(self):
        span = TraceSpan(
            service_name="dnk_api_gateway",
            name="GET /api/v1/stream/topics",
            kind="SERVER",
        )
        assert span.id.startswith("spn_")
        assert len(span.trace_id) == 32
        assert len(span.span_id) == 16
        assert span.parent_span_id is None
        assert span.is_root is True
        assert span.status_code == "OK"
        assert span.duration_ms == 0.0
        assert isinstance(span.attributes, dict)
        assert isinstance(span.events, list)
        assert isinstance(span.links, list)

        d = span.to_dict()
        assert d["service_name"] == "dnk_api_gateway"
        assert d["name"] == "GET /api/v1/stream/topics"
        assert d["is_root"] is True
        assert "start_time" in d
        assert "created_at" in d

    def test_trace_span_child_and_error_status(self):
        span = TraceSpan(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
            parent_span_id="5fb397be34d23b0f",
            service_name="dnk_event_stream_bus",
            name="StreamPublishEvent",
            kind="PRODUCER",
            status_code="ERROR",
            status_message="Schema validation failed",
            duration_ms=12.4,
            attributes={"stream.topic": "telemetry_events", "stream.partition": 2},
        )
        assert span.is_root is False
        assert span.status_code == "ERROR"
        assert span.status_message == "Schema validation failed"
        assert span.attributes["stream.topic"] == "telemetry_events"
        assert span.duration_ms == 12.4

        d = span.to_dict()
        assert d["parent_span_id"] == "5fb397be34d23b0f"
        assert d["status_code"] == "ERROR"

    def test_trace_service_defaults_and_to_dict(self):
        service = TraceService(
            name="dnk_a2a_agent_builder",
            environment="staging",
            version="1.2.0",
            runtime="Python 3.12 / FastAPI",
            health_status="HEALTHY",
            metadata_info={"cluster": "europe-west1", "replicas": 3},
        )
        assert service.id.startswith("srv_")
        assert service.name == "dnk_a2a_agent_builder"
        assert service.environment == "staging"
        assert service.health_status == "HEALTHY"

        d = service.to_dict()
        assert d["name"] == "dnk_a2a_agent_builder"
        assert d["metadata_info"]["cluster"] == "europe-west1"
        assert "created_at" in d
        assert "last_seen" in d

    def test_trace_context_w3c_traceparent(self):
        ctx = TraceContext(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
            trace_flags="01",
            trace_state="rojo=1,congo=2",
            baggage={"user.id": "usr_9912", "tier": "enterprise"},
        )
        expected_traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        assert ctx.to_w3c_traceparent() == expected_traceparent

        d = ctx.to_dict()
        assert d["traceparent"] == expected_traceparent
        assert d["trace_state"] == "rojo=1,congo=2"
        assert d["baggage"]["tier"] == "enterprise"
        assert d["sampled"] is True

    def test_span_event_defaults_and_to_dict(self):
        evt = SpanEvent(
            span_id="00f067aa0ba902b7",
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            name="exception",
            attributes={"exception.type": "ValueError", "exception.message": "Invalid partition"},
        )
        assert evt.id.startswith("spe_")
        assert evt.name == "exception"
        assert evt.attributes["exception.type"] == "ValueError"

        d = evt.to_dict()
        assert d["name"] == "exception"
        assert "timestamp" in d
        assert d["attributes"]["exception.type"] == "ValueError"

    def test_span_link_defaults_and_to_dict(self):
        link = SpanLink(
            source_span_id="00f067aa0ba902b7",
            linked_trace_id="7cf92f3577b34da6a3ce929d0e0e4799",
            linked_span_id="11f067aa0ba902aa",
            relationship_type="BATCH_ITEM",
            attributes={"batch.index": 4},
        )
        assert link.id.startswith("spl_")
        assert link.relationship_type == "BATCH_ITEM"
        assert link.attributes["batch.index"] == 4

        d = link.to_dict()
        assert d["source_span_id"] == "00f067aa0ba902b7"
        assert d["linked_trace_id"] == "7cf92f3577b34da6a3ce929d0e0e4799"
        assert d["relationship_type"] == "BATCH_ITEM"

    def test_trace_metric_aggregation(self):
        now = datetime.now(timezone.utc)
        agg = TraceMetricAggregation(
            service_name="dnk_event_stream_bus",
            operation="StreamPublishEvent",
            time_bucket=now,
            call_count=100,
            error_count=2,
            p50_ms=4.5,
            p95_ms=12.8,
            p99_ms=28.4,
            min_ms=1.1,
            max_ms=45.2,
            avg_ms=5.6,
        )
        assert agg.id.startswith("tma_")
        assert agg.error_rate == 0.02
        assert agg.p95_ms == 12.8

        d = agg.to_dict()
        assert d["service_name"] == "dnk_event_stream_bus"
        assert d["operation"] == "StreamPublishEvent"
        assert d["error_rate"] == 0.02
        assert d["call_count"] == 100
