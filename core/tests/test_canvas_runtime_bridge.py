# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_canvas_runtime_bridge.py"
# purpose: "Unit, integration, and E2E tests for Infinite Canvas ↔ LangGraph Runtime Bridge (Flower 19)."
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import os
import json
import pytest
from datetime import datetime
from core.runtime_events import RuntimeEvent, GraphExecutionSnapshot
from core.adapters.dnk_langgraph_adapter import DNKLangGraphAdapter, InMemoryCheckpointer
from core.canvas_runtime_bridge import CanvasRuntimeBridge

TEST_MEM_STORAGE_PATH = "core/tests/scones_swarm_visual_test.json"

@pytest.fixture
def clean_storage():
    if os.path.exists(TEST_MEM_STORAGE_PATH):
        os.remove(TEST_MEM_STORAGE_PATH)
    yield TEST_MEM_STORAGE_PATH
    if os.path.exists(TEST_MEM_STORAGE_PATH):
        os.remove(TEST_MEM_STORAGE_PATH)


# --- 1. Unit & Integration Tests (Min 10 required) ---

def test_runtime_event_dto_validation():
    """Test 1: Verify RuntimeEvent Pydantic DTO schema validation."""
    ev = RuntimeEvent(
        tenant_id="tenant_1",
        workspace_id="workspace_1",
        canvas_id="canvas_A",
        graph_id="graph_1",
        thread_id="thread_1",
        execution_id="exec_1",
        node_id="node_a",
        event_type="node.started",
        sequence_number=5,
        payload={"step": 2}
    )
    assert ev.sequence_number == 5
    assert ev.node_id == "node_a"
    assert isinstance(ev.timestamp, datetime)

def test_graph_snapshot_dto_validation():
    """Test 2: Verify GraphExecutionSnapshot Pydantic DTO schema validation."""
    snap = GraphExecutionSnapshot(
        tenant_id="tenant_1",
        workspace_id="workspace_1",
        canvas_id="canvas_A",
        graph_id="graph_1",
        thread_id="thread_1",
        execution_id="exec_1",
        current_node="node_y",
        status="paused",
        last_sequence_number=12,
        node_states={"node_x": "completed", "node_y": "waiting"},
        messages=[]
    )
    assert snap.status == "paused"
    assert snap.node_states["node_x"] == "completed"

def test_event_publishing_lifecycle():
    """Test 3: Verify that normal execution emits start, running, and completion events in order."""
    adapter = DNKLangGraphAdapter(checkpointer=InMemoryCheckpointer())
    adapter.add_node("node_a", lambda s: {"messages": ["A ran"]})
    adapter.compile_graph()
    
    initial_state = {
        "tenant_id": "tenant_1",
        "workspace_id": "workspace_1",
        "canvas_id": "canvas_1",
        "current_node": "node_a"
    }
    
    res = adapter.execute(initial_state, thread_id="thread_lifecycle")
    assert res["status"] == "completed"
    
    events = adapter.get_emitted_events("thread_lifecycle", "tenant_1", "workspace_1")
    assert len(events) >= 5 # created, started, node.started, checkpoint.created, graph.completed
    assert events[0].event_type == "graph.created"
    assert events[1].event_type == "graph.started"
    assert events[-1].event_type == "graph.completed"

def test_sequence_number_ordering():
    """Test 4: Verify strictly incremental sequence numbers on emitted event stream."""
    adapter = DNKLangGraphAdapter(checkpointer=InMemoryCheckpointer())
    adapter.add_node("node_a", lambda s: s)
    adapter.add_node("node_b", lambda s: s)
    adapter.add_edge("node_a", "node_b")
    adapter.add_edge("node_b", "__end__")
    adapter.compile_graph()
    
    adapter.execute({"current_node": "node_a"}, thread_id="thread_order")
    
    events = adapter.get_emitted_events("thread_order", "default", "default")
    seq_numbers = [ev.sequence_number for ev in events]
    
    # Assert sequence numbers are [1, 2, 3, 4, ...] and strict increasing
    assert seq_numbers == list(range(1, len(events) + 1))

