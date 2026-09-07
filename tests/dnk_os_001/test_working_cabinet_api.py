# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_001_test_working_cabinet_api"
# purpose: "Test working cabinet endpoints, fail-closed auth, zero network egress, and security invariants (DNK-VISUAL-OS-001)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import socket
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-Workspace-ID": "ws-alpha-001"}


def test_cabinet_health_endpoint():
    response = client.get("/api/cabinet/health", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "uptime_seconds" in data
    assert "active_agents" in data


def test_cabinet_tasks_endpoint():
    response = client.get("/api/cabinet/tasks", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["plant_scale"] in [
        "Project_Field", "Sector_Zone", "Epic_Tree", "Feature_Bush", "Task_Flower"
    ]


def test_cabinet_timeline_endpoint():
    response = client.get("/api/cabinet/timeline", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "timestamp" in data[0]
    assert "message" in data[0]


def test_cabinet_approvals_endpoint():
    response = client.get("/api/cabinet/approvals", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "preview_payload" in data[0]


def test_cabinet_plugins_endpoint():
    response = client.get("/api/cabinet/plugins", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["signature_verified"] is True


def test_cabinet_shopify_diff_endpoint():
    response = client.get("/api/cabinet/shopify/diff", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "theme_id" in data
    assert data["dry_run_passed"] is True
    assert isinstance(data["diff_entries"], list)


def test_cabinet_canvas_research_endpoint():
    response = client.get("/api/cabinet/canvas/research", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "topic" in data[0]


# ---------------------------------------------------------------------------
# Security & Fail-Closed Auth Tests
# ---------------------------------------------------------------------------

def test_cabinet_missing_workspace_header_fails_closed():
    response = client.get("/api/cabinet/tasks")
    assert response.status_code == 403
    assert "Missing or empty X-Workspace-ID header" in response.json().get("detail", "")


def test_cabinet_cross_workspace_unauthorized():
    response = client.get("/api/cabinet/tasks", headers={"X-Workspace-ID": "ws-unauthorized-999"})
    assert response.status_code == 403
    assert "not authorized" in response.json().get("detail", "")


def test_security_headers_present_on_response():
    response = client.get("/api/cabinet/health", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"


def test_protected_api_route_without_key_returns_401():
    # Route starting with /api/ not in excluded list requires API key
    response = client.get("/api/arbitrary_protected_route")
    assert response.status_code == 401
    assert "Unauthorized" in response.json().get("detail", "")


# ---------------------------------------------------------------------------
# Zero Network Egress Negative Verification
# ---------------------------------------------------------------------------

def test_cabinet_zero_network_egress_and_fixture_enforcement(monkeypatch):
    monkeypatch.setenv("FIXTURE_MODE", "true")
    network_call_count = 0

    def fail_on_socket(*args, **kwargs):
        nonlocal network_call_count
        network_call_count += 1
        raise RuntimeError("Forbidden outbound socket call detected during Cabinet/TaskDNA execution")

    monkeypatch.setattr(socket, "create_connection", fail_on_socket)
    monkeypatch.setattr(socket.socket, "connect", fail_on_socket)

    endpoints = [
        "/api/cabinet/health",
        "/api/cabinet/tasks",
        "/api/cabinet/timeline",
        "/api/cabinet/approvals",
        "/api/cabinet/plugins",
        "/api/cabinet/shopify/diff",
        "/api/cabinet/canvas/research",
        "/api/tasks/DNK-OS-001",
        "/api/tasks/DNK-OS-001/timeline",
        "/api/tasks/DNK-OS-001/graph",
    ]

    for ep in endpoints:
        res = client.get(ep, headers=AUTH_HEADERS)
        assert res.status_code in (200, 404), f"Endpoint {ep} failed with status {res.status_code}"

    assert network_call_count == 0, f"Expected 0 network calls, detected {network_call_count}"
