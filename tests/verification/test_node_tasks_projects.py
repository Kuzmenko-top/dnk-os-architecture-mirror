# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_node_tasks_projects.py"
# purpose: "Verification tests for Multi-Tenant Projects API and project-filtered Node Tasks DAG graph"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_default_projects_list():
    """Verify default projects are returned with task counts."""
    res = client.get("/api/v3/node_tasks/projects")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "projects" in data
    assert data["total_projects"] >= 3

    project_ids = [p["id"] for p in data["projects"]]
    assert "dnk_core" in project_ids
    assert "m_craft" in project_ids
    assert "brand_alpha" in project_ids

    # Validate schema of project objects
    for p in data["projects"]:
        assert "id" in p
        assert "name" in p
        assert "slug" in p
        assert "color" in p
        assert "icon" in p
        assert "is_active" in p
        assert "created_at" in p
        assert "tasks_count" in p


def test_create_project():
    """Verify creating a new project partition via POST /projects."""
    new_project_payload = {
        "id": "test_ecom_suite",
        "name": "E-Commerce Suite",
        "slug": "ecom-suite",
        "description": "Custom Multi-Tenant E-Commerce Workspace",
        "color": "#ec4899",
        "icon": "shopping-bag",
        "is_active": True,
    }
    create_res = client.post("/api/v3/node_tasks/projects", json=new_project_payload)
    assert create_res.status_code == 200
    res_data = create_res.json()
    assert res_data["status"] == "success"
    assert res_data["project"]["id"] == "test_ecom_suite"
    assert res_data["project"]["name"] == "E-Commerce Suite"

    # Verify project appears in GET /projects
    list_res = client.get("/api/v3/node_tasks/projects")
    assert list_res.status_code == 200
    projects = list_res.json()["projects"]
    ecom_proj = next((p for p in projects if p["id"] == "test_ecom_suite"), None)
    assert ecom_proj is not None
    assert ecom_proj["color"] == "#ec4899"


def test_project_graph_isolation_and_edges():
    """
    Verify:
    1. Creating nodes assigned to a specific project.
    2. Creating edge between nodes in that project.
    3. Filtering graph by project_id isolates nodes and edges.
    4. Nodes from other projects do not leak into the filtered graph.
    """
    proj_id = "test_ecom_suite"
    node1_id = "test-ecom-node-alpha"
    node2_id = "test-ecom-node-beta"

    try:
        # Create Node 1 in test_ecom_suite
        res1 = client.post(
            "/api/v3/node_tasks/node",
            json={
                "id": node1_id,
                "title": "Ecom Catalog Ingestion",
                "node_type": "task",
                "stage": "ideation",
                "project_id": proj_id,
                "priority": "P1_High",
            },
        )
        assert res1.status_code == 200
        assert res1.json()["node"]["project_id"] == proj_id

        # Create Node 2 in test_ecom_suite
        res2 = client.post(
            "/api/v3/node_tasks/node",
            json={
                "id": node2_id,
                "title": "Ecom Checkout Customizer",
                "node_type": "task",
                "stage": "ideation",
                "project_id": proj_id,
                "priority": "P2_Medium",
            },
        )
        assert res2.status_code == 200
        assert res2.json()["node"]["project_id"] == proj_id

        # Create Edge between Node 1 and Node 2
        edge_res = client.post(
            "/api/v3/node_tasks/edge",
            json={
                "source": node1_id,
                "target": node2_id,
                "relation": "blocks",
            },
        )
        assert edge_res.status_code == 200

        # Query graph filtered by test_ecom_suite
        proj_graph_res = client.get(f"/api/v3/node_tasks/graph?project_id={proj_id}")
        assert proj_graph_res.status_code == 200
        proj_graph_data = proj_graph_res.json()
        assert proj_graph_data["status"] == "success"
        assert proj_graph_data["project_id"] == proj_id

        nodes = proj_graph_data["graph"]["nodes"]
        edges = proj_graph_data["graph"]["edges"]

        # Only nodes of test_ecom_suite should be present
        assert node1_id in nodes
        assert node2_id in nodes
        assert len(nodes) == 2

        # Verify default dnk_core nodes are NOT present in this filtered graph
        assert "task-occ-merge" not in nodes
        assert "task-node-system" not in nodes

        # Verify edge between node1 and node2 is present
        matching_edges = [
            e for e in edges if e["source"] == node1_id and e["target"] == node2_id
        ]
        assert len(matching_edges) == 1

        # Query graph filtered by dnk_core
        core_graph_res = client.get("/api/v3/node_tasks/graph?project_id=dnk_core")
        assert core_graph_res.status_code == 200
        core_nodes = core_graph_res.json()["graph"]["nodes"]

        # Ensure test_ecom_suite nodes are NOT present in dnk_core graph
        assert node1_id not in core_nodes
        assert node2_id not in core_nodes

        # Verify task count in /projects endpoint
        projects_res = client.get("/api/v3/node_tasks/projects")
        assert projects_res.status_code == 200
        proj_item = next(
            (p for p in projects_res.json()["projects"] if p["id"] == proj_id), None
        )
        assert proj_item is not None
        assert proj_item["tasks_count"] == 2

    finally:
        # Cleanup nodes
        client.delete(f"/api/v3/node_tasks/node/{node1_id}")
        client.delete(f"/api/v3/node_tasks/node/{node2_id}")
