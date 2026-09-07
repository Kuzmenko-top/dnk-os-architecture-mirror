# --- DNK-MRH-HEADER ---
# mrh_id: "tests_canvas_test_canvas_v3_models"
# purpose: "Unit tests for Canvas V3 ORM Models (DNK-CANVAS-003 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.db.models.canvas_spatial_index import CanvasSpatialIndexModel
from apps.api.db.models.canvas_presence import CanvasPresenceModel
from apps.api.db.models.canvas_cursor_stream import CanvasCursorStreamModel
from apps.api.db.models.canvas_history_snapshot import CanvasHistorySnapshotModel
from apps.api.db.models.canvas_ai_generation_request import CanvasAIGenerationRequestModel
from apps.api.db.models.canvas_semantic_group import CanvasSemanticGroupModel


def test_canvas_spatial_index_model():
    spatial = CanvasSpatialIndexModel(
        canvas_id="canvas-100",
        node_id="node-1",
        min_x=10.0,
        min_y=10.0,
        max_x=110.0,
        max_y=110.0,
        lod_level=0,
    )
    assert spatial.min_x == 10.0
    assert spatial.intersects((0.0, 0.0, 50.0, 50.0)) is True
    assert spatial.intersects((200.0, 200.0, 300.0, 300.0)) is False

    d = spatial.to_dict()
    assert d["canvas_id"] == "canvas-100"
    assert d["node_id"] == "node-1"
    assert d["max_x"] == 110.0


def test_canvas_presence_model():
    presence = CanvasPresenceModel(
        canvas_id="canvas-100",
        user_id="user-42",
        user_name="Maksym",
        user_color="#10b981",
        cursor_x=250.5,
        cursor_y=400.0,
        viewport_bounds={"min_x": 0, "min_y": 0, "max_x": 1920, "max_y": 1080},
        selected_node_ids=["node-1", "node-2"],
        active_tool="draw",
    )
    d = presence.to_dict()
    assert d["canvas_id"] == "canvas-100"
    assert d["user_name"] == "Maksym"
    assert d["active_tool"] == "draw"
    assert len(d["selected_node_ids"]) == 2


def test_canvas_cursor_stream_model():
    stream = CanvasCursorStreamModel(
        canvas_id="canvas-100",
        user_id="user-42",
        event_type="POINTER_MOVE",
        x=300.0,
        y=450.0,
        payload={"pressure": 0.8},
    )
    d = stream.to_dict()
    assert d["event_type"] == "POINTER_MOVE"
    assert d["x"] == 300.0
    assert d["payload"]["pressure"] == 0.8


def test_canvas_history_snapshot_model():
    snapshot = CanvasHistorySnapshotModel(
        canvas_id="canvas-100",
        version_index=3,
        snapshot_tag="v1.0-release",
        author_id="user-42",
        nodes_count=15,
        edges_count=20,
        state_diff_json={"added_nodes": ["node-15"]},
    )
    d = snapshot.to_dict()
    assert d["version_index"] == 3
    assert d["snapshot_tag"] == "v1.0-release"
    assert d["nodes_count"] == 15


def test_canvas_ai_generation_request_model():
    ai_req = CanvasAIGenerationRequestModel(
        canvas_id="canvas-100",
        requester_id="user-42",
        prompt="Generate checkout funnel steps with thank you node",
        context_node_ids=["node-start"],
        target_coordinates={"x": 500.0, "y": 300.0},
        status="PENDING",
    )
    d = ai_req.to_dict()
    assert d["canvas_id"] == "canvas-100"
    assert d["prompt"] == "Generate checkout funnel steps with thank you node"
    assert d["status"] == "PENDING"


def test_canvas_semantic_group_model():
    group = CanvasSemanticGroupModel(
        canvas_id="canvas-100",
        title="Checkout Microservices Group",
        color="#8b5cf6",
        node_ids=["node-1", "node-2", "node-3"],
        bounding_box={"min_x": 50, "min_y": 50, "max_x": 400, "max_y": 300},
        is_collapsed=False,
    )
    d = group.to_dict()
    assert d["title"] == "Checkout Microservices Group"
    assert len(d["node_ids"]) == 3
    assert d["is_collapsed"] is False
