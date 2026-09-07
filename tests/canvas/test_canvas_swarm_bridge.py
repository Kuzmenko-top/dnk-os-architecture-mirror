# --- DNK-MRH-HEADER ---
# mrh_id: "tests_canvas_test_canvas_swarm_bridge"
# purpose: "Integration & E2E tests for Canvas Swarm Bridge WebSocket real-time execution, agent log streaming, and multi-version endpoint compatibility (Phase 1)"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# alters_files: []
# triggers_tasks: []
# --- END DNK-MRH-HEADER ---

import json
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_swarm_ws_ping_pong():
    """Test standard PING / PONG handshake on /ws endpoint."""
    with client.websocket_connect("/ws") as websocket:
        websocket.send_json({"type": "PING"})
        data = websocket.receive_json()
        assert data.get("type") == "PONG"
        assert "timestamp" in data


def test_swarm_ws_task_execution_stream():
    """Test full TASK_EXECUTE streaming lifecycle on /ws endpoint."""
    with client.websocket_connect("/ws") as websocket:
        node_id = "node-test-swarm-001"
        websocket.send_json({
            "type": "TASK_EXECUTE",
            "nodeId": node_id,
            "taskType": "dnk_dev_fullstack",
            "context": {
                "prompt": "Build Pydantic schema for checkout session",
                "projectId": "canvas-alpha-001"
            }
        })

        messages = []
        for _ in range(6):
            msg = websocket.receive_json()
            messages.append(msg)
            if msg.get("type") == "TASK_STATUS" and msg.get("status") == "completed":
                break

        types = [m.get("type") for m in messages]
        assert "TASK_STATUS" in types
        assert "AGENT_LOG" in types

        thinking_msg = next((m for m in messages if m.get("type") == "TASK_STATUS" and m.get("status") == "thinking"), None)
        assert thinking_msg is not None
        assert thinking_msg.get("nodeId") == node_id

        completed_msg = next((m for m in messages if m.get("type") == "TASK_STATUS" and m.get("status") == "completed"), None)
        assert completed_msg is not None
        assert completed_msg.get("nodeId") == node_id
        assert "metrics" in completed_msg
        assert "trace_id" in completed_msg


def test_canvas_v1_ws_task_execution_bridge():
    """Test that Canvas V1 WebSocket (/api/v1/ws/canvas/{id}) transparently handles TASK_EXECUTE."""
    with client.websocket_connect("/api/v1/ws/canvas/canvas-test-bridge") as websocket:
        handshake = websocket.receive_json()
        assert handshake.get("event") == "handshake_ack"

        node_id = "node-v1-bridge-002"
        websocket.send_text(json.dumps({
            "type": "TASK_EXECUTE",
            "nodeId": node_id,
            "taskType": "dnk_shopify",
            "context": {
                "prompt": "Generate Shopify checkout liquid spec",
                "projectId": "canvas-test-bridge"
            }
        }))

        received_types = []
        received_logs = []
        for _ in range(6):
            msg = websocket.receive_json()
            received_types.append(msg.get("type"))
            if msg.get("type") == "AGENT_LOG":
                received_logs.append(msg)
            if msg.get("type") == "TASK_STATUS" and msg.get("status") == "completed":
                break

        assert "TASK_STATUS" in received_types
        assert len(received_logs) >= 1
        assert any("liquid" in l.get("text", "").lower() or "worker" in l.get("text", "").lower() or "usersoul" in l.get("text", "").lower() or "dispatched" in l.get("text", "").lower() for l in received_logs)


def test_canvas_v3_ws_task_execution_bridge():
    """Test that Canvas V3 WebSocket (/api/v3/ws/canvas) handles TASK_EXECUTE."""
    with client.websocket_connect("/api/v3/ws/canvas") as websocket:
        node_id = "node-v3-bridge-003"
        websocket.send_text(json.dumps({
            "type": "TASK_EXECUTE",
            "nodeId": node_id,
            "taskType": "dnk_dev_fullstack",
            "context": {
                "prompt": "FastAPI router generation",
                "projectId": "canvas-v3-test"
            }
        }))

        first_msg = websocket.receive_json()
        assert first_msg.get("type") == "CONNECTED"

        messages = []
        for _ in range(6):
            msg = websocket.receive_json()
            messages.append(msg)
            if msg.get("type") == "TASK_STATUS" and msg.get("status") == "completed":
                break

        completed = any(m.get("type") == "TASK_STATUS" and m.get("status") == "completed" for m in messages)
        assert completed
