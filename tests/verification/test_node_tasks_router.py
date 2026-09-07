# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_node_tasks_router.py"
# purpose: "Integration tests for Node Tasks & Ideas DAG System router endpoints"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.2"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager
from services.dnk_node_tasks.seed_data import create_initial_dnk_node_task_graph

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolate_node_tasks_db(tmp_path):
    """Ensures router integration tests never touch live data/node_task_graph.json."""
    orig_instance = NodeTaskPersistenceManager._instance
    test_db = str(tmp_path / "node_task_graph.json")
    test_obsidian = str(tmp_path / "obsidian")
    test_projects = str(tmp_path / "projects.json")

    manager = NodeTaskPersistenceManager(
        data_file_path=test_db,
        obsidian_dir=test_obsidian,
        projects_file_path=test_projects,
    )
    manager.reset_to_baseline()
    NodeTaskPersistenceManager._instance = manager
    yield manager
    NodeTaskPersistenceManager._instance = orig_instance



def test_get_graph_and_stats():
    res = client.get("/api/v3/node_tasks/graph")
    assert res.status_code == 200
    data = res.json()
    assert "graph" in data
    assert "stats" in data
    assert "topological_order" in data
    assert data["stats"]["total_nodes"] >= 10
    assert len(data["graph"]["nodes"]) >= 10


def test_create_and_delete_node():
    node_payload = {
        "id": "test-temp-node-999",
        "title": "Temporary Test Node",
        "node_type": "task",
        "stage": "ready",
        "assigned_agent": "dnk_dev_fullstack",
        "priority": "P2_Medium",
        "tags": ["test", "temporary"]
    }
    create_res = client.post("/api/v3/node_tasks/node", json=node_payload)
    assert create_res.status_code == 200
    create_data = create_res.json()
    assert create_data["status"] == "success"
    assert create_data["node"]["id"] == "test-temp-node-999"

    # Delete the node
    del_res = client.delete("/api/v3/node_tasks/node/test-temp-node-999")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "success"


def test_stage_transition_gating():
    # task-occ-merge depends on task-node-system (which is in_progress, not completed)
    # attempting to move task-occ-merge to in_progress without force should fail with 400
    res = client.post(
        "/api/v3/node_tasks/stage_transition",
        json={
            "node_id": "task-occ-merge",
            "target_stage": "in_progress",
            "force": False
        }
    )
    assert res.status_code == 400
    assert "blocked" in res.json()["detail"].lower()

    # With force=True, it should proceed
    force_res = client.post(
        "/api/v3/node_tasks/stage_transition",
        json={
            "node_id": "task-occ-merge",
            "target_stage": "in_progress",
            "force": True
        }
    )
    assert force_res.status_code == 200
    force_data = force_res.json()
    assert force_data["node"]["stage"] == "in_progress"


def test_convert_idea_to_task():
    convert_res = client.post(
        "/api/v3/node_tasks/convert_idea",
        json={
            "idea_id": "idea-remotion",
            "new_node_type": "task",
            "assigned_agent": "dnk_video_ai_creator"
        }
    )
    assert convert_res.status_code == 200
    convert_data = convert_res.json()
    assert convert_data["status"] == "success"
    assert convert_data["spawned_task"]["node_type"] == "task"
    assert convert_data["spawned_task"]["stage"] == "architecture"


