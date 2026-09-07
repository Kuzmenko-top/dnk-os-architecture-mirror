# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_occ_merge.py"
# purpose: "Unit & Integration Tests for OCC 3-Way Graph Mutation Resolver"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["task-occ-merge", "task-node-system"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "Antigravity (Mentor) & DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from core.occ_merge import (
    OCCConcurrencyEngine,
    OCCGraphMergeResolver,
    OCCMergeResult,
    PositionConflictStrategy,
    ConflictType,
)
from apps.api.routers.node_tasks_router import router as node_tasks_router


@pytest.fixture
def base_graph():
    return {
        "version": "1.0.0",
        "nodes": {
            "node-1": {
                "id": "node-1",
                "title": "Base Node 1",
                "description": "Base description",
                "position": {"x": 100.0, "y": 100.0},
                "tags": ["core", "v1"],
                "status": "draft",
                "progress": 0.0,
            },
            "node-2": {
                "id": "node-2",
                "title": "Base Node 2",
                "description": "Node 2 description",
                "position": {"x": 300.0, "y": 100.0},
                "tags": ["feature"],
                "status": "draft",
                "progress": 0.0,
            },
        },
        "edges": [
            {
                "id": "edge-1-2",
                "source": "node-1",
                "target": "node-2",
                "relation": "depends_on",
            }
        ],
    }


def test_clean_3way_merge_concurrent_node_additions(base_graph):
    """Test non-conflicting concurrent additions: Mine adds node-3, Theirs adds node-4."""
    mine = {
        "nodes": dict(base_graph["nodes"]),
        "edges": list(base_graph["edges"]),
    }
    mine["nodes"]["node-3"] = {
        "id": "node-3",
        "title": "Mine Node 3",
        "position": {"x": 100.0, "y": 300.0},
        "tags": ["mine"],
    }
    mine["edges"].append({
        "id": "edge-1-3",
        "source": "node-1",
        "target": "node-3",
        "relation": "depends_on",
    })

    theirs = {
        "nodes": dict(base_graph["nodes"]),
        "edges": list(base_graph["edges"]),
    }
    theirs["nodes"]["node-4"] = {
        "id": "node-4",
        "title": "Theirs Node 4",
        "position": {"x": 300.0, "y": 300.0},
        "tags": ["theirs"],
    }
    theirs["edges"].append({
        "id": "edge-2-4",
        "source": "node-2",
        "target": "node-4",
        "relation": "depends_on",
    })

    result = OCCConcurrencyEngine.merge_graph_state(
        base_state=base_graph,
        current_state=theirs,
        incoming_state=mine,
    )

    assert result.status == "success"
    assert not result.has_unresolved_conflicts
    merged_nodes = result.merged_graph["nodes"]
    assert "node-1" in merged_nodes
    assert "node-2" in merged_nodes
    assert "node-3" in merged_nodes
    assert "node-4" in merged_nodes

    merged_edge_ids = {e["id"] for e in result.merged_graph["edges"]}
    assert "edge-1-2" in merged_edge_ids
    assert "edge-1-3" in merged_edge_ids
    assert "edge-2-4" in merged_edge_ids


def test_edge_deletion_by_one_party(base_graph):
    """Test deletion of edge by Mine while Theirs kept it unchanged."""
    mine = {
        "nodes": dict(base_graph["nodes"]),
        "edges": [],  # Mine deleted edge-1-2
    }
    theirs = {
        "nodes": dict(base_graph["nodes"]),
        "edges": list(base_graph["edges"]),  # Unchanged
    }

    result = OCCConcurrencyEngine.merge_graph_state(
        base_state=base_graph,
        current_state=theirs,
        incoming_state=mine,
    )

    assert result.status == "success"
    assert len(result.merged_graph["edges"]) == 0
    assert any("edge:deleted:edge-1-2" in m for m in result.applied_mutations)


