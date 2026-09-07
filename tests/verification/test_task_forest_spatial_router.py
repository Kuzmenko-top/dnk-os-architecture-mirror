# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_task_forest_spatial_router.py"
# purpose: "Integration tests for Task Forest 5-Plant Scale Engine & Spatial Canvas router endpoints"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

@pytest.fixture
def client():
    # Use TestClient with the FastAPI application
    return TestClient(app)

def test_get_task_forest_graph(client):
    """
    Test the GET /api/v3/task_forest/graph endpoint.
    It should return the 5-plant taxonomy root field and full list of nodes.
    """
    response = client.get("/api/v3/task_forest/graph")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "success"
    assert "root_field" in data
    assert "nodes" in data
    assert "overall_progress" in data
    assert "scale_counts" in data
    
    root_field = data["root_field"]
    assert root_field["plant_scale"] == "field"
    assert root_field["title"] == "DNK_HUB Master HQ"
    assert root_field["progress"] == 88.0
    
    # Check 5 levels of taxonomy: field -> sector -> tree -> bush -> flower
    assert len(root_field["children"]) > 0
    sector = root_field["children"][0]
    assert sector["plant_scale"] == "sector"
    
    assert len(sector["children"]) > 0
    tree = sector["children"][0]
    assert tree["plant_scale"] == "tree"
    
    assert len(tree["children"]) > 0
    bush = tree["children"][0]
    assert bush["plant_scale"] == "bush"
    
    assert len(bush["children"]) > 0
    flower = bush["children"][0]
    assert flower["plant_scale"] == "flower"

def test_node_mutation_and_bottom_up_rollup(client):
    """
    Test node status mutation and automatic bottom-up rollup recalculation.
    """
    # 1. Reset/Get baseline graph state
    response_baseline = client.get("/api/v3/task_forest/graph")
    assert response_baseline.status_code == 200
    baseline_data = response_baseline.json()
    assert baseline_data["overall_progress"] == 88.0
    
    # 2. Mutate flw-008 to completed
    mutate_response = client.post("/api/v3/task_forest/node/mutate", json={
        "node_id": "flw-008",
        "status": "completed",
        "progress": 100.0
    })
    assert mutate_response.status_code == 200
    mutated_data = mutate_response.json()
    assert mutated_data["status"] == "success"
    assert mutated_data["node"]["id"] == "flw-008"
    assert mutated_data["node"]["status"] == "completed"
    assert mutated_data["node"]["progress"] == 100.0
    
    # Verify bottom-up progress updated in the field
    assert mutated_data["overall_field_progress"] == 93.0
    
    # 3. Check graph again to confirm persistent change and rollup
    response_updated = client.get("/api/v3/task_forest/graph")
    assert response_updated.status_code == 200
    updated_data = response_updated.json()
    assert updated_data["overall_progress"] == 93.0
    assert updated_data["root_field"]["progress"] == 93.0
    
    # Verify that the parent bush and tree also recalculated
    nodes = updated_data["nodes"]
    assert nodes["bush-004"]["progress"] == 65.0  # (100 + 100 + 0 + 60) / 4 = 65%
    assert nodes["tree-004"]["progress"] == 65.0  # only 1 bush under tree-004, so it should match

def test_add_new_node(client):
    """
    Test creating a new flower node and verify parent rollup.
    """
    # Create a new flower under bush-004 (Task Forest Spatial Drawer UI)
    response = client.post("/api/v3/task_forest/node/mutate", json={
        "parent_id": "bush-004",
        "title": "Adversarial PR Verification Gate",
        "plant_scale": "flower",
        "status": "completed",
        "progress": 100.0,
        "assigned_agent": "gerych_auditor"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["mutation_type"] == "create"
    
    new_node = data["node"]
    assert new_node["id"].startswith("flw-")
    assert new_node["title"] == "Adversarial PR Verification Gate"
    assert new_node["parent_id"] == "bush-004"
    assert new_node["status"] == "completed"
    assert new_node["progress"] == 100.0

def test_evolution_history(client):
    """
    Test GET /api/v3/task_forest/evolution_history.
    """
    response = client.get("/api/v3/task_forest/evolution_history")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data
    assert len(data["events"]) > 0
    
    # Verify event structure
    event = data["events"][-1]
    assert "event_id" in event
    assert "timestamp" in event
    assert "node_id" in event
    assert "mutation_type" in event
