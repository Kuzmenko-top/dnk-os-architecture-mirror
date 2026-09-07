# --- DNK-MRH-HEADER ---
# mrh_id: "tests_dnk_os_002_test_github_router"
# purpose: "FastAPI router integration tests for GitHub Read-Only API endpoints"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.routers import github
from apps.api.services.github_adapter import GitHubAdapter
from apps.api.services.github_transport import MockGitHubTransport
from core.config.security_config import SECURITY_API_KEY

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": SECURITY_API_KEY}


def test_router_unauthorized_without_key():
    response = client.get("/api/github/pr/Kuzmenko-top/DNK_OS_MVP/18")
    assert response.status_code == 401


def test_router_forbidden_repo():
    response = client.get("/api/github/pr/malicious/repo/1", headers=AUTH_HEADERS)
    assert response.status_code == 403


def test_router_get_pr_success():
    mock_t = MockGitHubTransport()
    mock_t.set_response("repos/Kuzmenko-top/DNK_OS_MVP/pulls/18", {
        "number": 18,
        "title": "feat(dnk-os-002): clean server-side adapter",
        "state": "open",
        "merged": False,
        "head": {"sha": "clean_head_123"},
        "base": {"ref": "main"},
        "mergeable": True
    }, 200)

    test_adapter = GitHubAdapter(transport=mock_t)

    # Override adapter instance for router
    original_instance = github._adapter_instance
    github._adapter_instance = test_adapter
    try:
        response = client.get("/api/github/pr/Kuzmenko-top/DNK_OS_MVP/18", headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["data_source"] == "live"
        assert data["data"]["number"] == 18
        assert data["data"]["title"] == "feat(dnk-os-002): clean server-side adapter"
    finally:
        github._adapter_instance = original_instance


def test_router_get_checks_and_files():
    mock_t = MockGitHubTransport()
    mock_t.set_response("repos/Kuzmenko-top/DNK_OS_MVP/commits/sha999/check-runs", {
        "total_count": 1,
        "check_runs": [{"name": "pytest", "status": "completed", "conclusion": "success"}]
    }, 200)
    mock_t.set_response("repos/Kuzmenko-top/DNK_OS_MVP/pulls/18/files", [
        {"filename": "apps/api/services/github_adapter.py", "status": "modified", "additions": 10, "deletions": 0, "changes": 10}
    ], 200)

    test_adapter = GitHubAdapter(transport=mock_t)
    original_instance = github._adapter_instance
    github._adapter_instance = test_adapter
    try:
        checks_resp = client.get("/api/github/pr/Kuzmenko-top/DNK_OS_MVP/18/checks?ref=sha999", headers=AUTH_HEADERS)
        assert checks_resp.status_code == 200
        checks_data = checks_resp.json()
        assert checks_data["data"]["overall_status"] == "SUCCESS"

        files_resp = client.get("/api/github/pr/Kuzmenko-top/DNK_OS_MVP/18/files", headers=AUTH_HEADERS)
        assert files_resp.status_code == 200
        files_data = files_resp.json()
        assert len(files_data["data"]["files"]) == 1
        assert files_data["data"]["files"][0]["filename"] == "apps/api/services/github_adapter.py"
    finally:
        github._adapter_instance = original_instance
