# --- DNK-MRH-HEADER ---
# mrh_id: "tests_canvas_test_canvas_v3_phase3"
# purpose: "Unit tests for Canvas V3 AI Node Weaver & History Time-Travel Engine (DNK-CANVAS-003 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.canvas_ai_node_weaver import CanvasAINodeWeaver
from apps.api.services.canvas_history_time_travel_engine import (
    CanvasHistoryTimeTravelEngine,
)


def test_ai_node_weaver_synthesis_general():
    weaver = CanvasAINodeWeaver(default_spacing=50.0)

    res = weaver.synthesize_subflow(
        canvas_id="canvas-test",
        prompt="fetch customer data, validate tier, apply discount, send email",
        auto_group=True,
    )

    assert res["canvas_id"] == "canvas-test"
    assert res["total_nodes_generated"] == 4
    assert res["total_edges_generated"] == 3
    assert res["group"] is not None
    assert len(res["group"]["node_ids"]) == 4

    # Check non-overlapping coordinates
    nodes = res["nodes"]
    for i in range(len(nodes) - 1):
        assert nodes[i + 1]["x"] > nodes[i]["x"]


def test_ai_node_weaver_with_context_nodes():
    weaver = CanvasAINodeWeaver()
    context = [{"id": "node-existing-1", "x": 100.0, "y": 100.0, "width": 150.0}]

    res = weaver.synthesize_subflow(
        canvas_id="canvas-test",
        prompt="Process checkout payment and trigger thank you",
        context_nodes=context,
    )

    assert res["total_nodes_generated"] == 4
    # First generated edge connects from existing context node
    assert res["edges"][0]["source_node_id"] == "node-existing-1"
    assert res["nodes"][0]["x"] > 250.0  # Placed to the right of context node


def test_time_travel_engine_snapshots_and_undo_redo():
    engine = CanvasHistoryTimeTravelEngine(canvas_id="canvas-tt")

    # State 1
    s1 = engine.record_snapshot(
        author_id="user-1",
        state_data={"nodes": [{"id": "n1"}], "edges": []},
        snapshot_tag="init",
    )
    assert s1["version_index"] == 1

    # State 2
    s2 = engine.record_snapshot(
        author_id="user-1",
        state_data={"nodes": [{"id": "n1"}, {"id": "n2"}], "edges": [{"id": "e1"}]},
        snapshot_tag="added n2",
    )
    assert s2["version_index"] == 2
    assert engine.current_cursor == 1

    # Undo to State 1
    restored1 = engine.undo()
    assert restored1 is not None
    assert len(restored1["nodes"]) == 1
    assert engine.current_cursor == 0

    # Undo beyond 0 returns None
    assert engine.undo() is None

    # Redo back to State 2
    restored2 = engine.redo()
    assert restored2 is not None
    assert len(restored2["nodes"]) == 2
    assert engine.current_cursor == 1

    # Redo beyond max returns None
    assert engine.redo() is None


def test_time_travel_branching_and_merging():
    engine = CanvasHistoryTimeTravelEngine(canvas_id="canvas-branch")

    # Base snapshot on main
    engine.record_snapshot(
        author_id="user-1",
        state_data={"nodes": [{"id": "n1"}], "edges": []},
        snapshot_tag="main-base",
    )

    # Create feature branch
    branch_res = engine.create_branch("feature-ai")
    assert branch_res["branch_name"] == "feature-ai"

    # Switch active branch and commit to feature-ai
    engine.active_branch = "feature-ai"
    engine.record_snapshot(
        author_id="user-ai",
        state_data={"nodes": [{"id": "n1"}, {"id": "n-ai-1"}], "edges": [{"id": "e-ai-1"}]},
        snapshot_tag="feature-work",
    )

    # Merge feature-ai into main with union strategy
    merge_res = engine.merge_branch(
        source_branch="feature-ai", target_branch="main", strategy="union"
    )
    assert merge_res["strategy"] == "union"
    assert merge_res["total_merged_nodes"] == 2
    assert merge_res["total_merged_edges"] == 1
