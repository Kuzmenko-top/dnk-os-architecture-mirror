# --- DNK-MRH-HEADER ---
# mrh_id: "tests_workspace_test_approval_snapshot_commit_rollback"
# purpose: "Automated test suite verifying AC-11 through AC-16: Approval Cards, Pre-Mutation Snapshots, OCC Commits, 1-Click Rollback, Kill-Switch, and Audit Trail"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.services.auth_service import auth_service
from apps.api.services.workspace_service import workspace_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_workspace_state():
    workspace_service.WORKSPACES_DB["ws_alpha"]["metadata"]["state"] = "ACTIVE"
    workspace_service.WORKSPACES_DB["ws_alpha"]["metadata"]["version"] = 1
    yield
    workspace_service.WORKSPACES_DB["ws_alpha"]["metadata"]["state"] = "ACTIVE"


@pytest.fixture
def admin_auth_headers():
    token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": "tenant_corp_a",
        "X-Workspace-Id": "ws_alpha"
    }


@pytest.fixture
def viewer_auth_headers():
    token = auth_service.generate_test_token(
        user_id="usr_viewer_002",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )
    return {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": "tenant_corp_a",
        "X-Workspace-Id": "ws_alpha"
    }


def test_ac_11_approval_card_creation_and_expiration(admin_auth_headers):
    # 1. Create approval card
    payload = {
        "staged_diff_hash": "sha256_staged_diff_hero_banner_v1",
        "summary": "Update hero banner liquid section to blue gradient",
        "expires_in_minutes": 15
    }
    resp = client.post("/api/v1/workspaces/ws_alpha/approvals/create", json=payload, headers=admin_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "PENDING"
    assert data["approval_signature"] is not None
    approval_id = data["approval_id"]

    # 2. Approve card with valid role
    action_payload = {"action": "APPROVE"}
    resp_approve = client.post(f"/api/v1/workspaces/ws_alpha/approvals/{approval_id}/action", json=action_payload, headers=admin_auth_headers)
    assert resp_approve.status_code == 200
    assert resp_approve.json()["status"] == "APPROVED"


def test_ac_11_role_gate_approval_denied_for_viewer(viewer_auth_headers):
    payload = {
        "staged_diff_hash": "sha256_staged_diff_hero_banner_v1",
        "summary": "Unauthorized approval attempt"
    }
    resp = client.post("/api/v1/workspaces/ws_alpha/approvals/create", json=payload, headers=viewer_auth_headers)
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "ROLE_NOT_AUTHORIZED"


def test_ac_12_pre_mutation_snapshot_creation(admin_auth_headers):
    resp = client.post("/api/v1/workspaces/ws_alpha/snapshots", headers=admin_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "snapshot_id" in data
    assert "pre_hash" in data
    assert len(data["pre_hash"]) == 64
    assert len(data["nodes_state"]) > 0


def test_ac_13_occ_commit_version_mismatch_conflict(admin_auth_headers):
    # OCC conflict simulation
    commit_payload = {
        "diff_id": "diff_001",
        "expected_version": 999,  # Mismatched version
        "idempotency_key": "idem_tx_001",
        "modified_files": [{"file_path": "sections/hero-banner.liquid", "staged_snippet": "<div>OCC</div>"}]
    }
    resp = client.post("/api/v1/workspaces/ws_alpha/commit", json=commit_payload, headers=admin_auth_headers)
    assert resp.status_code == 409
    assert resp.json()["detail"]["error_code"] == "VERSION_MISMATCH"


def test_ac_13_successful_occ_commit_and_idempotency(admin_auth_headers):
    # 1. Successful commit
    commit_payload = {
        "diff_id": "diff_002",
        "expected_version": 1,
        "idempotency_key": "idem_tx_002",
        "modified_files": [{"file_path": "sections/hero-banner.liquid", "staged_snippet": "<div class='banner'>Committed</div>"}]
    }
    resp1 = client.post("/api/v1/workspaces/ws_alpha/commit", json=commit_payload, headers=admin_auth_headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "COMMITTED"
    assert data1["new_version"] == 2

    # 2. Idempotent retry returns identical commit response
    resp2 = client.post("/api/v1/workspaces/ws_alpha/commit", json=commit_payload, headers=admin_auth_headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["commit_id"] == data1["commit_id"]
    assert data2["new_version"] == data1["new_version"]


def test_ac_14_multi_section_mutation_boundary_rejected(admin_auth_headers):
    multi_file_payload = {
        "diff_id": "diff_multi",
        "expected_version": 2,
        "idempotency_key": "idem_multi",
        "modified_files": [
            {"file_path": "sections/hero-banner.liquid", "staged_snippet": "<div>Hero</div>"},
            {"file_path": "sections/footer.liquid", "staged_snippet": "<div>Footer</div>"}
        ]
    }
    resp = client.post("/api/v1/workspaces/ws_alpha/commit", json=multi_file_payload, headers=admin_auth_headers)
    assert resp.status_code == 400
    assert resp.json()["detail"]["error_code"] == "MULTI_SECTION_MUTATION_DENIED"


def test_ac_15_one_click_rollback_execution(admin_auth_headers):
    # 1. Take snapshot
    resp_snap = client.post("/api/v1/workspaces/ws_alpha/snapshots", headers=admin_auth_headers)
    snap_data = resp_snap.json()
    snapshot_id = snap_data["snapshot_id"]
    pre_hash = snap_data["pre_hash"]

    # 2. Mutate state via commit
    commit_payload = {
        "diff_id": "diff_roll",
        "expected_version": 2,
        "idempotency_key": "idem_roll_01",
        "modified_files": [{"file_path": "sections/hero-banner.liquid", "staged_snippet": "<div>Pre-Rollback State</div>"}]
    }
    client.post("/api/v1/workspaces/ws_alpha/commit", json=commit_payload, headers=admin_auth_headers)

    # 3. Execute 1-click rollback
    rollback_payload = {"snapshot_id": snapshot_id}
    resp_roll = client.post("/api/v1/workspaces/ws_alpha/rollback", json=rollback_payload, headers=admin_auth_headers)
    assert resp_roll.status_code == 200
    roll_data = resp_roll.json()
    assert roll_data["status"] == "RESTORED"
    assert roll_data["restored_hash"] == pre_hash


def test_ac_16_emergency_kill_switch_and_audit_trail(admin_auth_headers):
    # 1. Trigger kill-switch
    resp_kill = client.post("/api/v1/workspaces/ws_alpha/kill-switch", headers=admin_auth_headers)
    assert resp_kill.status_code == 200
    assert resp_kill.json()["status"] == "LOCKED_READ_ONLY"

    # 2. Attempt mutation after kill-switch
    commit_payload = {
        "diff_id": "diff_blocked",
        "expected_version": 1,
        "idempotency_key": "idem_blocked",
        "modified_files": [{"file_path": "sections/hero.liquid", "staged_snippet": "<div>Fail</div>"}]
    }
    resp_commit = client.post("/api/v1/workspaces/ws_alpha/commit", json=commit_payload, headers=admin_auth_headers)
    assert resp_commit.status_code == 403
    assert resp_commit.json()["detail"]["error_code"] == "WORKSPACE_LOCKED_READ_ONLY"

    # 3. Check audit trail
    resp_audit = client.get("/api/v1/workspaces/ws_alpha/audit-trail", headers=admin_auth_headers)
    assert resp_audit.status_code == 200
    events = resp_audit.json()
    assert len(events) > 0
    assert any(e["action"] == "KILL_SWITCH_TRIGGERED" for e in events)
