# --- DNK-MRH-HEADER ---
# mrh_id: "tests_workspace_test_prompt_dock_staged_diff"
# purpose: "Automated test suite verifying AC-02 through AC-08: Prompt Dock, Staged Diff Preview, Hash Determinism, and Mutation Boundaries"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient
from apps.api.main import app
from apps.api.services import auth_service

client = TestClient(app)


@pytest.fixture
def valid_auth_headers():
    token = auth_service.generate_test_token(user_id="usr_admin_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")
    return {"Authorization": f"Bearer {token}"}


def test_ac_02_prompt_dock_submission(valid_auth_headers):
    payload = {
        "prompt": "Update hero banner background to gradient blue",
        "target_node_id": "node_hero_01",
        "context_parameters": {"theme": "dawn"}
    }
    resp = client.post("/api/v1/workspaces/ws_alpha/prompts", json=payload, headers=valid_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUBMITTED"
    assert data["workspace_id"] == "ws_alpha"
    assert data["tenant_id"] == "tenant_corp_a"
    assert "prompt_id" in data
    assert "task_id" in data


def test_ac_03_prompt_dock_empty_prompt_rejected(valid_auth_headers):
    payload = {"prompt": "   "}
    resp = client.post("/api/v1/workspaces/ws_alpha/prompts", json=payload, headers=valid_auth_headers)
    assert resp.status_code == 400
    assert resp.json()["detail"]["error_code"] == "PROMPT_REQUIRED"


def test_ac_04_staged_diff_preview_generation(valid_auth_headers):
    files = [
        {"file_path": "sections/hero-banner.liquid", "staged_snippet": "<div class='hero-gradient'>New Content</div>"}
    ]
    resp = client.post("/api/v1/workspaces/ws_alpha/diffs/stage?task_id=task_123", json=files, headers=valid_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "STAGED"
    assert data["staged_diff_hash"] != ""
    assert data["preview_hash"] != ""


def test_ac_05_canonical_hash_determinism(valid_auth_headers):
    files_a = [{"file_path": "sections/hero-banner.liquid", "staged_snippet": "<div>Test</div>"}]
    files_b = [{"file_path": "sections/hero-banner.liquid", "staged_snippet": "<div>Test</div>"}]

    resp_a = client.post("/api/v1/workspaces/ws_alpha/diffs/stage?task_id=task_1", json=files_a, headers=valid_auth_headers)
    resp_b = client.post("/api/v1/workspaces/ws_alpha/diffs/stage?task_id=task_2", json=files_b, headers=valid_auth_headers)

    assert resp_a.json()["staged_diff_hash"] == resp_b.json()["staged_diff_hash"]


def test_ac_06_mutation_boundaries_phase2_blocked(valid_auth_headers):
    # 1. Direct unapproved mutate endpoint blocked
    resp_mutate = client.post("/api/v1/workspaces/ws_alpha/mutate", headers=valid_auth_headers)
    assert resp_mutate.status_code == 403
    assert resp_mutate.json()["detail"]["error_code"] == "MUTATION_GATED_IN_PHASE_2"

    # 2. Shopify sync endpoint blocked
    resp_sync = client.post("/api/v1/workspaces/ws_alpha/shopify/sync", headers=valid_auth_headers)
    assert resp_sync.status_code == 403
    assert resp_sync.json()["detail"]["error_code"] == "SHOPIFY_WRITE_BLOCKED"

    # 3. Commit unapproved / empty body is rejected
    resp_commit = client.post("/api/v1/workspaces/ws_alpha/commit", headers=valid_auth_headers)
    assert resp_commit.status_code in [403, 422]
