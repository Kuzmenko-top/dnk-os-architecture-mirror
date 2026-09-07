# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-DNK-SWARM-CANVAS-WS-001"
# purpose: "Integration Verification for CanvasRuntimeBridge and Swarm WebSocket Gateway Streaming"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import asyncio
from typing import Any, cast
from unittest.mock import MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocket

from apps.api.routers import swarm_ws
from core.canvas_runtime_bridge import CanvasRuntimeBridge
from core.runtime_events import RuntimeEventBus


class MockWebSocket:
    """Mock WebSocket for unit testing SwarmConnectionManager broadcast without network sockets."""
    def __init__(self):
        self.sent_messages = []
        self.closed = False

    async def accept(self):
        pass

    async def send_json(self, data):
        self.sent_messages.append(data)

    async def close(self, code: int = 1000):
        self.closed = True


@pytest.fixture
def clean_event_bus():
    bus = RuntimeEventBus.get_instance()
    bus.reset()
    yield bus
    bus.reset()


@pytest.fixture
def bridge_no_redis(clean_event_bus):
    bridge = CanvasRuntimeBridge(event_bus=clean_event_bus, redis_client=None)
    swarm_ws.set_canvas_bridge(bridge)
    yield bridge
    swarm_ws.swarm_ws_manager.stop_event_listener()


@pytest.fixture
def app_with_swarm_ws(bridge_no_redis):
    app = FastAPI(title="Swarm WebSocket Test App")
    app.include_router(swarm_ws.router, prefix="/swarm")
    # Mock swarm_coordinator to avoid external LLM dispatch in automated unit runs
    original_coordinator = swarm_ws.swarm_coordinator
    swarm_ws.swarm_coordinator = None
    yield app
    swarm_ws.swarm_coordinator = original_coordinator


def test_bridge_offline_redis_fallback_to_eventbus(clean_event_bus):
    """
    Invariants Verified:
    1. If Redis client is None or broken, bridge gracefully falls back to local RuntimeEventBus.
    2. No exceptions raised, all lifecycle and snapshot events recorded in memory.
    """
    mock_redis = MagicMock()
    mock_redis.publish.side_effect = ConnectionError("Redis cluster unreachable")

    bridge = CanvasRuntimeBridge(
        event_bus=clean_event_bus,
        redis_client=mock_redis,
        redis_channel="dnk:runtime:events",
    )
    # Simulate connection established then failed on publish
    bridge.redis_connected = True

    # 1. Publish node created
    e1 = bridge.publish_node_created(
        node_id="node_test_01",
        name="Mock Node",
        canvas_id="canvas_01",
        execution_id="exec_001",
        node_type="agent",
        payload={"step": "init"},
    )
    assert e1 is not None
    assert e1.node_id == "node_test_01"
    assert e1.event_type == "node.created"

    # 2. Publish node executed (running -> completed)
    e2 = bridge.publish_node_executed(
        node_id="node_test_01",
        status="running",
        event_type="node.started",
        canvas_id="canvas_01",
        execution_id="exec_001",
    )
    assert e2.event_type == "node.started"

    e3 = bridge.publish_node_executed(
        node_id="node_test_01",
        status="completed",
        event_type="node.completed",
        canvas_id="canvas_01",
        execution_id="exec_001",
        execution_result="Task execution successful",
        payload={"output_data": {"result": "ok"}},
    )
    assert e3.event_type == "node.completed"
    assert e3.payload.get("output_data") == {"result": "ok"}

    # 3. Publish graph snapshot & selection batch
    e4 = bridge.publish_graph_snapshot(
        canvas_id="canvas_01",
        nodes=[{"id": "node_test_01"}],
        edges=[],
        execution_id="exec_001",
    )
    assert e4.event_type == "canvas.graph_snapshot"

    e5 = bridge.publish_selection_batch(
        canvas_id="canvas_01",
        node_ids=["node_test_01"],
        action="select",
        execution_id="exec_001",
    )
    assert e5.event_type == "canvas.selection_batch"

    # Verify fallback to published_events
    assert len(bridge.published_events) == 5


def test_bridge_monotonic_sequence_numbering(clean_event_bus):
    """
    Invariants Verified:
    Sequence numbers must strictly and monotonically increment per execution_id (1, 2, 3...).
    Different execution_ids must maintain isolated sequence numbering starting at 1.
    """
    bridge = CanvasRuntimeBridge(event_bus=clean_event_bus, redis_client=None)

    # Sequence for exec_A
    s1 = bridge.publish_node_created(
        node_id="node_A1",
        name="Node A1",
        execution_id="exec_A",
    )
    s2 = bridge.publish_node_executed(
        node_id="node_A1",
        status="running",
        event_type="node.started",
        execution_id="exec_A",
    )
    s3 = bridge.publish_node_executed(
        node_id="node_A1",
        status="completed",
        event_type="node.completed",
        execution_id="exec_A",
    )

    assert s1.sequence_number == 1
    assert s2.sequence_number == 2
    assert s3.sequence_number == 3

    # Sequence for exec_B
    b1 = bridge.publish_node_created(
        node_id="node_B1",
        name="Node B1",
        execution_id="exec_B",
    )
    b2 = bridge.publish_node_executed(
        node_id="node_B1",
        status="error",
        event_type="node.error",
        execution_id="exec_B",
        payload={"error_message": "Fatal error"},
    )

    assert b1.sequence_number == 1
    assert b2.sequence_number == 2