def test_reconnect_snapshot_resync():
    """Test 5: Verify that get_graph_snapshot constructs a stable resync snapshot."""
    adapter = DNKLangGraphAdapter(checkpointer=InMemoryCheckpointer())
    adapter.add_node("node_a", lambda s: s)
    adapter.compile_graph()
    
    adapter.execute({"current_node": "node_a", "canvas_id": "canvas_xyz"}, thread_id="thread_resync")
    
    snapshot = adapter.get_graph_snapshot("thread_resync", "default", "default")
    assert snapshot is not None
    assert snapshot.canvas_id == "canvas_xyz"
    assert snapshot.current_node == "__end__"
    assert snapshot.node_states["node_a"] == "completed"
    assert snapshot.last_sequence_number > 0

def test_reconnect_duplicate_event_protection():
    """Test 6: Verify duplicate event protection. Starting same thread resets counter cleanly."""
    adapter = DNKLangGraphAdapter(checkpointer=InMemoryCheckpointer())
    adapter.add_node("node_a", lambda s: s)
    adapter.compile_graph()
    
    # Run 1
    adapter.execute({"current_node": "node_a"}, thread_id="thread_reconnect")
    len1 = len(adapter.get_emitted_events("thread_reconnect", "default", "default"))
    
    # Re-run / Reconnect start
    adapter.execute({"current_node": "node_a"}, thread_id="thread_reconnect")
    len2 = len(adapter.get_emitted_events("thread_reconnect", "default", "default"))
    
    # Length must be reset and equal, counter started from 1 again without duplicates
    assert len1 == len2
    assert adapter._sequence_counters["thread_reconnect"] == len2

def test_runtime_event_tenant_isolation_boundary():
    """Test 7: Verify that loading emitted events using wrong tenant raises PermissionError."""
    adapter = DNKLangGraphAdapter(checkpointer=InMemoryCheckpointer())
    adapter.add_node("node_a", lambda s: s)
    adapter.compile_graph()
    
    adapter.execute({"current_node": "node_a", "tenant_id": "tenant_A"}, thread_id="thread_iso")
    
    # Access as Tenant B -> PermissionError
    with pytest.raises(PermissionError) as exc:
        adapter.get_emitted_events("thread_iso", "tenant_B", "default")
    assert "Boundary Isolation Violation" in str(exc.value)

def test_runtime_snapshot_isolation_boundary():
    """Test 8: Verify that loading snapshot using wrong tenant raises PermissionError."""
    adapter = DNKLangGraphAdapter(checkpointer=InMemoryCheckpointer())
    adapter.add_node("node_a", lambda s: s)
    adapter.compile_graph()
    
    adapter.execute({"current_node": "node_a", "tenant_id": "tenant_A"}, thread_id="thread_iso")
    
    # Access snapshot as Tenant B -> PermissionError
    with pytest.raises(PermissionError) as exc:
        adapter.get_graph_snapshot("thread_iso", "tenant_B", "default")
    assert "Boundary Isolation Violation" in str(exc.value)

def test_event_node_states_mapping():
    """Test 9: Verify intermediate events correctly map state history inside the snapshot."""
    adapter = DNKLangGraphAdapter(checkpointer=InMemoryCheckpointer())
    
    # Interrupted flow
    adapter.add_node("node_a", lambda s: s)
    adapter.add_node("node_b", lambda s: s)
    adapter.add_edge("node_a", "node_b")
    adapter.add_edge("node_b", "__end__")
    adapter.compile_graph()
    
    adapter.execute({
        "current_node": "node_a",
        "interrupt_signal": "before_node_b"
    }, thread_id="thread_state_map")
    
    snapshot = adapter.get_graph_snapshot("thread_state_map", "default", "default")
    assert snapshot.node_states["node_a"] == "completed"
    assert snapshot.node_states["node_b"] == "waiting"

