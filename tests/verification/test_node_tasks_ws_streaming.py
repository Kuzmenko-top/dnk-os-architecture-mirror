# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-DNK-NODE-TASKS-WS-STREAMING-001"
# purpose: "FastAPI TestClient WebSocket verification for reactive node tasks execution and event streaming (ADR-0042)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import asyncio
from typing import Any, cast
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocket

from apps.api.routers import node_tasks_router, swarm_ws
from core.canvas_runtime_bridge import CanvasRuntimeBridge
from services.dnk_node_tasks.models import (
    DependencyEdge,
    EdgeRelation,
    ExecutionStage,
    NodeItem,
    NodeStatus,
    NodeTaskGraph,
    NodeType,
)
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager


class MockWebSocket:
    """Mock WebSocket for unit testing reactive SwarmConnectionManager streaming."""

    def __init__(self):
        self.sent_messages = []
        self.closed = False

    async def accept(self):
        pass

    async def send_json(self, data: Any):
        self.sent_messages.append(data)

    async def close(self, code: int = 1000):
        self.closed = True


@pytest.fixture
def clean_graph(tmp_path):
    """Sets up a clean mock graph with test nodes in an isolated temp database."""
    orig_instance = NodeTaskPersistenceManager._instance
    test_db = str(tmp_path / "node_task_graph.json")
    test_obsidian = str(tmp_path / "obsidian")
    test_projects = str(tmp_path / "projects.json")

    manager = NodeTaskPersistenceManager(
        data_file_path=test_db,
        obsidian_dir=test_obsidian,
        projects_file_path=test_projects,
    )
    manager.reset_to_baseline()
    NodeTaskPersistenceManager._instance = manager

    test_node_1 = NodeItem(
        id="ws_test_node_alpha",
        title="WebSocket Alpha Worker",
        description="Testing reactive WebSocket event streaming",
        node_type=NodeType.TASK,
        priority="high",
        stage=ExecutionStage.READY,
        status=NodeStatus.READY,
        progress=0.0,
        assigned_agent="gerych_builder",
    )
    test_node_2 = NodeItem(
        id="ws_test_node_beta",
        title="WebSocket Beta Worker",
        description="Testing dependency completion",
        node_type=NodeType.TASK,
        priority="medium",
        stage=ExecutionStage.READY,
        status=NodeStatus.READY,
        progress=0.0,
        assigned_agent="gerych_auditor",
    )

    test_edge = DependencyEdge(
        id="edge_alpha_beta",
        source="ws_test_node_alpha",
        target="ws_test_node_beta",
        relation=EdgeRelation.DEPENDS_ON,
    )

    graph = NodeTaskGraph(
        nodes={
            test_node_1.id: test_node_1,
            test_node_2.id: test_node_2,
        },
        edges=[test_edge],
    )
    manager.save_graph(graph)

    yield manager

    NodeTaskPersistenceManager._instance = orig_instance



@pytest.mark.asyncio
async def test_execute_agent_publishes_to_canvas_bridge(clean_graph):
    """Verifies execute_agent_for_node publishes start and completion events via CanvasRuntimeBridge."""
    bridge = CanvasRuntimeBridge()
    swarm_ws.set_canvas_bridge(bridge)

    req = node_tasks_router.ExecuteAgentRequest(
        node_id="ws_test_node_alpha",
        agent_override="gerych_builder",
        auto_complete=True,
    )

    res = await node_tasks_router.execute_agent_for_node(node_id="ws_test_node_alpha", req=req)

    assert res["status"] == "success"
    assert res["stage"] == "completed"
    assert res["progress"] == 100.0

    # Verify bridge recorded published events
    events = bridge.published_events
    assert len(events) >= 2

    # Initial start event: status_changed to in_progress
    start_events = [e for e in events if e.event_type == "node.status_changed" and e.node_id == "ws_test_node_alpha"]
    assert len(start_events) >= 1
    assert start_events[0].payload.get("status") == "in_progress"

    # Completion event: node.executed with status completed
    exec_events = [e for e in events if e.event_type == "node.executed" and e.node_id == "ws_test_node_alpha"]
    assert len(exec_events) >= 1
    assert exec_events[0].payload.get("status") == "completed"
    assert exec_events[0].payload.get("progress") == 100.0


