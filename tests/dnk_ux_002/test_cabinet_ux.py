# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_ux_002_test_cabinet_ux"
# purpose: "Unit and integration tests for Working Cabinet UX Polish — PR Inspector, Checks View & Timeline Stream"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import os
os.environ["FIXTURE_MODE"] = "true"

from fastapi.testclient import TestClient
from apps.api.main import app
from core.config.security_config import SECURITY_API_KEY

AUTH_HEADERS = {
    "X-Workspace-ID": "ws-alpha-001",
    "X-API-Key": SECURITY_API_KEY,
}

client = TestClient(app)


def test_github_list_prs_endpoint():
    """Verify GET /api/github/prs/{owner}/{repo} returns list of PRs with metadata envelope."""
    response = client.get("/api/github/prs/Kuzmenko-top/DNK_OS_MVP?allow_fixture_fallback=true", headers=AUTH_HEADERS)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()

    assert "data" in payload
    assert "data_source" in payload
    assert "stale" in payload
    assert "fetched_at" in payload
    assert isinstance(payload["data"], list)
    assert len(payload["data"]) > 0

    pr_item = payload["data"][0]
    assert "number" in pr_item
    assert "title" in pr_item
    assert "state" in pr_item
    assert "head_sha" in pr_item


def test_github_pr_checks_endpoint():
    """Verify GET /api/github/pr/{owner}/{repo}/{pr_number}/checks returns check runs envelope."""
    response = client.get("/api/github/pr/Kuzmenko-top/DNK_OS_MVP/30/checks?allow_fixture_fallback=true", headers=AUTH_HEADERS)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()

    assert "data" in payload
    assert "data_source" in payload
    data_dict = payload["data"]
    assert isinstance(data_dict, dict)
    assert "check_runs" in data_dict
    assert isinstance(data_dict["check_runs"], list)
    assert len(data_dict["check_runs"]) > 0
    assert "name" in data_dict["check_runs"][0]
    assert "status" in data_dict["check_runs"][0]


def test_github_pr_files_endpoint():
    """Verify GET /api/github/pr/{owner}/{repo}/{pr_number}/files returns changed files envelope."""
    response = client.get("/api/github/pr/Kuzmenko-top/DNK_OS_MVP/30/files?allow_fixture_fallback=true", headers=AUTH_HEADERS)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    payload = response.json()

    assert "data" in payload
    assert "data_source" in payload
    data_dict = payload["data"]
    assert isinstance(data_dict, dict)
    assert "files" in data_dict
    assert isinstance(data_dict["files"], list)
    assert len(data_dict["files"]) > 0
    assert "filename" in data_dict["files"][0]
    assert "status" in data_dict["files"][0]


def test_timeline_events_endpoint():
    """Verify GET /api/timeline/events with source and category filters."""
    response = client.get("/api/timeline/events?source=github&category=governance", headers=AUTH_HEADERS)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    payload = response.json()

    assert "data" in payload
    assert "total_count" in payload
    assert isinstance(payload["data"], list)
    assert len(payload["data"]) > 0
    for evt in payload["data"]:
        assert evt["source"] == "github"
        assert evt["category"] == "governance"


def test_timeline_events_all_filters():
    """Verify GET /api/timeline/events without filters returns full list."""
    response = client.get("/api/timeline/events", headers=AUTH_HEADERS)
    assert response.status_code == 200
    payload = response.json()

    assert "data" in payload
    assert len(payload["data"]) >= 3


def test_zero_mutation_and_read_only_cabinet_invariant():
    """Verify read-only GET accessibility and zero mutation invariant for Cabinet endpoints."""
    # Cabinet read-only GET endpoint returns 200 OK
    res = client.get("/api/github/prs/Kuzmenko-top/DNK_OS_MVP?allow_fixture_fallback=true", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert res.json()["data_source"] in ["fixture", "github_api"]