def test_position_conflict_vector_shift_strategy(base_graph):
    """
    Test position conflict: both Mine and Theirs moved node-1 to different coordinates.
    Default strategy 'shift' applies a deterministic +20px vector shift to Mine.
    """
    mine = {
        "nodes": {
            "node-1": {
                **base_graph["nodes"]["node-1"],
                "position": {"x": 150.0, "y": 150.0},
            },
            "node-2": base_graph["nodes"]["node-2"],
        },
        "edges": base_graph["edges"],
    }
    theirs = {
        "nodes": {
            "node-1": {
                **base_graph["nodes"]["node-1"],
                "position": {"x": 200.0, "y": 200.0},
            },
            "node-2": base_graph["nodes"]["node-2"],
        },
        "edges": base_graph["edges"],
    }

    result = OCCConcurrencyEngine.merge_graph_state(
        base_state=base_graph,
        current_state=theirs,
        incoming_state=mine,
        position_strategy=PositionConflictStrategy.SHIFT,
    )

    assert result.status == "success"
    # Position shifted: 150 + 20 = 170
    merged_pos = result.merged_graph["nodes"]["node-1"]["position"]
    assert merged_pos["x"] == 170.0
    assert merged_pos["y"] == 170.0
    assert any(c.conflict_type == ConflictType.POSITION_CONFLICT for c in result.conflicts)


def test_position_conflict_last_write_wins(base_graph):
    """Test position conflict resolved with last-write-wins (Mine wins)."""
    mine = {
        "nodes": {
            "node-1": {
                **base_graph["nodes"]["node-1"],
                "position": {"x": 180.0, "y": 180.0},
            },
            "node-2": base_graph["nodes"]["node-2"],
        },
        "edges": base_graph["edges"],
    }
    theirs = {
        "nodes": {
            "node-1": {
                **base_graph["nodes"]["node-1"],
                "position": {"x": 220.0, "y": 220.0},
            },
            "node-2": base_graph["nodes"]["node-2"],
        },
        "edges": base_graph["edges"],
    }

    result = OCCConcurrencyEngine.merge_graph_state(
        base_state=base_graph,
        current_state=theirs,
        incoming_state=mine,
        position_strategy=PositionConflictStrategy.LAST_WRITE_WINS,
    )

    assert result.status == "success"
    merged_pos = result.merged_graph["nodes"]["node-1"]["position"]
    assert merged_pos["x"] == 180.0
    assert merged_pos["y"] == 180.0


def test_node_data_conflicts_tags_union_and_description_concat(base_graph):
    """
    Test Node Data Conflicts:
    - Tags: Set union across both sides.
    - Description: Concatenation when both sides edited differently.
    """
    mine = {
        "nodes": {
            "node-1": {
                **base_graph["nodes"]["node-1"],
                "tags": ["core", "tag-mine", "shared"],
                "description": "Mine updated description",
            },
            "node-2": base_graph["nodes"]["node-2"],
        },
        "edges": base_graph["edges"],
    }
    theirs = {
        "nodes": {
            "node-1": {
                **base_graph["nodes"]["node-1"],
                "tags": ["core", "tag-theirs", "shared"],
                "description": "Theirs updated description",
            },
            "node-2": base_graph["nodes"]["node-2"],
        },
        "edges": base_graph["edges"],
    }

    result = OCCConcurrencyEngine.merge_graph_state(
        base_state=base_graph,
        current_state=theirs,
        incoming_state=mine,
    )

    assert result.status == "success"
    merged_node = result.merged_graph["nodes"]["node-1"]

    # Tags union
    tags = merged_node["tags"]
    assert "core" in tags
    assert "tag-mine" in tags
    assert "tag-theirs" in tags
    assert "shared" in tags

    # Description concatenation
    desc = merged_node["description"]
    assert "Theirs updated description" in desc
    assert "Mine updated description" in desc