@pytest.mark.asyncio
async def test_ws_connection_receives_reactive_node_lifecycle_events(clean_graph):
    """Verifies that SwarmConnectionManager delivers RUNTIME_EVENTs to active WebSockets."""
    bridge = CanvasRuntimeBridge()
    swarm_ws.set_canvas_bridge(bridge)

    # Use the active singleton manager
    manager = swarm_ws.swarm_ws_manager
    mock_ws = MockWebSocket()
    await manager.connect(cast(WebSocket, mock_ws))
    # Give event loop a tick to initialize the subscriber queue in the broadcast loop
    await asyncio.sleep(0.05)

    # Trigger execute_agent_for_node which publishes to bridge
    req = node_tasks_router.ExecuteAgentRequest(
        node_id="ws_test_node_alpha",
        agent_override="gerych_builder",
        auto_complete=True,
    )
    await node_tasks_router.execute_agent_for_node(node_id="ws_test_node_alpha", req=req)

    # Let the background event broadcast task deliver messages
    await asyncio.sleep(0.05)

    # Verify WebSocket received messages
    sent = mock_ws.sent_messages
    assert len(sent) > 0

    event_types = [m.get("event_type") for m in sent if m.get("type") == "RUNTIME_EVENT"]
    assert "node.status_changed" in event_types or "node.executed" in event_types

    manager.disconnect(cast(WebSocket, mock_ws))


def test_testclient_ws_endpoints_handshake(clean_graph):
    """Verifies FastAPI TestClient WebSocket handshake and basic interaction."""
    app = FastAPI()
    app.include_router(swarm_ws.router)
    app.include_router(node_tasks_router.router, prefix="/api/v3/node_tasks")

    client = TestClient(app)

    # Connect to /api/ws
    with client.websocket_connect("/api/ws") as ws:
        ws.send_json({"action": "PING"})
        msg = ws.receive_json()
        assert msg.get("status") == "PONG" or msg.get("type") == "PONG"

    # Connect to /ws/swarm
    with client.websocket_connect("/ws/swarm") as ws:
        ws.send_json({"action": "GET_STATE"})
        msg = ws.receive_json()
        assert "active_agents" in msg or "type" in msg


@pytest.mark.asyncio
async def test_autonomous_agent_flow_progresses_to_completion(clean_graph, monkeypatch):
    """Verifies that _run_autonomous_agent_flow steps through 35% -> 100% and marks completed."""
    import asyncio
    orig_sleep = asyncio.sleep
    async def fast_sleep(_):
        await orig_sleep(0.001)

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)

    bridge = CanvasRuntimeBridge()
    swarm_ws.set_canvas_bridge(bridge)

    node_id = "ws_test_node_alpha"
    await node_tasks_router._run_autonomous_agent_flow(node_id, "dnk_dev_fullstack", "Build test slice")

    # Load updated graph and verify node reached 100% and completed
    manager = NodeTaskPersistenceManager.get_instance()
    graph = manager.load_graph()
    node = graph.nodes[node_id]

    assert node.progress == 100.0
    assert node.stage == ExecutionStage.COMPLETED
    assert node.status == NodeStatus.COMPLETED

    # Verify logs were appended
    logs_res = node_tasks_router.get_node_execution_logs(node_id)
    assert len(logs_res["logs"]) >= 5
    messages = [log["message"] for log in logs_res["logs"]]
    assert any("TaskDNA decomposition" in m for m in messages)
    assert any("Master Quality Gate" in m for m in messages)


@pytest.mark.asyncio
async def test_edge_lifecycle_publishes_to_canvas_bridge(clean_graph):
    """Verifies create_edge and delete_edge publish edge.created and edge.deleted to CanvasRuntimeBridge."""
    bridge = CanvasRuntimeBridge()
    swarm_ws.set_canvas_bridge(bridge)

    req = node_tasks_router.CreateEdgeRequest(
        source="ws_test_node_alpha",
        target="ws_test_node_beta",
        relation="depends_on",
        description="Beta requires Alpha",
    )

    create_res = node_tasks_router.create_edge(req)
    assert create_res["status"] == "success"
    edge_id = create_res["edge"]["id"]

    # Verify edge.created event was published
    created_events = [e for e in bridge.published_events if e.event_type == "edge.created"]
    assert len(created_events) >= 1
    assert created_events[0].payload.get("edge_id") == edge_id
    assert created_events[0].payload.get("source") == "ws_test_node_alpha"

    # Delete edge and verify edge.deleted event was published
    delete_res = node_tasks_router.delete_edge(edge_id)
    assert delete_res["status"] == "success"

    deleted_events = [e for e in bridge.published_events if e.event_type == "edge.deleted"]
    assert len(deleted_events) >= 1
    assert deleted_events[0].payload.get("edge_id") == edge_id

