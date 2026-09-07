# --- DNK-MRH-HEADER ---
# mrh_id: "tests_canvas_test_canvas_api_and_ws"
# purpose: "Integration & E2E tests for Canvas REST endpoints and WebSocket real-time sync (DNK-CANVAS-002 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_canvas_crud_flow():
    # 1. Create Canvas
    res = client.post("/api/v1/canvas", json={
        "name": "E2E Architecture Canvas",
        "workspace_id": "ws-alpha-001",
        "viewport_x": 100.0,
        "viewport_y": 50.0,
        "zoom": 1.25,
        "snap_to_grid": True,
        "grid_size": 20
    })
    assert res.status_code == 201
    data = res.json()
    canvas_id = data["id"]
    assert data["name"] == "E2E Architecture Canvas"
    assert data["workspace_id"] == "ws-alpha-001"

    # 2. List Canvases
    res = client.get("/api/v1/canvas?workspace_id=ws-alpha-001")
    assert res.status_code == 200
    canvases = res.json()
    assert any(c["id"] == canvas_id for c in canvases)

    # 3. Get Canvas Details
    res = client.get(f"/api/v1/canvas/{canvas_id}")
    assert res.status_code == 200
    details = res.json()
    assert details["id"] == canvas_id
    assert "nodes" in details
    assert "edges" in details

    # 4. Update Canvas
    res = client.put(f"/api/v1/canvas/{canvas_id}", json={
        "name": "Updated Canvas Name",
        "zoom": 1.5
    })
    assert res.status_code == 200
    updated = res.json()
    assert updated["name"] == "Updated Canvas Name"
    assert updated["viewport"]["zoom"] == 1.5

    # 5. Add Node
    res = client.post(f"/api/v1/canvas/{canvas_id}/nodes", json={
        "id": "node_test_1",
        "node_type": "supervisor",
        "title": "Supervisor Root",
        "x": 20.0,
        "y": 40.0,
        "width": 260.0,
        "height": 180.0,
        "data": {"role": "orchestrator"}
    })
    assert res.status_code == 201
    node_data = res.json()
    assert node_data["id"] == "node_test_1"
    assert node_data["title"] == "Supervisor Root"

    # 6. Move Node
    res = client.put(f"/api/v1/canvas/{canvas_id}/nodes/node_test_1/move", json={
        "x": 100.0,
        "y": 120.0
    })
    assert res.status_code == 200
    moved = res.json()
    assert moved["position"]["x"] == 100.0
    assert moved["position"]["y"] == 120.0

    # 7. Add Target Node & Edge
    res = client.post(f"/api/v1/canvas/{canvas_id}/nodes", json={
        "id": "node_test_2",
        "node_type": "agent",
        "title": "Worker Agent",
        "x": 300.0,
        "y": 120.0
    })
    assert res.status_code == 201

    res = client.post(f"/api/v1/canvas/{canvas_id}/edges", json={
        "id": "edge_test_1",
        "source_node_id": "node_test_1",
        "target_node_id": "node_test_2",
        "source_port": "output",
        "target_port": "input"
    })
    assert res.status_code == 201
    edge_data = res.json()
    assert edge_data["source_node_id"] == "node_test_1"
    assert edge_data["target_node_id"] == "node_test_2"

    # 8. Batch Move Nodes
    res = client.post(f"/api/v1/canvas/{canvas_id}/nodes/move-batch", json={
        "node_ids": ["node_test_1", "node_test_2"],
        "delta_x": 40.0,
        "delta_y": 20.0
    })
    assert res.status_code == 200
    batch_moved = res.json()
    assert len(batch_moved) == 2

    # 9. Delete Edge
    res = client.delete(f"/api/v1/canvas/{canvas_id}/edges/edge_test_1")
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"

    # 10. Delete Node
    res = client.delete(f"/api/v1/canvas/{canvas_id}/nodes/node_test_2")
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"

    # 11. Delete Canvas
    res = client.delete(f"/api/v1/canvas/{canvas_id}")
    assert res.status_code == 200
    assert res.json()["status"] == "deleted"


