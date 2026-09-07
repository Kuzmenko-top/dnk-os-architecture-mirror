# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-CANVAS-002-TEST-ENGINE-OCC"
# purpose: "Unit tests for Canvas Graph Engine & OCC Real-Time State Sync (DNK-CANVAS-002 Phase 2)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import time
import pytest
from apps.api.services.canvas_graph_engine import (
    Point,
    Rect,
    CanvasSpatialMath,
    CanvasGraphEngine
)
from apps.api.services.canvas_occ_sync import (
    PatchOpType,
    CanvasPatchOp,
    CanvasOCCSyncManager
)


def test_spatial_math_coordinate_transforms():
    # World (100, 200) with Viewport (0, 0) and Zoom 2.0 -> Screen (200, 400)
    screen_pt = CanvasSpatialMath.world_to_screen(100.0, 200.0, 0.0, 0.0, 2.0)
    assert screen_pt.x == 200.0
    assert screen_pt.y == 400.0

    # Screen (200, 400) -> World (100, 200)
    world_pt = CanvasSpatialMath.screen_to_world(200.0, 400.0, 0.0, 0.0, 2.0)
    assert world_pt.x == 100.0
    assert world_pt.y == 200.0

    # Snapping
    assert CanvasSpatialMath.snap_to_grid(18.0, 16) == 16.0
    assert CanvasSpatialMath.snap_to_grid(25.0, 16) == 32.0


def test_rect_and_bounding_box():
    r1 = Rect(x=10, y=10, width=50, height=50)
    r2 = Rect(x=30, y=30, width=50, height=50)
    r3 = Rect(x=100, y=100, width=50, height=50)

    assert r1.intersects(r2) is True
    assert r1.intersects(r3) is False
    assert r1.contains(20, 20) is True
    assert r1.contains(70, 70) is False

    nodes = [
        {"position": {"x": 100, "y": 100}, "dimensions": {"width": 100, "height": 50}},
        {"position": {"x": 300, "y": 250}, "dimensions": {"width": 150, "height": 80}}
    ]
    bbox = CanvasSpatialMath.calculate_bounding_box(nodes)
    assert bbox is not None
    assert bbox.x == 100
    assert bbox.y == 100
    assert bbox.width == 350  # (300+150) - 100
    assert bbox.height == 230  # (250+80) - 100


def test_canvas_graph_engine_crud_and_snapping():
    engine = CanvasGraphEngine(canvas_id="c1", grid_size=10, snap_to_grid=True)

    n1 = engine.add_node("n1", "component", "Hero", 12.0, 19.0, 200, 100)
    assert n1["position"]["x"] == 10.0
    assert n1["position"]["y"] == 20.0

    moved = engine.move_node("n1", 98.0, 104.0)
    assert moved is not None
    assert moved["position"]["x"] == 100.0
    assert moved["position"]["y"] == 100.0

    # Batch move
    n2 = engine.add_node("n2", "agent", "Worker", 200.0, 200.0)
    batch = engine.move_nodes_batch(["n1", "n2"], delta_x=10, delta_y=10)
    assert len(batch) == 2


def test_canvas_graph_edge_and_cycle_prevention():
    engine = CanvasGraphEngine(canvas_id="c1")
    engine.add_node("A", "task", "Task A", 0, 0)
    engine.add_node("B", "task", "Task B", 100, 0)
    engine.add_node("C", "task", "Task C", 200, 0)

    e1, err = engine.add_edge("e1", "A", "B")
    assert e1 is not None
    assert err is None

    e2, err = engine.add_edge("e2", "B", "C")
    assert e2 is not None
    assert err is None

    # Attempt cycle: C -> A
    e3, err = engine.add_edge("e3", "C", "A", allow_cycles=False)
    assert e3 is None
    assert err is not None and "introduces a cycle" in err

    # Self reference
    e_self, err_self = engine.add_edge("e_self", "A", "A")
    assert e_self is None
    assert err_self is not None and "Self-referencing" in err_self


