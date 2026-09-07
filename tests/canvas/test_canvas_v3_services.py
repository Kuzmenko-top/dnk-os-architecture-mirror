# --- DNK-MRH-HEADER ---
# mrh_id: "tests_canvas_test_canvas_v3_services"
# purpose: "Unit tests for Canvas V3 Spatial Index Engine & Collaboration Arbiter (DNK-CANVAS-003 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import time
import pytest
from apps.api.services.canvas_spatial_index_engine import (
    CanvasSpatialIndexEngine,
    SpatialItem,
)
from apps.api.services.canvas_collaboration_arbiter import (
    CanvasCollaborationArbiter,
    NodeLock,
)


def test_spatial_item_intersection():
    item = SpatialItem("n1", 0.0, 0.0, 100.0, 100.0, lod_level=0)
    assert item.center_x == 50.0
    assert item.center_y == 50.0
    assert item.width == 100.0
    assert item.height == 100.0
    assert item.intersects((50.0, 50.0, 150.0, 150.0)) is True
    assert item.intersects((101.0, 101.0, 200.0, 200.0)) is False


def test_spatial_index_engine_crud_and_viewport():
    engine = CanvasSpatialIndexEngine(canvas_id="canvas-001", grid_cell_size=200.0)

    # Insert nodes
    engine.insert_node("node-1", 0.0, 0.0, 100.0, 100.0, lod_level=0)
    engine.insert_node("node-2", 300.0, 300.0, 400.0, 400.0, lod_level=1)
    engine.insert_node("node-3", 1000.0, 1000.0, 1100.0, 1100.0, lod_level=2)

    stats = engine.get_stats()
    assert stats["total_nodes_indexed"] == 3
    assert stats["total_active_grid_cells"] > 0

    # Query viewport covering node-1 and node-2
    vp_res = engine.query_viewport((-50.0, -50.0, 500.0, 500.0))
    node_ids = {n["node_id"] for n in vp_res}
    assert "node-1" in node_ids
    assert "node-2" in node_ids
    assert "node-3" not in node_ids

    # Query with LOD filter <= 0
    lod0_res = engine.query_viewport((-50.0, -50.0, 500.0, 500.0), lod_filter=0)
    assert len(lod0_res) == 1
    assert lod0_res[0]["node_id"] == "node-1"

    # Update node
    engine.update_node("node-1", 50.0, 50.0, 150.0, 150.0)
    assert engine.items["node-1"].min_x == 50.0

    # Remove node
    assert engine.remove_node("node-3") is True
    assert engine.remove_node("non-existent") is False
    assert len(engine.items) == 2


def test_spatial_index_nearest_neighbors_and_bbox():
    engine = CanvasSpatialIndexEngine(canvas_id="canvas-002", grid_cell_size=100.0)
    nodes = [
        {"node_id": "a", "x": 10.0, "y": 10.0, "width": 20.0, "height": 20.0},
        {"node_id": "b", "x": 50.0, "y": 50.0, "width": 20.0, "height": 20.0},
        {"node_id": "c", "x": 500.0, "y": 500.0, "width": 20.0, "height": 20.0},
    ]
    count = engine.bulk_index_nodes(nodes)
    assert count == 3

    # Nearest to (0, 0)
    nn = engine.find_nearest_neighbors(x=0.0, y=0.0, k=2, max_distance=200.0)
    assert len(nn) == 2
    assert nn[0]["node_id"] == "a"
    assert nn[1]["node_id"] == "b"

    # Compute bounding box
    bbox = engine.compute_bounding_box(["a", "b"])
    assert bbox is not None
    assert bbox["min_x"] == 10.0
    assert bbox["min_y"] == 10.0
    assert bbox["max_x"] == 70.0
    assert bbox["max_y"] == 70.0


def test_collaboration_arbiter_locks():
    arbiter = CanvasCollaborationArbiter(canvas_id="canvas-003")

    # User 1 acquires lock on node-1
    res1 = arbiter.acquire_node_lock("node-1", user_id="u1", user_name="Alice", ttl_sec=10.0)
    assert res1["success"] is True
    assert res1["status"] == "ACQUIRED"

    # User 2 tries to acquire lock on node-1 -> fails
    res2 = arbiter.acquire_node_lock("node-1", user_id="u2", user_name="Bob")
    assert res2["success"] is False
    assert res2["status"] == "LOCKED_BY_OTHER"
    assert res2["locked_by"]["user_id"] == "u1"

    # User 1 renews lock
    res3 = arbiter.acquire_node_lock("node-1", user_id="u1", ttl_sec=20.0)
    assert res3["success"] is True
    assert res3["status"] == "RENEWED"

    # Check active locks
    locks = arbiter.get_locked_nodes()
    assert "node-1" in locks
    assert locks["node-1"]["user_id"] == "u1"

    # Release lock
    assert arbiter.release_node_lock("node-1", user_id="u2") is False
    assert arbiter.release_node_lock("node-1", user_id="u1") is True
    assert len(arbiter.get_locked_nodes()) == 0


def test_collaboration_arbiter_presence_and_cursor():
    arbiter = CanvasCollaborationArbiter(canvas_id="canvas-004")

    # Record presence
    p = arbiter.record_presence_heartbeat(
        user_id="u1",
        user_name="Alice",
        user_color="#ef4444",
        cursor_x=100.0,
        cursor_y=200.0,
        selected_node_ids=["node-1"],
        active_tool="pen",
    )
    assert p["user_id"] == "u1"
    assert p["active_tool"] == "pen"

    active = arbiter.get_active_presences(timeout_sec=5.0)
    assert len(active) == 1
    assert active[0]["user_id"] == "u1"

    # Process cursor move event
    ev = arbiter.process_cursor_event("u1", "POINTER_MOVE", x=150.0, y=250.0)
    assert ev["event_type"] == "POINTER_MOVE"
    assert arbiter.presences["u1"]["cursor_x"] == 150.0
    assert arbiter.presences["u1"]["cursor_y"] == 250.0

    stream = arbiter.get_cursor_stream("u1")
    assert len(stream) == 1

    # Prune stale
    time.sleep(0.05)
    pruned = arbiter.prune_stale_presences(timeout_sec=0.01)
    assert pruned == 1
    assert len(arbiter.get_active_presences()) == 0