def test_failed_and_retried_event_publishing(clean_storage):
    """Test 10: Verify transient crash emits failed, retrying, and recovered events."""
    adapter = DNKLangGraphAdapter(checkpointer=InMemoryCheckpointer())
    
    # Override distiller SCONES storage explicitly to avoid test pollution
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    adapter.distiller.memory_manager.initialize_all(
        session_id="langgraph_e2e_session_bridge",
        hermes_home=base_dir,
        platform="cli",
        tenant_id="tenant_L",
        workspace_id="workspace_1"
    )
    adapter.distiller.memory_manager.get_provider("scones")._engine.storage_path = clean_storage
    adapter.distiller.memory_manager.get_provider("scones")._engine.memories = []
    adapter.distiller.memory_manager.get_provider("scones")._engine.save_memories()

    attempts = 0
    def crash_and_recover_handler(state):
        nonlocal attempts
        attempts += 1
        for msg in state.get("messages", []):
            if "[Self-Healing Workaround Injected]" in msg.get("content", ""):
                return {"status": "ok"}
        raise TimeoutError("Temporary rate limit hit 429")

    adapter.add_node("node_a", crash_and_recover_handler)
    adapter.add_edge("node_a", "__end__")
    adapter.compile_graph()
    
    adapter.execute({
        "current_node": "node_a",
        "tenant_id": "tenant_L",
        "workspace_id": "workspace_1"
    }, thread_id="thread_retry_events")
    
    events = adapter.get_emitted_events("thread_retry_events", "tenant_L", "workspace_1")
    event_types = [ev.event_type for ev in events]
    
    # Assert specific self-healing events are mapped and published on the bridge!
    assert "node.failed" in event_types
    assert "node.retrying" in event_types
    assert "node.recovered" in event_types


# --- 2. End-to-End (E2E) Test ---

def test_e2e_canvas_node_to_graph_completion_bridge():
    """
    Test 11 (E2E): Complete visual flow mapping.
    Canvas node trigger ➔ start execution ➔ events generated ➔ completed snapshot resynced.
    """
    checkpointer = InMemoryCheckpointer()
    adapter = DNKLangGraphAdapter(checkpointer=checkpointer)
    
    # Multi-agent node chain
    adapter.add_node("canvas_selection_parser", lambda s: {"parsed": True})
    adapter.add_node("agent_coder_task", lambda s: {"summary": "Built Next.js UI"})
    adapter.add_edge("canvas_selection_parser", "agent_coder_task")
    adapter.add_edge("agent_coder_task", "__end__")
    adapter.compile_graph()
    
    # Initialize from Canvas payload DTO
    initial_canvas_payload = {
        "tenant_id": "tenant_e2e_bridge",
        "workspace_id": "ws_production",
        "canvas_id": "stitch_canvas_main",
        "graph_id": "user_ui_pipeline",
        "execution_id": "run_e2e_01",
        "current_node": "canvas_selection_parser"
    }
    
    thread_id = "thread_e2e_canvas_01"
    
    # 1. Canvas UI Triggers Execution API
    adapter.execute(initial_canvas_payload, thread_id=thread_id)
    
    # 2. Canvas Reconnects / Requests Resync Snapshot
    snapshot = adapter.get_graph_snapshot(thread_id, "tenant_e2e_bridge", "ws_production")
    
    assert snapshot is not None
    assert snapshot.canvas_id == "stitch_canvas_main"
    assert snapshot.graph_id == "user_ui_pipeline"
    assert snapshot.status == "completed"
    
    # Confirm both custom nodes are successfully tracked as completed in the snapshot resync!
    assert snapshot.node_states["canvas_selection_parser"] == "completed"
    assert snapshot.node_states["agent_coder_task"] == "completed"


# --- CANVAS RUNTIME TRANSPORT & SECURITY TESTS (Flower 20) ---

from core.runtime_events import RuntimeEventBus

@pytest.mark.anyio
async def test_runtime_event_bus_basic_routing():
    """Test 12: Verify basic publish/subscribe routing under normal conditions."""
    bus = RuntimeEventBus.get_instance()
    bus.reset()
    
    # Subscribe to exec_1
    queue = bus.subscribe("exec_1", "tenant_1", "ws_1")
    
    # Publish event
    event = RuntimeEvent(
        tenant_id="tenant_1",
        workspace_id="ws_1",
        canvas_id="canvas_1",
        graph_id="graph_1",
        thread_id="thread_1",
        execution_id="exec_1",
        event_type="node.started",
        sequence_number=1
    )
    bus.publish(event)
    
    # Assert received
    received = await queue.get()
    assert received.execution_id == "exec_1"
    assert received.event_type == "node.started"
    assert received.sequence_number == 1

@pytest.mark.anyio
async def test_runtime_event_bus_fail_closed_validation():
    """Test 13: Verify that subscription raises PermissionError on missing credentials."""
    bus = RuntimeEventBus.get_instance()
    bus.reset()
    
    with pytest.raises(PermissionError) as exc:
        bus.subscribe("exec_1", "", "ws_1")
    assert "Fail-Closed" in str(exc.value)

