# --- DNK-MRH-HEADER ---
# mrh_id: "tests_security_test_security_router"
# purpose: "Integration Tests for Security REST Router (DNK-SECURITY-001 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.routers.security_router import router as security_router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(security_router)
    return TestClient(app)


def test_policy_crud_and_lifecycle(client):
    # 1. Create Policy
    create_payload = {
        "policy_name": "API Admin Full Access",
        "effect": "ALLOW",
        "subject_roles": ["admin", "superadmin"],
        "resource_patterns": ["api:v1:*"],
        "action_patterns": ["*"],
        "ip_allowlist": ["10.0.0.0/8", "192.168.1.0/24"],
        "geo_countries": ["UA", "US", "DE"],
        "min_trust_score": 0.8,
        "require_mfa": True,
        "priority": 10,
        "workspace_id": "ws_alpha",
    }
    resp = client.post("/api/v1/security/policies", json=create_payload)
    assert resp.status_code == 201
    created = resp.json()
    assert created["id"].startswith("pol_")
    policy_id = created["id"]

    # 2. List Policies
    list_resp = client.get("/api/v1/security/policies?workspace_id=ws_alpha")
    assert list_resp.status_code == 200
    policies = list_resp.json()
    assert any(p["id"] == policy_id for p in policies)

    # 3. Get Policy by ID
    get_resp = client.get(f"/api/v1/security/policies/{policy_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["policy_name"] == "API Admin Full Access"

    # 4. Delete Policy
    del_resp = client.delete(f"/api/v1/security/policies/{policy_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    # Verify 404 after delete
    assert client.get(f"/api/v1/security/policies/{policy_id}").status_code == 404


def test_dynamic_evaluate_access(client):
    # Add a viewer policy
    pol_payload = {
        "policy_name": "Viewer Read Policy",
        "effect": "ALLOW",
        "subject_roles": ["viewer"],
        "resource_patterns": ["catalog:products:*"],
        "action_patterns": ["read", "get"],
        "ip_allowlist": ["10.0.0.0/8"],
        "min_trust_score": 0.5,
        "priority": 50,
    }
    client.post("/api/v1/security/policies", json=pol_payload)

    # 1. Matching evaluation
    eval_req_allowed = {
        "subject_id": "user_viewer_1",
        "roles": ["viewer"],
        "resource": "catalog:products:item_42",
        "action": "read",
        "ip_address": "10.0.1.5",
        "trust_score": 0.9,
    }
    resp = client.post("/api/v1/security/evaluate", json=eval_req_allowed)
    assert resp.status_code == 200
    assert resp.json()["allowed"] is True
    assert resp.json()["decision"] == "ALLOWED"

    # 2. Non-matching IP (outside CIDR)
    eval_req_denied_ip = {
        "subject_id": "user_viewer_1",
        "roles": ["viewer"],
        "resource": "catalog:products:item_42",
        "action": "read",
        "ip_address": "203.0.113.1",
        "trust_score": 0.9,
    }
    resp_denied = client.post("/api/v1/security/evaluate", json=eval_req_denied_ip)
    assert resp_denied.status_code == 200
    assert resp_denied.json()["allowed"] is False
    assert resp_denied.json()["decision"] == "DENIED"


def test_token_revocation_endpoints(client):
    # 1. Revoke token
    revoke_payload = {
        "token_jti": "jti_test_revocation_123",
        "subject_id": "user_compromised",
        "reason": "Security incident test",
    }
    resp = client.post("/api/v1/security/tokens/revoke", json=revoke_payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "revoked"

    # 2. Check is-revoked
    check_resp = client.get("/api/v1/security/tokens/is-revoked/jti_test_revocation_123")
    assert check_resp.status_code == 200
    assert check_resp.json()["is_revoked"] is True

    # 3. Check non-revoked token
    check_clean = client.get("/api/v1/security/tokens/is-revoked/jti_clean_token")
    assert check_clean.status_code == 200
    assert check_clean.json()["is_revoked"] is False

    # 4. Get stats
    stats_resp = client.get("/api/v1/security/tokens/stats")
    assert stats_resp.status_code == 200
    assert stats_resp.json()["total_entries"] >= 1

    # 5. Cleanup
    clean_resp = client.post("/api/v1/security/tokens/cleanup")
    assert clean_resp.status_code == 200
    assert "pruned_count" in clean_resp.json()


def test_audit_logs_and_verify_chain(client):
    # Trigger an evaluate request to generate an audit log entry
    eval_req = {
        "subject_id": "user_audited",
        "roles": ["guest"],
        "resource": "admin:system",
        "action": "write",
        "trust_score": 0.1,
    }
    client.post("/api/v1/security/evaluate", json=eval_req)

    # 1. Query audit logs
    logs_resp = client.get("/api/v1/security/audit/logs?subject_id=user_audited")
    assert logs_resp.status_code == 200
    logs_data = logs_resp.json()
    assert logs_data["total"] >= 1
    assert any(log["subject_id"] == "user_audited" for log in logs_data["logs"])

    # 2. Verify audit chain
    chain_resp = client.get("/api/v1/security/audit/verify-chain")
    assert chain_resp.status_code == 200
    chain_data = chain_resp.json()
    assert chain_data["is_valid"] is True
    assert chain_data["tampered_index"] is None


def test_subject_and_role_management(client):
    # 1. Subject Management
    sub_payload = {
        "subject_id": "service_payment_worker",
        "subject_type": "service",
        "roles": ["payment_processor"],
        "trust_score": 0.95,
        "mfa_enabled": False,
        "workspace_id": "ws_finance",
        "metadata": {"cluster": "eu-central-1"},
    }
    create_sub_resp = client.post("/api/v1/security/subjects", json=sub_payload)
    assert create_sub_resp.status_code == 201

    get_sub_resp = client.get("/api/v1/security/subjects/service_payment_worker")
    assert get_sub_resp.status_code == 200
    assert get_sub_resp.json()["subject_type"] == "service"

    list_sub_resp = client.get("/api/v1/security/subjects?workspace_id=ws_finance")
    assert list_sub_resp.status_code == 200
    assert len(list_sub_resp.json()) >= 1

    # 2. Role Management
    role_payload = {
        "role_key": "finance_auditor",
        "role_name": "Finance Auditor",
        "permissions": ["finance:reports:read", "audit:logs:read"],
        "workspace_id": "ws_finance",
    }
    create_role_resp = client.post("/api/v1/security/roles", json=role_payload)
    assert create_role_resp.status_code == 201

    list_roles_resp = client.get("/api/v1/security/roles")
    assert list_roles_resp.status_code == 200
    assert any(r["role_key"] == "finance_auditor" for r in list_roles_resp.json())
