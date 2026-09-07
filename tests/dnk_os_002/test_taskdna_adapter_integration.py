# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_002_test_taskdna_adapter_integration"
# purpose: "Integration tests for TaskDNA API with GitHub Read-Only Adapter (DNK-OS-002)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import json
import base64
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from apps.api.main import app

client = TestClient(app)

def make_jwt(claims: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    signature = base64.urlsafe_b64encode(b"sig").decode().rstrip("=")
    return f"{header}.{payload}.{signature}"

VALID_WS_HEADER = {
    "X-Workspace-ID": "ws-alpha-001",
    "Authorization": f"Bearer {make_jwt({'workspace_id': 'ws-alpha-001', 'sub': 'user-1'})}"
}


def test_task_detail_returns_data_source_metadata():
    response = client.get("/api/tasks/DNK-OS-001", headers=VALID_WS_HEADER)
    assert response.status_code == 200
    data = response.json()
    assert "data_source" in data
    assert data["data_source"] in ("live", "cache", "fixture")
    assert "stale" in data
    assert isinstance(data["stale"], bool)


def test_task_detail_reflects_live_adapter_data():
    from apps.api.routers.taskdna import github_adapter
    github_adapter._cache.clear()

    fake_pr = {
        "number": 13,
        "title": "Mock Live Title for PR #13",
        "state": "closed",
        "merged": True,
        "merged_at": "2026-08-23T12:00:00Z",
        "head": {"sha": "6e87df1fea33b02517d9f39cbf6059b55b302760"},
        "base": {"ref": "main"},
        "mergeable": True
    }
    with patch.object(github_adapter._transport, "get", return_value=(fake_pr, 200, None)):
        response = client.get("/api/tasks/DNK-OS-001", headers=VALID_WS_HEADER)
        assert response.status_code == 200
        data = response.json()
        assert data["data_source"] in ("live", "cache")
        assert data["pull_request"]["title"] == "Mock Live Title for PR #13"
        assert data["pull_request"]["state"] == "MERGED"