def test_execute_agent_simulation():
    res = client.post(
        "/api/v3/node_tasks/execute_agent",
        json={
            "node_id": "task-scones-l3",
            "task_instructions": "Verify L3 vector indexing"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["assigned_agent"] == "dnk_scones_memory"
    assert "stage" in data
    assert len(data.get("logs", [])) > 0


def test_execute_node_direct_and_logs():
    # Direct node execution endpoint
    res = client.post(
        "/api/v3/node_tasks/task-scones-l3/execute",
        json={
            "auto_complete": True,
            "task_instructions": "Complete L3 cache indexing with verification"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["stage"] == "completed"
    assert data["progress"] == 100.0

    # Retrieve logs
    logs_res = client.get("/api/v3/node_tasks/task-scones-l3/logs")
    assert logs_res.status_code == 200
    logs_data = logs_res.json()
    assert logs_data["status"] == "success"
    assert len(logs_data["logs"]) >= 2
    levels = [entry["level"] for entry in logs_data["logs"]]
    assert "INFO" in levels
    assert "SUCCESS" in levels


def test_sync_obsidian_and_reset():
    sync_res = client.post("/api/v3/node_tasks/sync_obsidian")
    assert sync_res.status_code == 200
    sync_data = sync_res.json()
    assert sync_data["synced_count"] > 0
    assert "obsidian_dir" in sync_data

    # Reset baseline
    reset_res = client.post("/api/v3/node_tasks/reset_baseline")
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["status"] == "success"


def test_chat_intake():
    res = client.post(
        "/api/v3/node_tasks/chat_intake",
        json={
            "prompt": "Ідея: реалізувати розумний відеоплеєр для TikTok та протестувати його терміново",
            "workspace_id": "ws-alpha-001"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["created_nodes"]) >= 1
    assert "reply" in data
    assert "Герич" in data["reply"]


def test_chat_intake_conversational_query_does_not_create_nodes():
    res = client.post(
        "/api/v3/node_tasks/chat_intake",
        json={
            "prompt": "Герич - чому така велика кількість нод з'явилася?",
            "workspace_id": "ws-alpha-001"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["created_nodes"]) == 0
    assert "Герич" in data["reply"]
    assert any(w in data["reply"].lower() for w in ["вузл", "нод", "задач", "граф"])


def test_chat_intake_greeting_does_not_create_nodes():
    res = client.post(
        "/api/v3/node_tasks/chat_intake",
        json={
            "prompt": "Привіт, як справи?",
            "workspace_id": "ws-alpha-001"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert len(data["created_nodes"]) == 0
    assert "Герич" in data["reply"]



def test_decompose_node():
    epic_id = "test-epic-to-decompose-01"
    create_res = client.post(
        "/api/v3/node_tasks/node",
        json={
            "id": epic_id,
            "title": "Відеогенератор Remotion для Shopify",
            "description": "Повна розробка та інтеграція відео-генератора",
            "node_type": "epic",
            "stage": "ready",
            "assigned_agent": "antigravity_mentor",
            "tags": ["video", "remotion", "shopify"],
            "priority": "high",
        }
    )
    assert create_res.status_code == 200

    decompose_res = client.post(
        f"/api/v3/node_tasks/{epic_id}/decompose",
        json={
            "instructions": "Створити високоякісну анімацію та перевірити регресії",
            "workspace_id": "ws-alpha-001"
        }
    )
    assert decompose_res.status_code == 200
    decompose_data = decompose_res.json()
    assert decompose_data["status"] == "success"
    assert len(decompose_data["created_nodes"]) == 3
    assert len(decompose_data["created_edges"]) >= 3
    assert "Герич" in decompose_data["message"]

    # Clean up created nodes
    client.delete(f"/api/v3/node_tasks/node/{epic_id}")
    for sub in decompose_data["created_nodes"]:
        client.delete(f"/api/v3/node_tasks/node/{sub['id']}")


def test_batch_update_positions():
    # Fetch current graph
    res = client.get("/api/v3/node_tasks/graph")
    assert res.status_code == 200
    nodes = res.json()["graph"]["nodes"]
    assert len(nodes) > 0

    first_node_id = list(nodes.keys())[0]
    payload = {
        "positions": {
            first_node_id: {"x": 555.0, "y": 777.0}
        }
    }

    batch_res = client.post("/api/v3/node_tasks/batch_positions", json=payload)
    assert batch_res.status_code == 200
    data = batch_res.json()
    assert data["status"] == "success"
    assert data["updated_count"] >= 1

    # Verify persisted in next fetch
    verify_res = client.get("/api/v3/node_tasks/graph")
    pos = verify_res.json()["graph"]["nodes"][first_node_id]["position"]
    assert pos["x"] == 555.0
    assert pos["y"] == 777.0


def test_create_and_delete_edge_with_cycle_detection():
    # 1. Create two temporary nodes
    node_a = {
        "id": "test-edge-node-a",
        "title": "Alpha Task",
        "node_type": "task",
        "stage": "ready",
        "assigned_agent": "dnk_dev_fullstack",
    }
    node_b = {
        "id": "test-edge-node-b",
        "title": "Beta Task",
        "node_type": "task",
        "stage": "ready",
        "assigned_agent": "dnk_dev_fullstack",
    }
    client.post("/api/v3/node_tasks/node", json=node_a)
    client.post("/api/v3/node_tasks/node", json=node_b)

    try:
        # 2. Create valid edge A -> B
        edge_payload = {
            "source": "test-edge-node-a",
            "target": "test-edge-node-b",
            "relation": "depends_on",
            "description": "Beta requires Alpha to be completed first",
        }
        res = client.post("/api/v3/node_tasks/edge", json=edge_payload)
        assert res.status_code == 200
        edge_data = res.json()
        assert edge_data["status"] == "success"
        edge_id = edge_data["edge"]["id"]
        assert edge_id == "edge-test-edge-node-a-to-test-edge-node-b"

        # 3. Attempt circular dependency B -> A
        cycle_payload = {
            "source": "test-edge-node-b",
            "target": "test-edge-node-a",
            "relation": "depends_on",
        }
        cycle_res = client.post("/api/v3/node_tasks/edge", json=cycle_payload)
        assert cycle_res.status_code == 400
        assert "Circular dependency detected" in cycle_res.json()["detail"]

        # 4. Delete the edge
        del_res = client.delete(f"/api/v3/node_tasks/edge/{edge_id}")
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "success"
        assert del_res.json()["deleted_edge_id"] == edge_id

        # 5. Verify deleting again returns 404
        del_again_res = client.delete(f"/api/v3/node_tasks/edge/{edge_id}")
        assert del_again_res.status_code == 404

    finally:
        # Cleanup nodes
        client.delete("/api/v3/node_tasks/node/test-edge-node-a")
        client.delete("/api/v3/node_tasks/node/test-edge-node-b")


def test_audit_node_task_session_endpoint():
    # 1. Non-existent node returns 404
    res_404 = client.post("/api/v3/node_tasks/non-existent-node-xyz/audit_session")
    assert res_404.status_code == 404

    # 2. Existing node triggers audit
    graph_res = client.get("/api/v3/node_tasks/graph")
    first_node_id = list(graph_res.json()["graph"]["nodes"].keys())[0]

    res = client.post(
        f"/api/v3/node_tasks/{first_node_id}/audit_session",
        json={"session_id": "non_existent_mock_session"}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["node_id"] == first_node_id
    # Either warning if no session in db or success with audit
    assert data["status"] in ("warning", "success")


def test_get_critical_path():
    res = client.get("/api/v3/node_tasks/critical_path")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "critical_path_node_ids" in data
    assert "critical_edge_ids" in data
    assert "total_duration_hours" in data
    assert "bottlenecks" in data
    assert "node_metrics" in data
    assert isinstance(data["critical_path_node_ids"], list)
    assert isinstance(data["bottlenecks"], list)
    assert isinstance(data["total_duration_hours"], (int, float))




