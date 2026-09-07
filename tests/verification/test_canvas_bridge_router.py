# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_canvas_bridge_router.py"
# purpose: "Integration tests for FastAPI Canvas Bridge router (Obsidian Canvas ↔ React Flow SSOT)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK Swarm (gerych_auditor & Gerych Prime)"
# --- END DNK-MRH-HEADER ---

import json
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


@pytest.fixture
def sample_canvas_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".canvas", delete=False, encoding="utf-8") as f:
        doc = {
            "nodes": [
                {
                    "id": "node-1",
                    "type": "text",
                    "text": "## Architecture Foundation\n**Worker**: `dnk_dev_fullstack`\n- Status: In Progress",
                    "x": 100,
                    "y": 200,
                    "width": 350,
                    "height": 200,
                    "color": "3",
                },
                {
                    "id": "node-2",
                    "type": "text",
                    "text": "## UI Dashboard\n**Worker**: `gerych_builder`\n- [x] Run Tests",
                    "x": 550,
                    "y": 200,
                    "width": 350,
                    "height": 200,
                    "color": "5",
                },
            ],
            "edges": [
                {
                    "id": "edge-1",
                    "fromNode": "node-1",
                    "fromSide": "right",
                    "toNode": "node-2",
                    "toSide": "left",
                    "label": "depends_on",
                }
            ],
        }
        json.dump(doc, f, indent=2)
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_get_obsidian_as_react_flow(sample_canvas_file):
    response = client.get(f"/api/v1/canvas/bridge/obsidian?canvas_path={sample_canvas_file}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["node_count"] == 2
    assert data["edge_count"] == 1

    rf = data["react_flow"]
    assert len(rf["nodes"]) == 2
    assert rf["nodes"][0]["id"] == "node-1"
    assert rf["nodes"][0]["data"]["title"] == "Architecture Foundation"
    assert rf["nodes"][0]["data"]["worker"] == "dnk_dev_fullstack"
    assert rf["nodes"][0]["position"]["x"] == 100
    assert rf["nodes"][0]["position"]["y"] == 200


def test_save_react_flow_to_obsidian():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".canvas", delete=False, encoding="utf-8") as f:
        out_path = f.name

    try:
        flow_data = {
            "nodes": [
                {
                    "id": "task-flow-1",
                    "position": {"x": 250, "y": 150},
                    "dimensions": {"width": 320, "height": 180},
                    "data": {
                        "id": "task-flow-1",
                        "title": "API Gateway Setup",
                        "content": "## API Gateway Setup\n**Worker**: `dnk_dev_fullstack`\n- Setup complete",
                        "color": "4",
                        "worker": "dnk_dev_fullstack",
                    },
                }
            ],
            "edges": [],
        }

        response = client.post(
            "/api/v1/canvas/bridge/react-flow-to-canvas",
            json={"flow_data": flow_data, "canvas_path": out_path},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["node_count"] == 1

        # Verify on-disk file
        with open(out_path, "r", encoding="utf-8") as f:
            saved_canvas = json.load(f)
        assert len(saved_canvas["nodes"]) == 1
        assert saved_canvas["nodes"][0]["id"] == "task-flow-1"
        assert saved_canvas["nodes"][0]["x"] == 250
        assert saved_canvas["nodes"][0]["y"] == 150
        assert saved_canvas["nodes"][0]["color"] == "4"
    finally:
        if os.path.exists(out_path):
            os.remove(out_path)


def test_convert_canvas_to_flow_in_memory():
    canvas_doc = {
        "nodes": [
            {
                "id": "hud-node",
                "type": "text",
                "text": "# Swarm HUD\nActive tasks: 3",
                "x": 0,
                "y": 0,
                "width": 400,
                "height": 200,
                "color": "1",
            }
        ],
        "edges": [],
    }
    response = client.post(
        "/api/v1/canvas/bridge/convert/canvas-to-flow",
        json={"canvas_data": canvas_doc},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["react_flow"]["nodes"]) == 1
    assert data["react_flow"]["nodes"][0]["id"] == "hud-node"
    assert data["react_flow"]["nodes"][0]["data"]["title"] == "Swarm HUD"


def test_convert_flow_to_canvas_in_memory():
    flow_doc = {
        "nodes": [
            {
                "id": "node-mem-1",
                "position": {"x": 10, "y": 20},
                "dimensions": {"width": 300, "height": 150},
                "data": {
                    "id": "node-mem-1",
                    "title": "In Memory Node",
                    "content": "## In Memory Node\n**Worker**: `gerych_builder`",
                    "color": "5",
                    "worker": "gerych_builder",
                },
            }
        ],
        "edges": [],
    }
    response = client.post(
        "/api/v1/canvas/bridge/convert/flow-to-canvas",
        json={"flow_data": flow_doc},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    canvas = data["canvas"]
    assert len(canvas["nodes"]) == 1
    assert canvas["nodes"][0]["id"] == "node-mem-1"
    assert canvas["nodes"][0]["x"] == 10
    assert canvas["nodes"][0]["y"] == 20


def test_trigger_check_endpoint(sample_canvas_file):
    response = client.post(
        "/api/v1/canvas/bridge/trigger-check",
        json={"canvas_path": sample_canvas_file},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Node 2 had "- [x] Run Tests", so 1 action should be executed
    assert len(data["result"]) == 1
    assert data["result"][0]["action"] == "run_tests"
    assert data["result"][0]["node_id"] == "node-2"


def test_websocket_canvas_stream(sample_canvas_file):
    with client.websocket_connect(f"/api/v1/canvas/bridge/ws?canvas_path={sample_canvas_file}") as ws:
        # Receive INITIAL_STATE
        init_msg = ws.receive_json()
        assert init_msg["type"] == "INITIAL_STATE"
        assert init_msg["node_count"] == 2
        assert init_msg["edge_count"] == 1

        # Test PING
        ws.send_json({"action": "ping"})
        pong_msg = ws.receive_json()
        assert pong_msg["type"] == "PONG"

        # Test REFRESH
        ws.send_json({"action": "refresh"})
        refresh_msg = ws.receive_json()
        assert refresh_msg["type"] == "CANVAS_UPDATE"
        assert len(refresh_msg["react_flow"]["nodes"]) == 2

        # Test Reactive FileWatcher: modify file on disk externally
        import time
        time.sleep(0.1)
        with open(sample_canvas_file, "r") as f:
            canvas_content = json.load(f)
        canvas_content["nodes"].append({
            "id": "reactive-node",
            "type": "text",
            "text": "## Reactive Node\nObsidian external edit",
            "x": 600,
            "y": 100,
            "width": 250,
            "height": 120
        })
        with open(sample_canvas_file, "w") as f:
            json.dump(canvas_content, f)

        # File watcher ticks every 0.5s -> should push CANVAS_UPDATE
        watcher_msg = ws.receive_json()
        assert watcher_msg["type"] == "CANVAS_UPDATE"
        assert watcher_msg["source"] == "file_watcher"
        assert len(watcher_msg["react_flow"]["nodes"]) == 3


def test_merge_canvas_state_rest(sample_canvas_file):
    """
    Verifies OCC 3-Way Merge via REST API (/api/v1/canvas/bridge/merge):
    - Base snapshot has node-1
    - Disk has node-1 and node-2 (added by external Obsidian editor)
    - Client incoming has node-1 (repositioned/edited) and node-3 (added in React Flow)
    - Merged result must retain node-1, node-2, and node-3 without conflict loss.
    """
    # 1. Update disk canvas to have node-1 and node-2
    disk_data = {
        "nodes": [
            {
                "id": "node-1",
                "type": "text",
                "text": "## Root Goal\nInitial description",
                "x": 0,
                "y": 0,
                "width": 300,
                "height": 150
            },
            {
                "id": "node-2",
                "type": "text",
                "text": "## Obsidian Note\nAdded concurrently in Obsidian",
                "x": 400,
                "y": 0,
                "width": 250,
                "height": 120
            }
        ],
        "edges": []
    }
    with open(sample_canvas_file, "w") as f:
        json.dump(disk_data, f)

    # 2. Base snapshot (ancestor when client fetched canvas)
    base_flow = {
        "nodes": [
            {
                "id": "node-1",
                "type": "custom_node",
                "position": {"x": 0.0, "y": 0.0},
                "dimensions": {"width": 300.0, "height": 150.0},
                "data": {"title": "Root Goal", "content": "Initial description"}
            }
        ],
        "edges": []
    }

    # 3. Client incoming mutation: node-1 moved & node-3 created
    incoming_flow = {
        "nodes": [
            {
                "id": "node-1",
                "type": "custom_node",
                "position": {"x": 150.0, "y": 80.0},
                "dimensions": {"width": 320.0, "height": 160.0},
                "data": {"title": "Root Goal", "content": "Updated in React Flow"}
            },
            {
                "id": "node-3",
                "type": "custom_node",
                "position": {"x": 200.0, "y": 300.0},
                "dimensions": {"width": 250.0, "height": 120.0},
                "data": {"title": "Web UI Card", "content": "Added concurrently in Web UI"}
            }
        ],
        "edges": []
    }

    response = client.post(
        "/api/v1/canvas/bridge/merge",
        json={
            "canvas_path": sample_canvas_file,
            "base_flow": base_flow,
            "incoming_flow": incoming_flow,
            "position_strategy": "last_write_wins"
        }
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["has_unresolved_conflicts"] is False
    assert res_data["node_count"] == 3

    node_ids = {n["id"] for n in res_data["react_flow"]["nodes"]}
    assert node_ids == {"node-1", "node-2", "node-3"}

    # Verify disk canvas has also been updated
    with open(sample_canvas_file, "r") as f:
        saved_canvas = json.load(f)
    saved_ids = {n["id"] for n in saved_canvas.get("nodes", [])}
    assert saved_ids == {"node-1", "node-2", "node-3"}


def test_websocket_canvas_occ_merge(sample_canvas_file):
    """
    Verifies OCC 3-Way Merge via WebSocket action 'merge'.
    """
    # Setup disk canvas with node-1 and node-2
    disk_data = {
        "nodes": [
            {"id": "node-1", "type": "text", "text": "## Base\nContent", "x": 0, "y": 0, "width": 200, "height": 100},
            {"id": "node-2", "type": "text", "text": "## Branch\nObsidian", "x": 300, "y": 0, "width": 200, "height": 100}
        ],
        "edges": []
    }
    with open(sample_canvas_file, "w") as f:
        json.dump(disk_data, f)

    base_flow = {
        "nodes": [{"id": "node-1", "position": {"x": 0, "y": 0}, "data": {"title": "Base"}}],
        "edges": []
    }
    incoming_flow = {
        "nodes": [
            {"id": "node-1", "position": {"x": 50, "y": 50}, "data": {"title": "Base Mod"}},
            {"id": "node-3", "position": {"x": 500, "y": 100}, "data": {"title": "Web Node"}}
        ],
        "edges": []
    }

    with client.websocket_connect(f"/api/v1/canvas/bridge/ws?canvas_path={sample_canvas_file}") as ws:
        init_msg = ws.receive_json()
        assert init_msg["type"] == "INITIAL_STATE"

        ws.send_json({
            "action": "merge",
            "base_flow": base_flow,
            "incoming_flow": incoming_flow,
            "position_strategy": "last_write_wins"
        })

        merge_msg = ws.receive_json()
        assert merge_msg["type"] == "MERGED"
        assert merge_msg["status"] == "success"
        merged_ids = {n["id"] for n in merge_msg["react_flow"]["nodes"]}
        assert merged_ids == {"node-1", "node-2", "node-3"}


def test_swarm_hud_rest_event_broadcast(sample_canvas_file):
    """
    Verifies Swarm HUD REST endpoint:
    - Formats worker badge, hex, canvas color and progress bar.
    - Supports alias /swarm-hud and /events/swarm.
    - Updates canvas disk state when requested.
    """
    res1 = client.post(
        "/api/v1/canvas/bridge/events/swarm",
        json={
            "task_id": "node-1",
            "event_type": "TASK_STARTED",
            "assigned_agent": "gerych_builder",
            "canvas_path": sample_canvas_file,
            "progress_pct": 25,
            "message": "Scaffolding React Flow HUD",
            "update_canvas_disk": True,
        },
    )
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "broadcasted"
    assert data1["assigned_agent"] == "gerych_builder"
    assert "Gerych Builder" in data1["agent_badge"]
    assert data1["canvas_color"] == "5"
    assert data1["hex_color"] == "#3B82F6"
    assert data1["progress_pct"] == 25
    assert data1["progress_bar"] is not None
    assert data1["disk_updated"] is True

    # Check alias /swarm-hud with Shopify worker
    res2 = client.post(
        "/api/v1/canvas/bridge/swarm-hud",
        json={
            "task_id": "node-2",
            "event_type": "TASK_PROGRESS",
            "assigned_agent": "dnk_shopify",
            "canvas_path": sample_canvas_file,
            "progress_pct": 80,
            "message": "Compiling Liquid Theme AST",
            "update_canvas_disk": False,
        },
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["assigned_agent"] == "dnk_shopify"
    assert "Shopify" in data2["agent_badge"]
    assert data2["canvas_color"] == "4"
    assert data2["hex_color"] == "#10B981"
    assert data2["progress_pct"] == 80


def test_swarm_hud_websocket_broadcast(sample_canvas_file):
    """
    Verifies that a Swarm HUD event published via REST is pushed
    in real time to connected WebSocket clients as SWARM_HUD_EVENT.
    """
    with client.websocket_connect(f"/api/v1/canvas/bridge/ws?canvas_path={sample_canvas_file}") as ws:
        init_msg = ws.receive_json()
        assert init_msg["type"] == "INITIAL_STATE"

        # Publish event via REST while client is connected
        res = client.post(
            "/api/v1/canvas/bridge/events/swarm",
            json={
                "task_id": "node-1",
                "event_type": "TASK_PROGRESS",
                "assigned_agent": "gerych_auditor",
                "canvas_path": sample_canvas_file,
                "progress_pct": 95,
                "message": "Adversarial security review passing",
                "update_canvas_disk": False,
            },
        )
        assert res.status_code == 200
        assert res.json()["clients_notified"] >= 1

        # Receive on websocket
        hud_msg = ws.receive_json()
        assert hud_msg["type"] == "SWARM_HUD_EVENT"
        assert hud_msg["task_id"] == "node-1"
        assert hud_msg["event_type"] == "TASK_PROGRESS"
        assert hud_msg["assigned_agent"] == "gerych_auditor"
        assert "Auditor" in hud_msg["agent_badge"]
        assert hud_msg["canvas_color"] == "1"
        assert hud_msg["hex_color"] == "#EF4444"
        assert hud_msg["progress_pct"] == 95
        assert hud_msg["progress_bar"] is not None


def test_swarm_hud_websocket_client_event(sample_canvas_file):
    """
    Verifies WebSocket client sending action='swarm_event' receives SWARM_EVENT_ACK
    and SWARM_HUD_EVENT broadcast.
    """
    with client.websocket_connect(f"/api/v1/canvas/bridge/ws?canvas_path={sample_canvas_file}") as ws:
        init_msg = ws.receive_json()
        assert init_msg["type"] == "INITIAL_STATE"

        ws.send_json({
            "action": "swarm_event",
            "task_id": "ws-node",
            "event_type": "TASK_COMPLETED",
            "assigned_agent": "dnk_dev_fullstack",
            "progress_pct": 100,
            "message": "FastAPI schema validated",
            "update_canvas_disk": False,
        })

        # Can receive broadcast first or ack
        msgs = [ws.receive_json(), ws.receive_json()]
        types = {m["type"] for m in msgs}
        assert "SWARM_HUD_EVENT" in types
        assert "SWARM_EVENT_ACK" in types

        hud_event = next(m for m in msgs if m["type"] == "SWARM_HUD_EVENT")
        assert hud_event["assigned_agent"] == "dnk_dev_fullstack"
        assert hud_event["stage"] == "completed"
        assert "Fullstack" in hud_event["agent_badge"]
        assert hud_event["canvas_color"] == "5"
        assert hud_event["hex_color"] == "#06B6D4"




