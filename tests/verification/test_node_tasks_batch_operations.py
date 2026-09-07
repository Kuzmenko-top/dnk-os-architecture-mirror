# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_node_tasks_batch_operations.py"
# purpose: "Integration tests for Slice 20.4 Node Tasks Batch Operations (batch stage, batch delete, batch execute)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & gerych_auditor"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_batch_stage_transition_and_execution():
    # 1. Create two test nodes
    node_1 = {
        "id": "test-batch-node-alpha",
        "title": "Batch Test Node Alpha",
        "node_type": "task",
        "stage": "ideation",
        "assigned_agent": "dnk_dev_fullstack",
        "priority": "medium",
        "tags": ["test", "batch"]
    }
    node_2 = {
        "id": "test-batch-node-beta",
        "title": "Batch Test Node Beta",
        "node_type": "task",
        "stage": "ideation",
        "assigned_agent": "gerych_builder",
        "priority": "high",
        "tags": ["test", "batch"]
    }

    res1 = client.post("/api/v3/node_tasks/node", json=node_1)
    assert res1.status_code == 200, res1.text
    res2 = client.post("/api/v3/node_tasks/node", json=node_2)
    assert res2.status_code == 200, res2.text

    # 2. Batch stage transition: ideation -> ready
    batch_trans_res = client.post(
        "/api/v3/node_tasks/batch_stage_transition",
        json={
            "node_ids": ["test-batch-node-alpha", "test-batch-node-beta"],
            "target_stage": "ready",
            "force": False
        }
    )
    assert batch_trans_res.status_code == 200, batch_trans_res.text
    data = batch_trans_res.json()
    assert data["status"] == "success"
    assert "test-batch-node-alpha" in data["updated_ids"]
    assert "test-batch-node-beta" in data["updated_ids"]

    # 3. Batch execute: run batch execution with auto_complete=True
    batch_exec_res = client.post(
        "/api/v3/node_tasks/batch_execute",
        json={
            "node_ids": ["test-batch-node-alpha", "test-batch-node-beta"],
            "agent_override": "gerych_auditor",
            "auto_complete": True
        }
    )
    assert batch_exec_res.status_code == 200, batch_exec_res.text
    exec_data = batch_exec_res.json()
    assert exec_data["status"] == "success"
    assert "test-batch-node-alpha" in exec_data["executed_ids"]
    assert "test-batch-node-beta" in exec_data["executed_ids"]

    # Verify nodes in graph are completed
    graph_res = client.get("/api/v3/node_tasks/graph")
    assert graph_res.status_code == 200
    graph_nodes = graph_res.json()["graph"]["nodes"]
    assert graph_nodes["test-batch-node-alpha"]["stage"] == "completed"
    assert graph_nodes["test-batch-node-beta"]["stage"] == "completed"

    # 4. Batch delete
    batch_del_res = client.post(
        "/api/v3/node_tasks/batch_delete",
        json={
            "node_ids": ["test-batch-node-alpha", "test-batch-node-beta"]
        }
    )
    assert batch_del_res.status_code == 200, batch_del_res.text
    del_data = batch_del_res.json()
    assert del_data["status"] == "success"
    assert "test-batch-node-alpha" in del_data["deleted_ids"]
    assert "test-batch-node-beta" in del_data["deleted_ids"]

    # Verify nodes are gone
    graph_res_after = client.get("/api/v3/node_tasks/graph")
    after_nodes = graph_res_after.json()["graph"]["nodes"]
    assert "test-batch-node-alpha" not in after_nodes
    assert "test-batch-node-beta" not in after_nodes


def test_batch_delete_removes_incident_edges():
    # Create two nodes and an edge between them
    n1 = {
        "id": "test-edge-batch-src",
        "title": "Batch Edge Source",
        "node_type": "task",
        "stage": "ready",
    }
    n2 = {
        "id": "test-edge-batch-tgt",
        "title": "Batch Edge Target",
        "node_type": "task",
        "stage": "ready",
    }
    client.post("/api/v3/node_tasks/node", json=n1)
    client.post("/api/v3/node_tasks/node", json=n2)

    edge_payload = {
        "source": "test-edge-batch-src",
        "target": "test-edge-batch-tgt",
        "relation": "depends_on"
    }
    edge_res = client.post("/api/v3/node_tasks/edge", json=edge_payload)
    assert edge_res.status_code == 200

    # Batch delete one of the nodes
    del_res = client.post(
        "/api/v3/node_tasks/batch_delete",
        json={"node_ids": ["test-edge-batch-src"]}
    )
    assert del_res.status_code == 200

    # Verify edge is gone
    graph_res = client.get("/api/v3/node_tasks/graph")
    edges = graph_res.json()["graph"]["edges"]
    assert not any(e["source"] == "test-edge-batch-src" or e["target"] == "test-edge-batch-src" for e in edges)

    # Cleanup remaining node
    client.post("/api/v3/node_tasks/batch_delete", json={"node_ids": ["test-edge-batch-tgt"]})
