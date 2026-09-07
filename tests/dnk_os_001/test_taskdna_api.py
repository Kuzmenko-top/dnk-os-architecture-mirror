# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_001_test_taskdna_api"
# purpose: "Comprehensive Unit & Security tests for TaskDNA API and workspace isolation (DNK-OS-001)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import json
import base64
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def make_jwt(claims: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"sig").decode().rstrip("=")
    return f"{header}.{payload}.{signature}"


def test_list_tasks_missing_header_fails_closed():
    """Security Gate: Missing X-Workspace-ID must fail closed with 403."""
    response = client.get("/api/tasks")
    assert response.status_code == 403
    assert response.json()["error_type"] == "SecurityGateDenied"


def test_list_tasks_empty_header_fails_closed():
    """Security Gate: Empty X-Workspace-ID must fail closed with 403."""
    response = client.get("/api/tasks", headers={"X-Workspace-ID": "   "})
    assert response.status_code == 403
    assert response.json()["error_type"] == "SecurityGateDenied"


def test_list_tasks_malformed_workspace_id_fails_closed():
    """Security Gate: Malformed characters in X-Workspace-ID must fail closed with 403."""
    response = client.get("/api/tasks", headers={"X-Workspace-ID": "ws-invalid@#$%"})
    assert response.status_code == 403
    assert response.json()["error_type"] == "SecurityGateDenied"


def test_list_tasks_unauthorized_workspace_fails_closed():
    """Security Gate: Unknown / unauthorized workspace ID must fail closed with 403."""
    response = client.get("/api/tasks", headers={"X-Workspace-ID": "ws-hacker-tenant-999"})
    assert response.status_code == 403
    assert response.json()["error_type"] == "SecurityGateDenied"


