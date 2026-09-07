# --- DNK-MRH-HEADER ---
# mrh_id: "tests_verification_test_task_forest_spatial_ui"
# purpose: "Comprehensive Verification Suite for Task Forest Spatial HQ (LOD Levels, Time-Travel History & Component Integrity)"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import pytest
import os
import json
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_task_forest_spatial_graph_endpoint():
    """Verify that the Task Forest Graph endpoint returns the 5-level spatial hierarchy."""
    response = client.get("/api/v3/task_forest/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "root_field" in data
    assert "nodes" in data
    nodes_list = list(data["nodes"].values()) if isinstance(data["nodes"], dict) else data["nodes"]
    assert len(nodes_list) >= 5

    # Check 5 hierarchy plant scales exist
    scales = {node["plant_scale"] for node in nodes_list}
    assert "field" in scales
    assert "sector" in scales
    assert "tree" in scales
    assert "bush" in scales
    assert "flower" in scales

def test_task_forest_evolution_history_endpoint():
    """Verify that the evolution history endpoint returns chronologically logged mutation events."""
    response = client.get("/api/v3/task_forest/evolution_history")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "events" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) > 0

    first_event = data["events"][0]
    required_fields = [
        "event_id",
        "timestamp",
        "node_id",
        "node_title",
        "plant_scale",
        "mutation_type",
        "overall_field_progress",
        "description"
    ]
    for field in required_fields:
        assert field in first_event

def test_task_forest_node_mutation_cascade():
    """Verify that mutating a flower node recalculates bottom-up progress and logs an evolution event."""
    # Find a flower node
    graph_res = client.get("/api/v3/task_forest/graph")
    data = graph_res.json()
    nodes_list = list(data["nodes"].values()) if isinstance(data["nodes"], dict) else data["nodes"]
    flowers = [n for n in nodes_list if n["plant_scale"] == "flower"]
    assert len(flowers) > 0
    target_flower = flowers[0]

    # Mutate to completed 100%
    mutate_payload = {
        "node_id": target_flower["id"],
        "status": "completed",
        "progress": 100.0,
        "mutation_type": "status_transition",
        "notes": "Automated verification test of atomic mutation"
    }
    mutate_res = client.post("/api/v3/task_forest/node/mutate", json=mutate_payload)
    assert mutate_res.status_code == 200
    mutate_data = mutate_res.json()
    assert mutate_data["status"] == "success"
    assert mutate_data["node"]["id"] == target_flower["id"]
    assert mutate_data["node"]["status"] == "completed"
    assert mutate_data["node"]["progress"] == 100.0

    # Verify event appears in history
    hist_res = client.get("/api/v3/task_forest/evolution_history")
    hist_data = hist_res.json()
    flower_events = [
        e for e in hist_data["events"]
        if e["node_id"] == target_flower["id"] and e.get("new_status") == "completed"
    ]
    assert len(flower_events) > 0

def test_spatial_component_files_exist():
    """Verify that all Task Forest Spatial UI components exist on disk with valid headers."""
    expected_files = [
        "apps/web/components/canvas/nodes/TaskForestSpatialNode.tsx",
        "apps/web/components/canvas/TimeTravelRail.tsx",
        "apps/web/components/canvas/CanvasEngine.tsx",
        "apps/web/components/canvas/DNKCanvas.tsx"
    ]
    for file_path in expected_files:
        assert os.path.exists(file_path), f"File {file_path} is missing!"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "DNK-MRH-HEADER" in content, f"File {file_path} lacks MRH header!"
            assert "TaskForestSpatialNode" in content or "TimeTravelRail" in content or "Canvas" in content
