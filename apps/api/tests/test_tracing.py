# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_tests_test_tracing"
# purpose: "Comprehensive unit and integration tests for Structured Logger and Distributed Tracing"
# standard: "DNK-STD-0080"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# alters_files: []
# triggers_tasks: []
# canonical_source: true
# --- END DNK-MRH-HEADER ---

import io
import json
import uuid
import asyncio
import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from apps.api.logging.structured_logger import (
    StructuredLogger,
    JSONFormatter,
    TraceMiddleware,
    trace_span,
    get_trace_id,
    set_trace_id,
    get_span_id,
    set_span_id,
    get_parent_span_id,
    bind_context,
    clear_context,
    get_context,
)
from apps.api.routers.canvas_v3_ws import CanvasV3WebSocketManager


def test_json_formatter_valid_structure():
    """Verify JSONFormatter produces strict schema-compliant JSON for ELK/Loki."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    formatter = JSONFormatter(service_name="dnk-api")
    handler.setFormatter(formatter)

    test_logger = logging.getLogger("test_elk_logger")
    test_logger.handlers = [handler]
    test_logger.setLevel(logging.INFO)
    test_logger.propagate = False

    test_trace_id = str(uuid.uuid4())
    set_trace_id(test_trace_id)
    bind_context(environment="test", user_id="u-42")

    test_logger.info("ELK Loki ingest probe")
    handler.flush()

    line = stream.getvalue().strip()
    data = json.loads(line)

    assert "timestamp" in data
    assert "level" in data
    assert data["level"] == "INFO"
    assert "service" in data
    assert data["service"] == "dnk-api"
    assert "trace_id" in data
    assert data["trace_id"] == test_trace_id
    assert "span_id" in data
    assert "message" in data
    assert data["message"] == "ELK Loki ingest probe"
    assert "context" in data
    assert data["context"]["environment"] == "test"
    assert data["context"]["user_id"] == "u-42"
    clear_context()


def test_structured_logger_levels_and_payload():
    """Verify structured logger helper methods write valid JSON logs."""
    stream = io.StringIO()
    logger_inst = StructuredLogger(service_name="dnk-api-test", stream=stream)

    test_trace = str(uuid.uuid4())
    set_trace_id(test_trace)

    try:
        logger_inst.info("User registered successfully", user_id="u-123", role="admin")
        logger_inst.warning("Rate limit threshold approached", threshold=0.85)
        logger_inst.error("Failed to connect to backend", error_code="CONN_ERR", retry=False)

        lines = [line for line in stream.getvalue().split("\n") if line.strip()]
        assert len(lines) == 3

        parsed_logs = [json.loads(l) for l in lines]

        # Check required fields across all emitted logs
        for entry in parsed_logs:
            assert "timestamp" in entry
            assert "level" in entry
            assert "trace_id" in entry
            assert entry["trace_id"] == test_trace
            assert "span_id" in entry
            assert "message" in entry
            assert "context" in entry

        assert parsed_logs[0]["level"] == "INFO"
        assert parsed_logs[0]["context"]["user_id"] == "u-123"

        assert parsed_logs[1]["level"] == "WARNING"
        assert parsed_logs[1]["context"]["threshold"] == 0.85

        assert parsed_logs[2]["level"] == "ERROR"
        assert parsed_logs[2]["context"]["error_code"] == "CONN_ERR"
    finally:
        clear_context()


def test_trace_span_parent_child():
    """Verify trace_span creates nested child spans linked to parent span."""
    clear_context()
    root_trace = str(uuid.uuid4())
    set_trace_id(root_trace)
    root_span = set_span_id()

    with trace_span("child_operation_1", module="auth") as child_1:
        assert get_trace_id() == root_trace
        assert get_span_id() == child_1
        assert get_parent_span_id() == root_span
        assert get_context().get("module") == "auth"

        with trace_span("grandchild_operation", sub_task="hashing") as grandchild:
            assert get_trace_id() == root_trace
            assert get_span_id() == grandchild
            assert get_parent_span_id() == child_1
            assert get_context().get("sub_task") == "hashing"

        # Exited grandchild
        assert get_span_id() == child_1
        assert get_parent_span_id() == root_span

    # Exited child
    assert get_span_id() == root_span
    assert get_parent_span_id() is None
    clear_context()


@pytest.mark.asyncio
async def test_trace_span_async_support():
    """Verify trace_span supports async context manager."""
    clear_context()
    root_trace = str(uuid.uuid4())
    set_trace_id(root_trace)
    root_span = set_span_id()

    async with trace_span("async_step", step=1) as child_span:
        assert get_trace_id() == root_trace
        assert get_span_id() == child_span
        assert get_parent_span_id() == root_span
        assert get_context().get("step") == 1

    assert get_span_id() == root_span
    assert get_parent_span_id() is None
    clear_context()


@pytest.mark.asyncio
async def test_contextvars_async_isolation():
    """Ensure trace contexts do not bleed across concurrent asyncio tasks."""
    clear_context()
    results = {}

    async def worker(worker_id: str, trace_val: str):
        set_trace_id(trace_val)
        bind_context(worker=worker_id)
        await asyncio.sleep(0.01)
        results[worker_id] = {
            "trace_id": get_trace_id(),
            "context": get_context(),
        }

    task_a = asyncio.create_task(worker("worker_a", "trace-AAA-111"))
    task_b = asyncio.create_task(worker("worker_b", "trace-BBB-222"))
    await asyncio.gather(task_a, task_b)

    assert results["worker_a"]["trace_id"] == "trace-AAA-111"
    assert results["worker_a"]["context"]["worker"] == "worker_a"
    assert results["worker_b"]["trace_id"] == "trace-BBB-222"
    assert results["worker_b"]["context"]["worker"] == "worker_b"
    clear_context()


def test_http_middleware_trace_propagation():
    """Verify HTTP requests propagate X-Trace-ID or generate new trace headers."""
    app = FastAPI()
    app.add_middleware(TraceMiddleware)

    @app.get("/test/trace")
    async def sample_endpoint():
        return {"current_trace_id": get_trace_id()}

    client = TestClient(app)
    custom_trace = "trace-custom-999-http"
    response = client.get("/test/trace", headers={"X-Trace-ID": custom_trace})

    assert response.status_code == 200
    assert response.headers.get("X-Trace-ID") == custom_trace
    assert response.json()["current_trace_id"] == custom_trace


def test_http_middleware_generates_new_uuid_when_omitted():
    """Verify HTTP requests generate valid UUIDv4 when X-Trace-ID is not provided."""
    app = FastAPI()
    app.add_middleware(TraceMiddleware)

    @app.get("/test/auto-trace")
    async def sample_endpoint():
        return {"current_trace_id": get_trace_id()}

    client = TestClient(app)
    response = client.get("/test/auto-trace")

    assert response.status_code == 200
    trace_header = response.headers.get("X-Trace-ID")
    assert trace_header is not None
    # Validate UUID structure
    val = uuid.UUID(trace_header)
    assert str(val) == trace_header


@pytest.mark.asyncio
async def test_websocket_broadcast_trace_injection():
    """Verify WebSocket messages automatically receive trace_id."""
    manager = CanvasV3WebSocketManager()
    canvas_id = "canvas-test-tracing-101"

    received_messages = []

    class MockWebSocket:
        async def send_text(self, text: str):
            received_messages.append(json.loads(text))

    mock_ws = MockWebSocket()
    client_trace = "ws-trace-init-42"
    manager.active_connections[canvas_id] = [
        {"ws": mock_ws, "user_id": "test_user", "trace_id": client_trace}
    ]

    set_trace_id(client_trace)
    await manager.broadcast(canvas_id, {"type": "CANVAS_MUTATION", "node_id": "n-1"})

    assert len(received_messages) == 1
    broadcast_msg = received_messages[0]
    assert "trace_id" in broadcast_msg
    assert broadcast_msg["trace_id"] == client_trace
    assert broadcast_msg["type"] == "CANVAS_MUTATION"
    clear_context()


def test_clear_context_resets_all_vars():
    """Verify clear_context resets all context variables."""
    set_trace_id("temp-trace")
    set_span_id("temp-span")
    bind_context(temp_key="temp_val")

    assert get_trace_id() == "temp-trace"
    assert get_span_id() == "temp-span"
    assert get_context().get("temp_key") == "temp_val"

    clear_context()

    # After clearing, get_context should be empty
    assert get_context() == {}
    # get_parent_span_id should be None
    assert get_parent_span_id() is None


def test_json_log_validation_verification_command():
    """Verify the exact JSON validation command from slice directive."""
    stream = io.StringIO()
    logger_inst = StructuredLogger(service_name="dnk-api", stream=stream)
    logger_inst.info("Direct verification test message", status="ok")

    log_line = stream.getvalue().strip()
    data = json.loads(log_line)

    assert "timestamp" in data
    assert "level" in data
    assert "trace_id" in data
    assert "span_id" in data
    assert "message" in data
    assert data["message"] == "Direct verification test message"
