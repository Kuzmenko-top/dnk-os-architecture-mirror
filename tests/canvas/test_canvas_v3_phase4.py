# --- DNK-MRH-HEADER ---
# mrh_id: "tests_canvas_test_canvas_v3_phase4"
# purpose: "Integration and E2E unit tests for Canvas V3 REST and WebSocket APIs (DNK-CANVAS-003 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_canvas_v3_spatial_rest_endpoints():
    canvas_id = "canvas-test-spatial-001"

    # 1. Bulk index nodes
    nodes_payload = {
        "nodes": [
            {"node_id": "n1", "min_x": 0.0, "min_y": 0.0, "max_x": 100.0, "max_y": 100.0, "lod_level": 0},
            {"node_id": "n2", "min_x": 150.0, "min_y": 150.0, "max_x": 250.0, "max_y": 250.0, "lod_level": 1},
            {"node_id": "n3", "min_x": 1000.0, "min_y": 1000.0, "max_x": 1100.0, "max_y": 1100.0, "lod_level": 0},
        ]
    }
    res = client.post(f"/api/v3/canvas/{canvas_id}/spatial/index", json=nodes_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["canvas_id"] == canvas_id
    assert data["indexed_count"] == 3

    # 2. Viewport query
    query_payload = {
        "min_x": -50.0,
        "min_y": -50.0,
        "max_x": 300.0,
        "max_y": 300.0
    }
    res = client.post(f"/api/v3/canvas/{canvas_id}/spatial/query", json=query_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_visible_nodes"] == 2
    node_ids = {n["node_id"] for n in data["nodes"]}
    assert node_ids == {"n1", "n2"}

    # 3. Nearest neighbors
    res_nn = client.post(f"/api/v3/canvas/{canvas_id}/spatial/nearest?x=10.0&y=10.0&k=2")
    assert res_nn.status_code == 200
    nn_data = res_nn.json()
    assert nn_data["total_neighbors"] >= 1
    assert nn_data["neighbors"][0]["node_id"] == "n1"


def test_canvas_v3_locking_and_presence_rest():
    canvas_id = "canvas-test-collab-001"

    # 1. Acquire Lock
    lock_req = {
        "node_id": "node-target-42",
        "user_id": "user-alpha",
        "user_name": "Alice Developer",
        "ttl_sec": 20.0
    }
    res = client.post(f"/api/v3/canvas/{canvas_id}/lock/acquire", json=lock_req)
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 2. Conflicting Lock Attempt
    conflict_req = {
        "node_id": "node-target-42",
        "user_id": "user-beta",
        "user_name": "Bob Designer",
        "ttl_sec": 10.0
    }
    res_conflict = client.post(f"/api/v3/canvas/{canvas_id}/lock/acquire", json=conflict_req)
    assert res_conflict.status_code == 409

    # 3. List Locks
    res_list = client.get(f"/api/v3/canvas/{canvas_id}/lock/list")
    assert res_list.status_code == 200
    locks = res_list.json()["locks"]
    assert "node-target-42" in locks
    assert locks["node-target-42"]["user_id"] == "user-alpha"

    # 4. Release Lock
    rel_req = {"node_id": "node-target-42", "user_id": "user-alpha"}
    res_rel = client.post(f"/api/v3/canvas/{canvas_id}/lock/release", json=rel_req)
    assert res_rel.status_code == 200
    assert res_rel.json()["success"] is True

    # 5. Presence Heartbeat & List
    heartbeat_req = {
        "user_id": "user-alpha",
        "user_name": "Alice Developer",
        "user_color": "#10b981",
        "cursor_x": 120.0,
        "cursor_y": 340.0,
        "active_tool": "select",
        "viewport": {"x": 0, "y": 0, "zoom": 1.0}
    }
    res_hb = client.post(f"/api/v3/canvas/{canvas_id}/presence/heartbeat", json=heartbeat_req)
    assert res_hb.status_code == 200
    assert res_hb.json()["success"] is True

    res_active = client.get(f"/api/v3/canvas/{canvas_id}/presence/active")
    assert res_active.status_code == 200
    presences = res_active.json()["presences"]
    matching = [p for p in presences if p["user_id"] == "user-alpha"]
    assert len(matching) == 1
    assert matching[0]["cursor_x"] == 120.0

    # 6. Cursor Event
    cursor_req = {
        "user_id": "user-alpha",
        "event_type": "move",
        "x": 130.0,
        "y": 350.0,
        "payload": {"pressure": 0.8}
    }
    res_cur = client.post(f"/api/v3/canvas/{canvas_id}/cursor/event", json=cursor_req)
    assert res_cur.status_code == 200
    assert res_cur.json()["success"] is True


def test_canvas_v3_ai_weaver_rest():
    canvas_id = "canvas-test-ai-001"

    # 1. AI Generate Subflow
    ai_req = {
        "prompt": "Create automated payment verification pipeline with retry queue",
        "auto_group": True,
        "group_title": "Payment Automation Group"
    }
    res = client.post(f"/api/v3/canvas/{canvas_id}/ai/generate-subflow", json=ai_req)
    assert res.status_code == 200
    data = res.json()
    assert len(data["nodes"]) >= 3
    assert len(data["edges"]) >= 2
    assert data["group"] is not None
    assert data["group"]["title"] == "Payment Automation Group"

    # 2. Semantic Group Creation
    group_req = {
        "title": "Manual Test Cluster",
        "nodes": [
            {"id": "c1", "x": 100.0, "y": 100.0, "width": 120.0, "height": 60.0},
            {"id": "c2", "x": 300.0, "y": 200.0, "width": 150.0, "height": 80.0}
        ],
        "color": "#8b5cf6"
    }
    res = client.post(f"/api/v3/canvas/{canvas_id}/ai/create-group", json=group_req)
    assert res.status_code == 200
    grp = res.json()
    assert grp["title"] == "Manual Test Cluster"
    assert grp["bounding_box"]["min_x"] <= 100.0


def test_canvas_v3_time_travel_rest():
    canvas_id = "canvas-test-tt-001"

    # 1. Record Snapshots
    s1 = client.post(f"/api/v3/canvas/{canvas_id}/history/snapshot", json={
        "author_id": "dev-1",
        "state_data": {"nodes": [{"id": "a"}], "edges": []},
        "snapshot_tag": "Initial Setup"
    })
    assert s1.status_code == 200
    s1_id = s1.json()["id"]

    s2 = client.post(f"/api/v3/canvas/{canvas_id}/history/snapshot", json={
        "author_id": "dev-1",
        "state_data": {"nodes": [{"id": "a"}, {"id": "b"}], "edges": [{"id": "e1", "source": "a", "target": "b"}]},
        "snapshot_tag": "Added Node B"
    })
    assert s2.status_code == 200

    # 2. List History
    res = client.get(f"/api/v3/canvas/{canvas_id}/history/list")
    assert res.status_code == 200
    assert res.json()["total_snapshots"] == 2

    # 3. Undo
    res_undo = client.post(f"/api/v3/canvas/{canvas_id}/history/undo")
    assert res_undo.status_code == 200
    assert len(res_undo.json()["restored_state"]["nodes"]) == 1

    # 4. Redo
    res_redo = client.post(f"/api/v3/canvas/{canvas_id}/history/redo")
    assert res_redo.status_code == 200
    assert len(res_redo.json()["restored_state"]["nodes"]) == 2

    # 5. Branch & Merge
    res_branch = client.post(f"/api/v3/canvas/{canvas_id}/history/branch", json={
        "branch_name": "experimental-feature",
        "from_snapshot_id": s1_id
    })
    assert res_branch.status_code == 200
    assert res_branch.json()["branch_name"] == "experimental-feature"

    res_merge = client.post(f"/api/v3/canvas/{canvas_id}/history/merge", json={
        "source_branch": "experimental-feature",
        "target_branch": "main",
        "strategy": "union"
    })
    assert res_merge.status_code == 200
    assert res_merge.json()["strategy"] == "union"


def test_canvas_v3_websocket_multiplexing():
    canvas_id = "canvas-ws-test-room-99"

    with client.websocket_connect(f"/api/v3/ws/canvas/{canvas_id}?user_id=usr_alex&user_name=Alex") as ws:
        # Initial greeting / connection ack
        init_msg = ws.receive_json()
        assert init_msg["type"] == "CONNECTED"
        assert init_msg["canvas_id"] == canvas_id
        assert init_msg["user_id"] == "usr_alex"

        # Send Presence Heartbeat
        ws.send_json({
            "action": "PRESENCE_HEARTBEAT",
            "user_name": "Alex",
            "cursor_x": 450.0,
            "cursor_y": 600.0,
            "active_tool": "pan"
        })
        ack1 = ws.receive_json()
        assert ack1["type"] == "PRESENCE_ACK"
        assert ack1["status"] == "ok"

        # Send Cursor Delta Stream
        ws.send_json({
            "action": "CURSOR_STREAM",
            "event_type": "move",
            "x": 455.0,
            "y": 605.0
        })
        ack2 = ws.receive_json()
        assert ack2["type"] == "CURSOR_ACK"
        assert ack2["status"] == "ok"

        # Send Lock Acquire
        ws.send_json({
            "action": "LOCK_ACQUIRE",
            "node_id": "node-flow-777",
            "ttl_sec": 30.0
        })
        ack3 = ws.receive_json()
        assert ack3["type"] == "LOCK_RESULT"
        assert ack3["node_id"] == "node-flow-777"
        assert ack3["success"] is True

        # Send Lock Release
        ws.send_json({
            "action": "LOCK_RELEASE",
            "node_id": "node-flow-777"
        })
        ack4 = ws.receive_json()
        assert ack4["type"] == "LOCK_RELEASED"
        assert ack4["success"] is True

        # Send Ping
        ws.send_json({"action": "PING"})
        ack5 = ws.receive_json()
        assert ack5["type"] == "PONG"