def test_generative_ui_and_sandbox_api():
    # 1. Synthesize Component
    res = client.post("/api/v1/canvas/generate-ui", json={
        "prompt": "Create an analytics KPI card with revenue, conversion rate and chart",
        "framework": "react"
    })
    assert res.status_code == 200
    comp = res.json()
    assert comp["framework"] == "react"
    assert "value" in comp["props_schema"]["properties"]
    assert "title" in comp["props_schema"]["properties"]
    assert len(comp["source_code"]) > 50

    # 2. Validate Props
    res = client.post("/api/v1/canvas/validate-props", json={
        "props": {"title": "Sales Report", "value": "$94,200", "trend": "up"},
        "schema_definition": comp["props_schema"]
    })
    assert res.status_code == 200
    validation = res.json()
    assert validation["valid"] is True
    assert len(validation["errors"]) == 0

    # 3. Sandbox Envelope Generation
    res = client.post("/api/v1/canvas/sandbox/envelope", json={
        "component_code": comp["source_code"],
        "props": {"title": "Live Test"},
        "framework": "react",
        "instance_id": "inst_001"
    })
    assert res.status_code == 200
    envelope = res.json()
    assert "Content-Security-Policy" in envelope["envelope_html"]
    assert 'id="root"' in envelope["envelope_html"]


def test_auto_layout_and_smart_connectors_api():
    # Create test canvas
    res = client.post("/api/v1/canvas", json={"name": "Auto Layout Canvas"})
    assert res.status_code == 201
    cid = res.json()["id"]

    # Add 3 nodes
    client.post(f"/api/v1/canvas/{cid}/nodes", json={"id": "sup_1", "node_type": "supervisor", "title": "Supervisor"})
    client.post(f"/api/v1/canvas/{cid}/nodes", json={"id": "ag_1", "node_type": "agent", "title": "Coder Agent"})
    client.post(f"/api/v1/canvas/{cid}/nodes", json={"id": "ui_1", "node_type": "component", "title": "UI Card"})

    # Auto layout
    res = client.post(f"/api/v1/canvas/{cid}/auto-layout", json={"layout_type": "horizontal_flow", "spacing_x": 220.0})
    assert res.status_code == 200
    layout_res = res.json()
    assert len(layout_res) == 3

    # Smart connectors
    res = client.post(f"/api/v1/canvas/{cid}/smart-connectors")
    assert res.status_code == 200
    edges = res.json()
    assert len(edges) >= 2


def test_canvas_websocket_collaboration():
    cid = "canvas_ws_e2e_test"
    # Ensure canvas is created in store
    client.post("/api/v1/canvas", json={"name": "WS Collab Canvas"})

    with client.websocket_connect(f"/api/v1/ws/canvas/{cid}?client_id=user_alice&user_name=Alice&color=%23ff0000") as ws:
        # 1. Receive Handshake
        raw = ws.receive_text()
        handshake = json.loads(raw)
        assert handshake["event"] == "handshake_ack"
        assert handshake["canvas_id"] == cid
        assert handshake["client_id"] == "user_alice"

        # 2. Send Ping
        ws.send_text(json.dumps({"action": "ping"}))
        pong = json.loads(ws.receive_text())
        assert pong["event"] == "pong"

        # 3. Move Cursor
        ws.send_text(json.dumps({"action": "cursor_move", "x": 150.0, "y": 250.0}))

        # 4. Acquire Node Lock
        ws.send_text(json.dumps({"action": "acquire_lock", "node_id": "node_ws_1", "timeout_seconds": 15.0}))
        lock_resp = json.loads(ws.receive_text())
        assert lock_resp["event"] == "lock_response"
        assert lock_resp["success"] is True

        # 5. Apply OCC Patch
        ws.send_text(json.dumps({
            "action": "apply_patch",
            "patch": {
                "op_type": "node_add",
                "base_version": handshake["current_version"],
                "payload": {"id": "node_ws_1", "title": "WS Node"}
            }
        }))
        patch_resp = json.loads(ws.receive_text())
        assert patch_resp["event"] == "patch_applied"
        assert patch_resp["version"] == 2

        # 6. Release Lock
        ws.send_text(json.dumps({"action": "release_lock", "node_id": "node_ws_1"}))
        rel_resp = json.loads(ws.receive_text())
        assert rel_resp["event"] == "release_lock_response"
        assert rel_resp["success"] is True