def test_jwt_bearer_valid_token_allowed():
    """Security Gate: Valid JWT matching workspace allows request."""
    valid_jwt = make_jwt({"sub": "user_123", "workspace_id": "ws-alpha-001"})
    response = client.get(
        "/api/tasks",
        headers={
            "X-Workspace-ID": "ws-alpha-001",
            "Authorization": f"Bearer {valid_jwt}"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any(t["id"] == "DNK-OS-001" for t in data)


def test_jwt_bearer_malformed_header_fails_closed():
    """Security Gate: Malformed Authorization header without 'Bearer ' prefix fails closed with 403."""
    response = client.get(
        "/api/tasks",
        headers={
            "X-Workspace-ID": "ws-alpha-001",
            "Authorization": "Basic dXNlcjpwYXNz"
        }
    )
    assert response.status_code == 403
    assert response.json()["error_type"] == "SecurityGateDenied"


def test_jwt_bearer_malformed_token_fails_closed():
    """Security Gate: Malformed JWT token string fails closed with 403."""
    response = client.get(
        "/api/tasks",
        headers={
            "X-Workspace-ID": "ws-alpha-001",
            "Authorization": "Bearer not_a_valid_jwt_structure"
        }
    )
    assert response.status_code == 403
    assert response.json()["error_type"] == "SecurityGateDenied"


def test_jwt_bearer_workspace_mismatch_fails_closed():
    """Security Gate: JWT with claim for ws-shopify-001 trying to access ws-alpha-001 fails closed with 403."""
    mismatched_jwt = make_jwt({"sub": "user_123", "workspace_id": "ws-shopify-001"})
    response = client.get(
        "/api/tasks",
        headers={
            "X-Workspace-ID": "ws-alpha-001",
            "Authorization": f"Bearer {mismatched_jwt}"
        }
    )
    assert response.status_code == 403
    assert response.json()["error_type"] == "SecurityGateDenied"
    assert "claim" in response.json()["detail"].lower()


def test_cross_workspace_task_access_forbidden():
    """Tenant Isolation: ws-alpha-001 cannot access task DNK-SHOPIFY-011 which belongs to ws-shopify-001."""
    response = client.get(
        "/api/tasks/DNK-SHOPIFY-011",
        headers={"X-Workspace-ID": "ws-alpha-001"}
    )
    assert response.status_code == 403
    assert response.json()["error_type"] == "SecurityGateDenied"
    assert "Cross-workspace task access forbidden" in response.json()["detail"]


def test_cross_workspace_timeline_access_forbidden():
    """Tenant Isolation: Timeline access for task of another workspace is blocked with 403."""
    response = client.get(
        "/api/tasks/DNK-SHOPIFY-011/timeline",
        headers={"X-Workspace-ID": "ws-alpha-001"}
    )
    assert response.status_code == 403
    assert response.json()["error_type"] == "SecurityGateDenied"


def test_cross_workspace_graph_access_forbidden():
    """Tenant Isolation: Graph access for task of another workspace is blocked with 403."""
    response = client.get(
        "/api/tasks/DNK-SHOPIFY-011/graph",
        headers={"X-Workspace-ID": "ws-alpha-001"}
    )
    assert response.status_code == 403
    assert response.json()["error_type"] == "SecurityGateDenied"


def test_task_not_found_returns_404():
    """Unknown task ID returns 404."""
    response = client.get(
        "/api/tasks/NON-EXISTENT-TASK-999",
        headers={"X-Workspace-ID": "ws-alpha-001"}
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_invalid_status_filter_returns_400():
    """Invalid status query param returns 400."""
    response = client.get(
        "/api/tasks?status=HACKED_STATUS",
        headers={"X-Workspace-ID": "ws-alpha-001"}
    )
    assert response.status_code == 400
    assert "Invalid status filter" in response.json()["detail"]


def test_valid_status_filter_works():
    """Filtering by COMPLETED status returns only completed tasks."""
    response = client.get(
        "/api/tasks?status=COMPLETED",
        headers={"X-Workspace-ID": "ws-shopify-001"}
    )
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) > 0
    for t in tasks:
        assert t["status"] == "COMPLETED"


def test_get_task_detail_valid():
    """Fetch task detail for valid task in matching workspace."""
    response = client.get(
        "/api/tasks/DNK-OS-001",
        headers={"X-Workspace-ID": "ws-alpha-001"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "DNK-OS-001"
    assert data["owner"] == "Maxim (Lead)"
    assert data["supervisor"]["name"] == "Antigravity"
    assert data["worker"]["name"] == "Gerych"
    assert len(data["validation_gates"]) == 4


def test_get_task_timeline_valid():
    """Fetch timeline for valid task."""
    response = client.get(
        "/api/tasks/DNK-OS-001/timeline",
        headers={"X-Workspace-ID": "ws-alpha-001"}
    )
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 5
    assert events[0]["event_type"] == "TASK_CREATED"


def test_get_task_graph_valid():
    """Fetch canvas graph structure."""
    response = client.get(
        "/api/tasks/DNK-OS-001/graph",
        headers={"X-Workspace-ID": "ws-alpha-001"}
    )
    assert response.status_code == 200
    graph = response.json()
    assert graph["task_id"] == "DNK-OS-001"
    assert len(graph["nodes"]) > 0
    assert len(graph["edges"]) > 0
    node_types = {n["type"] for n in graph["nodes"]}
    assert "taskNode" in node_types
    assert "agentNode" in node_types
    assert "gateNode" in node_types
    assert "prNode" in node_types


def test_get_workspace_valid():
    """Fetch workspace by ID."""
    response = client.get(
        "/api/workspaces/ws-alpha-001",
        headers={"X-Workspace-ID": "ws-alpha-001"}
    )
    assert response.status_code == 200
    assert response.json()["id"] == "ws-alpha-001"
    assert response.json()["name"] == "DNK OS Core Delivery"


def test_get_workspace_unknown_returns_404():
    """Unknown workspace ID returns 404 or 403."""
    response = client.get(
        "/api/workspaces/ws-unknown",
        headers={"X-Workspace-ID": "ws-alpha-001"}
    )
    assert response.status_code in (403, 404)