def test_canvas_graph_topological_sort_and_downstream():
    engine = CanvasGraphEngine(canvas_id="c1")
    engine.add_node("A", "task", "A", 0, 0)
    engine.add_node("B", "task", "B", 100, 0)
    engine.add_node("C", "task", "C", 200, 0)
    engine.add_node("D", "task", "D", 300, 0)

    engine.add_edge("e1", "A", "B")
    engine.add_edge("e2", "B", "C")
    engine.add_edge("e3", "A", "D")

    order, valid = engine.topological_sort()
    assert valid is True
    assert order.index("A") < order.index("B")
    assert order.index("B") < order.index("C")
    assert order.index("A") < order.index("D")

    downstream = engine.find_downstream_nodes("A")
    assert set(downstream) == {"B", "C", "D"}

    downstream_b = engine.find_downstream_nodes("B")
    assert downstream_b == ["C"]


def test_canvas_marquee_selection():
    engine = CanvasGraphEngine(canvas_id="c1", snap_to_grid=False)
    engine.add_node("N1", "task", "N1", 50, 50, 50, 50)
    engine.add_node("N2", "task", "N2", 200, 200, 50, 50)
    engine.add_node("N3", "task", "N3", 500, 500, 50, 50)

    marquee = Rect(x=0, y=0, width=150, height=150)
    selected = engine.select_nodes_in_marquee(marquee)
    assert selected == ["N1"]

    marquee_all = Rect(x=0, y=0, width=600, height=600)
    assert set(engine.select_nodes_in_marquee(marquee_all)) == {"N1", "N2", "N3"}


def test_canvas_occ_sync_locks_and_patches():
    manager = CanvasOCCSyncManager(canvas_id="c1", initial_version=1)

    # Acquire lock
    ok, err = manager.acquire_lock("node_1", "client_A")
    assert ok is True
    assert err is None

    # Client B fails to acquire locked node
    ok_b, err_b = manager.acquire_lock("node_1", "client_B")
    assert ok_b is False
    assert err_b is not None and "currently locked by client 'client_A'" in err_b

    # Add Node patch
    p_add = CanvasPatchOp(
        op_type=PatchOpType.NODE_ADD,
        client_id="client_A",
        base_version=1,
        payload={"id": "node_1", "title": "Card 1", "position": {"x": 100, "y": 100}}
    )
    ok, v, res, err = manager.apply_patch(p_add)
    assert ok is True
    assert v == 2
    assert "node_1" in manager.state_nodes

    # Client B fails to move node locked by client A
    p_move_b = CanvasPatchOp(
        op_type=PatchOpType.NODE_MOVE,
        client_id="client_B",
        base_version=2,
        payload={"node_id": "node_1", "x": 200, "y": 200}
    )
    ok_mb, _, _, err_mb = manager.apply_patch(p_move_b)
    assert ok_mb is False
    assert err_mb is not None and "locked by peer 'client_A'" in err_mb

    # Client A moves node
    p_move_a = CanvasPatchOp(
        op_type=PatchOpType.NODE_MOVE,
        client_id="client_A",
        base_version=2,
        payload={"node_id": "node_1", "x": 250, "y": 350}
    )
    ok_ma, v_ma, _, _ = manager.apply_patch(p_move_a)
    assert ok_ma is True
    assert v_ma == 3
    assert manager.state_nodes["node_1"]["position"] == {"x": 250, "y": 350}

    # Release lock
    assert manager.release_lock("node_1", "client_A") is True

    # Now Client B can move
    ok_b_after, v_b, _, _ = manager.apply_patch(p_move_b)
    assert ok_b_after is True
    assert v_b == 4

    # History replay check
    patches_since = manager.get_patches_since(since_version=2)
    assert len(patches_since) == 2  # v3 and v4