@pytest.mark.asyncio
async def test_websocket_realtime_runtime_event_broadcast(clean_event_bus):
    """
    Invariants Verified:
    Connected WebSocket clients receive real-time RUNTIME_EVENT envelopes for all bridge events.
    """
    bridge = CanvasRuntimeBridge(event_bus=clean_event_bus, redis_client=None)
    swarm_ws.set_canvas_bridge(bridge)

    mock_ws = MockWebSocket()
    await swarm_ws.swarm_ws_manager.connect(cast(WebSocket, mock_ws))
    # Brief yield so background event listener subscribes to the event bus
    await asyncio.sleep(0.02)

    try:
        # Publish node.created
        bridge.publish_node_created(
            node_id="node_ws_01",
            name="WebSocket Node",
            canvas_id="canvas_ws_demo",
            execution_id="exec_ws_01",
            node_type="agent",
            payload={"initial": True},
        )

        # Publish node.started
        bridge.publish_node_executed(
            node_id="node_ws_01",
            status="started",
            event_type="node.started",
            canvas_id="canvas_ws_demo",
            execution_id="exec_ws_01",
        )

        # Publish node.completed
        bridge.publish_node_executed(
            node_id="node_ws_01",
            status="completed",
            event_type="node.completed",
            canvas_id="canvas_ws_demo",
            execution_id="exec_ws_01",
            execution_result="Completed successfully",
            payload={"output_data": {"metrics": {"accuracy": 0.99}}},
        )

        # Allow broadcast loop to flush
        await asyncio.sleep(0.05)

        assert len(mock_ws.sent_messages) == 3

        types = [m.get("event_type") for m in mock_ws.sent_messages]
        assert types == ["node.created", "node.started", "node.completed"]

        for idx, m in enumerate(mock_ws.sent_messages, start=1):
            assert m.get("type") == "RUNTIME_EVENT"
            assert m.get("node_id") == "node_ws_01"
            assert m.get("execution_id") == "exec_ws_01"
            assert m.get("sequence_number") == idx
            assert "event" in m
    finally:
        swarm_ws.swarm_ws_manager.stop_event_listener()
        swarm_ws.swarm_ws_manager.disconnect(cast(WebSocket, mock_ws))


def test_websocket_task_execution_lifecycle_with_bridge(app_with_swarm_ws, bridge_no_redis):
    """
    Invariants Verified:
    TASK_EXECUTE message sent via WebSocket transitions through lifecycle:
    1. TASK_STATUS thinking / running / completed sent to socket.
    2. CanvasRuntimeBridge captures node.created, node.started, and node.completed events.
    """
    client = TestClient(app_with_swarm_ws)

    with client.websocket_connect("/swarm/ws") as ws:
        # Send execution command
        ws.send_json({
            "action": "TASK_EXECUTE",
            "nodeId": "node_e2e_01",
            "taskType": "mock_worker",
            "prompt": "Synthesize high-speed Liquid component",
            "canvasId": "canvas_e2e",
        })

        statuses = []
        for _ in range(10):
            msg = ws.receive_json()
            if msg.get("type") == "TASK_STATUS":
                statuses.append(msg.get("status"))
                if msg.get("status") == "completed":
                    break

        assert "thinking" in statuses
        assert "running" in statuses
        assert "completed" in statuses

    # Verify bridge recorded all 3 lifecycle stages
    recorded = bridge_no_redis.published_events
    assert len(recorded) >= 3

    event_types = [e.event_type for e in recorded]
    assert "node.created" in event_types
    assert "node.started" in event_types
    assert "node.completed" in event_types

    # Sequence numbers must be monotonic
    exec_id = recorded[0].execution_id
    seqs = [e.sequence_number for e in recorded if e.execution_id == exec_id]
    assert seqs == list(range(1, len(seqs) + 1))


def test_websocket_task_execution_error_lifecycle(app_with_swarm_ws, bridge_no_redis, monkeypatch):
    """
    Invariants Verified:
    When an unexpected error occurs during task execution, the bridge publishes
    a node.error event and the WebSocket receives a failed TASK_STATUS.
    """
    client = TestClient(app_with_swarm_ws)

    # Monkeypatch asyncio.sleep in swarm_ws to simulate failure during execution
    real_sleep = asyncio.sleep

    async def fail_sleep(secs):
        if secs == 0.3:  # Execution phase sleep
            raise RuntimeError("Synthetic worker failure for error verification")
        await real_sleep(secs)

    monkeypatch.setattr(swarm_ws.asyncio, "sleep", fail_sleep)

    with client.websocket_connect("/swarm/ws") as ws:
        ws.send_json({
            "action": "TASK_EXECUTE",
            "nodeId": "node_error_01",
            "taskType": "mock_worker",
            "prompt": "Trigger intentional error",
        })

        statuses = []
        for _ in range(10):
            msg = ws.receive_json()
            if msg.get("type") == "TASK_STATUS":
                statuses.append(msg.get("status"))
                if msg.get("status") in ("failed", "error"):
                    break

        assert "error" in statuses

    # Verify bridge recorded node.error event
    recorded = bridge_no_redis.published_events
    error_events = [e for e in recorded if e.event_type == "node.error"]
    assert len(error_events) >= 1
    assert error_events[0].payload.get("status") == "error"
    assert "Synthetic worker failure" in (error_events[0].payload.get("error") or error_events[0].payload.get("error_message", ""))
