# --- DNK-MRH-HEADER ---
# mrh_id: "tests/observe/test_trace_instrumentation_service.py"
# purpose: "Unit & Integration Tests for Distributed Context Injection and Auto-Instrumentation (DNK-OBSERVE-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import asyncio
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from apps.api.db.models.trace_context import TraceContext
from apps.api.services.telemetry_collector_service import TelemetryCollectorService
from apps.api.services.trace_instrumentation_service import (
    TraceContextMiddleware,
    extract_from_a2a_envelope,
    extract_from_stream_message,
    extract_w3c_trace_context,
    get_current_span,
    get_current_trace_context,
    inject_into_a2a_envelope,
    inject_into_stream_message,
    inject_w3c_trace_context,
    trace_span,
)


class TestTraceInstrumentationService:
    """Test suite for Phase 3 Distributed Context Injection & Auto-Instrumentation."""

    def test_w3c_trace_context_injection_and_extraction(self):
        ctx = TraceContext(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
            trace_flags="01",
            tracestate="congo=t61rcWkgMzE,rojo=00f067aa0ba902b7",
            baggage={"user.id": "user_42", "tenant": "ws-alpha-001"},
        )

        carrier = {}
        inject_w3c_trace_context(carrier, ctx)
        assert carrier["traceparent"] == "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        assert carrier["tracestate"] == "congo=t61rcWkgMzE,rojo=00f067aa0ba902b7"
        assert "user.id=user_42" in carrier["baggage"]

        extracted = extract_w3c_trace_context(carrier)
        assert extracted is not None
        assert extracted.trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert extracted.span_id == "00f067aa0ba902b7"
        assert extracted.sampled is True
        assert extracted.baggage["user.id"] == "user_42"
        assert extracted.baggage["tenant"] == "ws-alpha-001"

    def test_w3c_trace_context_extraction_invalid(self):
        assert extract_w3c_trace_context({}) is None
        assert extract_w3c_trace_context({"traceparent": "invalid-format"}) is None
        assert extract_w3c_trace_context({"traceparent": "00-1234-5678-01"}) is None

    def test_event_stream_bus_message_propagation(self):
        ctx = TraceContext(
            trace_id="a1b2c3d4e5f60718293a4b5c6d7e8f90",
            span_id="1122334455667788",
            baggage={"partition": "2"},
        )
        event = {"topic": "order.created", "payload": {"order_id": "ord_100"}}

        inject_into_stream_message(event, ctx)
        assert "traceparent" in event
        assert event["metadata"]["trace_id"] == ctx.trace_id
        assert event["metadata"]["baggage"]["partition"] == "2"

        extracted = extract_from_stream_message(event)
        assert extracted is not None
        assert extracted.trace_id == ctx.trace_id
        assert extracted.span_id == ctx.span_id

    def test_a2a_agent_envelope_propagation(self):
        ctx = TraceContext(
            trace_id="fedcba9876543210fedcba9876543210",
            span_id="aabbccddeeff0011",
            baggage={"sender": "agent_builder", "target": "agent_auditor"},
        )
        envelope = {
            "protocol": "DNK-A2A-004",
            "message_id": "msg_001",
            "body": {"task": "run_audit"},
        }

        inject_into_a2a_envelope(envelope, ctx)
        assert "traceparent" in envelope
        assert envelope["metadata"]["trace_id"] == ctx.trace_id
        assert envelope["metadata"]["baggage"]["sender"] == "agent_builder"

        extracted = extract_from_a2a_envelope(envelope)
        assert extracted is not None
        assert extracted.trace_id == ctx.trace_id
        assert extracted.span_id == ctx.span_id

    def test_sync_nested_spans_hierarchy(self):
        collector = TelemetryCollectorService()

        with trace_span("parent_operation", service_name="order_service", collector=collector) as parent:
            assert get_current_span() == parent
            parent_trace_id = parent.trace_id
            parent_span_id = parent.span_id

            with trace_span("child_operation_1", service_name="payment_service", collector=collector) as child1:
                assert child1.trace_id == parent_trace_id
                assert child1.parent_span_id == parent_span_id

            with trace_span("child_operation_2", service_name="inventory_service", collector=collector) as child2:
                assert child2.trace_id == parent_trace_id
                assert child2.parent_span_id == parent_span_id

        collector.flush()
        trace = collector.get_trace(parent_trace_id)
        assert len(trace) == 3

        span_map = {s["name"]: s for s in trace}
        assert span_map["parent_operation"]["parent_span_id"] is None
        assert span_map["child_operation_1"]["parent_span_id"] == parent_span_id
        assert span_map["child_operation_2"]["parent_span_id"] == parent_span_id
        assert all(s["status_code"] == "OK" for s in trace)

    def test_exception_handling_in_span(self):
        collector = TelemetryCollectorService()

        with pytest.raises(ValueError, match="Invalid order amount"):
            with trace_span("failing_operation", service_name="billing", collector=collector) as span:
                raise ValueError("Invalid order amount")

        collector.flush()
        traces = collector.list_traces(service_name="billing")
        assert len(traces) == 1
        trace = collector.get_trace(traces[0]["trace_id"])
        assert len(trace) == 1
        s = trace[0]
        assert s["status_code"] == "ERROR"
        assert s["status_message"] == "Invalid order amount"
        assert len(s["events"]) == 1
        assert s["events"][0]["name"] == "exception"
        assert s["events"][0]["attributes"]["exception.type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_async_context_manager_and_decorator(self):
        collector = TelemetryCollectorService()

        @trace_span("async_decorated_func", service_name="ai_worker", collector=collector)
        async def mock_async_task(x: int) -> int:
            await asyncio.sleep(0.01)
            return x * 2

        result = await mock_async_task(21)
        assert result == 42

        collector.flush()
        traces = collector.list_traces(service_name="ai_worker")
        assert len(traces) == 1
        trace = collector.get_trace(traces[0]["trace_id"])
        assert len(trace) == 1
        assert trace[0]["name"] == "async_decorated_func"
        assert trace[0]["duration_ms"] >= 8.0

    def test_sync_function_decorator(self):
        collector = TelemetryCollectorService()

        @trace_span("sync_decorated_func", service_name="crypto_util", collector=collector)
        def compute_hash(data: str) -> str:
            return f"hash_{data}"

        res = compute_hash("secret")
        assert res == "hash_secret"

        collector.flush()
        traces = collector.list_traces(service_name="crypto_util")
        assert len(traces) == 1
        assert traces[0]["root_operation"] == "sync_decorated_func"

    def test_fastapi_trace_context_middleware(self):
        collector = TelemetryCollectorService()
        app = FastAPI()
        app.add_middleware(TraceContextMiddleware, service_name="test_api_gateway", collector=collector)

        @app.get("/api/v1/orders/{order_id}")
        async def get_order(order_id: str):
            ctx = get_current_trace_context()
            return {
                "order_id": order_id,
                "trace_id": ctx.trace_id if ctx else None,
            }

        client = TestClient(app)

        # 1. Request without existing traceparent -> generates new trace
        res1 = client.get("/api/v1/orders/101")
        assert res1.status_code == 200
        assert "traceparent" in res1.headers
        assert "x-trace-id" in res1.headers
        data1 = res1.json()
        assert data1["trace_id"] == res1.headers["x-trace-id"]

        # 2. Request with incoming W3C traceparent -> preserves trace_id
        parent_trace_id = "55555555555555555555555555555555"
        parent_span_id = "9999999999999999"
        incoming_traceparent = f"00-{parent_trace_id}-{parent_span_id}-01"

        res2 = client.get(
            "/api/v1/orders/102",
            headers={"traceparent": incoming_traceparent, "baggage": "client=web"},
        )
        assert res2.status_code == 200
        assert res2.headers["x-trace-id"] == parent_trace_id

        collector.flush()
        trace2 = collector.get_trace(parent_trace_id)
        assert len(trace2) == 1
        s = trace2[0]
        assert s["service_name"] == "test_api_gateway"
        assert s["parent_span_id"] == parent_span_id
        assert s["attributes"]["http.status_code"] == 200