@pytest.mark.anyio
async def test_runtime_event_bus_cross_workspace_protection():
    """Test 14: Verify that events are NOT delivered to wrong workspaces."""
    bus = RuntimeEventBus.get_instance()
    bus.reset()
    
    # Subscriber A (Tenant 1, WS A)
    queue_A = bus.subscribe("exec_1", "tenant_1", "ws_A")
    
    # Subscriber B (Tenant 1, WS B)
    queue_B = bus.subscribe("exec_1", "tenant_1", "ws_B")
    
    # Publish event with Tenant 1, WS A
    event = RuntimeEvent(
        tenant_id="tenant_1",
        workspace_id="ws_A",
        canvas_id="canvas_1",
        graph_id="graph_1",
        thread_id="thread_1",
        execution_id="exec_1",
        event_type="node.started",
        sequence_number=1
    )
    bus.publish(event)
    
    # Queue A should have the event, Queue B should be empty
    assert queue_A.qsize() == 1
    assert queue_B.qsize() == 0
    
    received = await queue_A.get()
    assert received.workspace_id == "ws_A"

@pytest.mark.anyio
async def test_runtime_event_bus_reconnect_replay():
    """Test 15: Verify that subscribing with last_event_id replays missed events."""
    bus = RuntimeEventBus.get_instance()
    bus.reset()
    
    # Pre-publish 3 events
    for i in range(1, 4):
        event = RuntimeEvent(
            tenant_id="tenant_1",
            workspace_id="ws_1",
            canvas_id="canvas_1",
            graph_id="graph_1",
            thread_id="thread_1",
            execution_id="exec_1",
            event_type="node.started",
            sequence_number=i
        )
        bus.publish(event)
        
    # Subscribe starting from last_event_id = 1
    queue = bus.subscribe("exec_1", "tenant_1", "ws_1", last_event_id=1)
    
    # Should receive event 2 and 3
    assert queue.qsize() == 2
    ev2 = await queue.get()
    ev3 = await queue.get()
    assert ev2.sequence_number == 2
    assert ev3.sequence_number == 3

@pytest.mark.anyio
async def test_runtime_event_bus_snapshot_fallback_on_gaps():
    """Test 16: Verify that reconnect with a sequence gap triggers a snapshot fallback event."""
    bus = RuntimeEventBus.get_instance()
    bus.reset()
    
    # Pre-publish events with a gap (say sequence 1, then sequence 3, sequence 4)
    event1 = RuntimeEvent(
        tenant_id="tenant_1",
        workspace_id="ws_1",
        canvas_id="canvas_1",
        graph_id="graph_1",
        thread_id="thread_1",
        execution_id="exec_1",
        event_type="node.started",
        sequence_number=1
    )
    event3 = RuntimeEvent(
        tenant_id="tenant_1",
        workspace_id="ws_1",
        canvas_id="canvas_1",
        graph_id="graph_1",
        thread_id="thread_1",
        execution_id="exec_1",
        event_type="node.started",
        sequence_number=3
    )
    bus.publish(event1)
    bus.publish(event3)
    
    # Subscribe with last_event_id = 1. Event 2 is missing (gap!)
    queue = bus.subscribe("exec_1", "tenant_1", "ws_1", last_event_id=1)
    
    # Should receive the snapshot_fallback sentinel
    assert queue.qsize() == 1
    fallback = await queue.get()
    assert isinstance(fallback, dict)
    assert fallback["event_type"] == "snapshot_fallback"

@pytest.mark.anyio
async def test_runtime_event_bus_bounded_queue_backpressure():
    """Test 17: Verify that bounded queue drops oldest event under overflow (backpressure)."""
    bus = RuntimeEventBus(max_queue_size=2)
    bus.reset()
    
    queue = bus.subscribe("exec_1", "tenant_1", "ws_1")
    
    # Publish 3 events (exceeds max_queue_size=2)
    for i in range(1, 4):
        event = RuntimeEvent(
            tenant_id="tenant_1",
            workspace_id="ws_1",
            canvas_id="canvas_1",
            graph_id="graph_1",
            thread_id="thread_1",
            execution_id="exec_1",
            event_type="node.started",
            sequence_number=i
        )
        bus.publish(event)
        
    # Queue size should be capped at 2
    assert queue.qsize() == 2
    
    # First item should be 2 (oldest item 1 is dropped)
    ev2 = await queue.get()
    ev3 = await queue.get()
    assert ev2.sequence_number == 2
    assert ev3.sequence_number == 3

from fastapi.testclient import TestClient
from services.dnk_canvas_api.main import app