def test_edge_cycle_conflict_detection():
    """
    Test cycle detection:
    Base has A -> B.
    Mine adds B -> C.
    Theirs adds C -> A.
    Resulting candidate graph has cycle A -> B -> C -> A.
    Must flag conflict and mark has_unresolved_conflicts = True.
    """
    base = {
        "nodes": {
            "A": {"id": "A", "title": "Node A", "position": {"x": 0, "y": 0}},
            "B": {"id": "B", "title": "Node B", "position": {"x": 100, "y": 0}},
            "C": {"id": "C", "title": "Node C", "position": {"x": 200, "y": 0}},
        },
        "edges": [
            {"id": "e_ab", "source": "A", "target": "B", "relation": "depends_on"}
        ],
    }

    mine = {
        "nodes": base["nodes"],
        "edges": [
            {"id": "e_ab", "source": "A", "target": "B", "relation": "depends_on"},
            {"id": "e_bc", "source": "B", "target": "C", "relation": "depends_on"},
        ],
    }

    theirs = {
        "nodes": base["nodes"],
        "edges": [
            {"id": "e_ab", "source": "A", "target": "B", "relation": "depends_on"},
            {"id": "e_ca", "source": "C", "target": "A", "relation": "depends_on"},
        ],
    }

    result = OCCConcurrencyEngine.merge_graph_state(
        base_state=base,
        current_state=theirs,
        incoming_state=mine,
    )

    assert result.status == "conflict"
    assert result.has_unresolved_conflicts
    assert any(c.conflict_type == ConflictType.CYCLE_DETECTED for c in result.conflicts)


def test_api_merge_endpoint_200_and_409_cycle_conflict():
    """Test FastAPI /api/v3/node_tasks/merge endpoint for 200 OK and 409 Conflict."""
    app = FastAPI()
    app.include_router(node_tasks_router)
    client = TestClient(app)

    base = {
        "version": "1.0.0",
        "nodes": {
            "A": {"id": "A", "title": "A", "position": {"x": 0, "y": 0}, "tags": ["base"]},
            "B": {"id": "B", "title": "B", "position": {"x": 100, "y": 0}, "tags": ["base"]},
        },
        "edges": [
            {"id": "e_ab", "source": "A", "target": "B", "relation": "depends_on"}
        ],
    }

    # Successful merge
    mine_ok = {
        "nodes": {
            **base["nodes"],
            "C": {"id": "C", "title": "C", "position": {"x": 200, "y": 0}, "tags": ["new"]},
        },
        "edges": [
            {"id": "e_ab", "source": "A", "target": "B", "relation": "depends_on"},
            {"id": "e_bc", "source": "B", "target": "C", "relation": "depends_on"},
        ],
    }

    resp = client.post(
        "/api/v3/node_tasks/merge",
        json={
            "base_state": base,
            "incoming_state": mine_ok,
            "current_state": base,
            "save_to_persistence": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "C" in data["merged_graph"]["nodes"]

    # Cycle conflict merge -> HTTP 409
    theirs_cycle = {
        "nodes": {
            **base["nodes"],
            "C": {"id": "C", "title": "C", "position": {"x": 200, "y": 0}, "tags": []},
        },
        "edges": [
            {"id": "e_ab", "source": "A", "target": "B", "relation": "depends_on"},
            {"id": "e_ca", "source": "C", "target": "A", "relation": "depends_on"},
        ],
    }

    resp_conflict = client.post(
        "/api/v3/node_tasks/merge",
        json={
            "base_state": base,
            "incoming_state": mine_ok,
            "current_state": theirs_cycle,
            "save_to_persistence": False,
        },
    )
    assert resp_conflict.status_code == 409
    detail = resp_conflict.json()["detail"]
    assert detail["error"] == "OCC_MERGE_CONFLICT"
    assert any(c["conflict_type"] == "CYCLE_DETECTED" for c in detail["conflicts"])