def test_fastapi_websocket_missing_creds():
    """Test 18: Verify WebSocket rejects connection with missing query params (fail-closed)."""
    client = TestClient(app)
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws/executions/exec_123") as websocket:
            pass

def test_fastapi_control_resume_endpoint():
    """Test 19: Verify HTTP POST to resume execution publishes resumption event."""
    client = TestClient(app)
    bus = RuntimeEventBus.get_instance()
    bus.reset()
    
    queue = bus.subscribe("exec_resume_test", "tenant_x", "ws_x")
    
    payload = {
        "tenant_id": "tenant_x",
        "workspace_id": "ws_x",
        "canvas_id": "canvas_x",
        "resume_updates": {"step_name": "resume_node_a"}
    }
    
    response = client.post("/api/v1/executions/exec_resume_test/resume", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Assert event was published to the bus!
    assert queue.qsize() == 1
    event = queue.get_nowait()
    assert event.event_type == "graph.resumed"
    assert event.payload["step_name"] == "resume_node_a"

def test_fastapi_control_cancel_endpoint():
    """Test 20: Verify HTTP POST to cancel execution publishes cancellation event."""
    client = TestClient(app)
    bus = RuntimeEventBus.get_instance()
    bus.reset()
    
    queue = bus.subscribe("exec_cancel_test", "tenant_y", "ws_y")
    
    payload = {
        "tenant_id": "tenant_y",
        "workspace_id": "ws_y",
        "canvas_id": "canvas_y",
        "resume_updates": {}
    }
    
    response = client.post("/api/v1/executions/exec_cancel_test/cancel", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    # Assert event was published to the bus!
    assert queue.qsize() == 1
    event = queue.get_nowait()
    assert event.event_type == "graph.cancelled"


class MockRedis:
    def __init__(self):
        self.published = []

    def publish(self, channel, message):
        self.published.append((channel, message))
        return 1


def test_canvas_runtime_bridge_node_lifecycle_events():
    """Verify CanvasRuntimeBridge publishes node.created and node.executed to EventBus and Redis."""
    bus = RuntimeEventBus()
    mock_redis = MockRedis()
    bridge = CanvasRuntimeBridge(event_bus=bus, redis_client=mock_redis)

    ev_create = bridge.publish_node_created(
        node_id="n_100",
        name="SourceNode",
        node_type="agent_task",
        thread_id="th_lifecycle",
        execution_id="exec_lifecycle"
    )
    assert ev_create.event_type == "node.created"
    assert ev_create.node_id == "n_100"
    assert ev_create.sequence_number == 1

    ev_exec = bridge.publish_node_executed(
        node_id="n_100",
        status="completed",
        thread_id="th_lifecycle",
        execution_id="exec_lifecycle",
        execution_result={"processed": True}
    )
    assert ev_exec.event_type == "node.executed"
    assert ev_exec.node_id == "n_100"
    assert ev_exec.sequence_number == 2

    # Verify Redis publication
    assert len(mock_redis.published) == 2
    assert mock_redis.published[0][0] == "dnk:canvas:events"
    data0 = json.loads(mock_redis.published[0][1])
    assert data0["event_type"] == "node.created"
    data1 = json.loads(mock_redis.published[1][1])
    assert data1["event_type"] == "node.executed"


def test_canvas_runtime_bridge_selection_scenario():
    """Verify CanvasRuntimeBridge runs canvas selection scenario end-to-end."""
    bus = RuntimeEventBus()
    mock_redis = MockRedis()
    bridge = CanvasRuntimeBridge(event_bus=bus, redis_client=mock_redis)

    res = bridge.execute_selection_scenario(
        selection_id="sel_highlight_1",
        selected_nodes=[
            {"id": "node_a", "name": "PromptInput", "type": "prompt"},
            {"id": "node_b", "name": "LLMWorker", "type": "agent"}
        ],
        selection_bounds={"x": 50.0, "y": 80.0, "width": 600.0, "height": 400.0}
    )

    assert res["status"] == "success"
    assert res["selection_id"] == "sel_highlight_1"
    assert res["events_count"] == 6  # 1 parser created + 2 nodes created + 1 parser executed + 2 nodes executed
    assert len(mock_redis.published) == 6
    assert res["node_states"]["node_a"] == "completed"
    assert res["node_states"]["node_b"] == "completed"
    assert res["snapshot"]["status"] == "completed"

