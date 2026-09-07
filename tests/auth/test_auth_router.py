# --- DNK-MRH-HEADER ---
# mrh_id: "tests/auth/test_auth_router.py"
# purpose: "Integration tests for DNK-AUTH-001 REST API Router, FastAPI Dependencies & Security Middleware."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_jwks_endpoint():
    response = client.get("/api/v1/auth/jwks.json")
    assert response.status_code == 200
    data = response.json()
    assert "keys" in data
    assert len(data["keys"]) > 0
    assert data["keys"][0]["kty"] in ("oct", "RSA", "EC")


def test_user_registration_and_login_flow():
    # 1. Register User
    reg_payload = {
        "tenant_id": "tenant_default",
        "email": "user.test@dnk-e.com",
        "password": "SecurePassword123!",
        "display_name": "Test User",
        "roles": ["developer"],
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["status"] == "success"
    user_id = reg_data["user_id"]

    # 2. Login User
    login_payload = {
        "tenant_id": "tenant_default",
        "email": "user.test@dnk-e.com",
        "password": "SecurePassword123!",
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["user_id"] == user_id

    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 3. Get /me Profile
    headers = {"Authorization": f"Bearer {access_token}"}
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    profile = me_res.json()
    assert profile["subject_id"] == user_id
    assert "developer" in profile["roles"]

    # 4. Refresh Token
    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    ref_tokens = ref_res.json()
    assert "access_token" in ref_tokens
    assert ref_tokens["access_token"] != access_token

    # 5. Logout
    logout_res = client.post("/api/v1/auth/logout", json={"refresh_token": ref_tokens["refresh_token"]}, headers=headers)
    assert logout_res.status_code == 200


def test_api_keys_flow():
    # Login first to get JWT
    login_res = client.post(
        "/api/v1/auth/login",
        json={"tenant_id": "tenant_default", "email": "user.test@dnk-e.com", "password": "SecurePassword123!"},
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Create API Key
    key_payload = {
        "tenant_id": "tenant_default",
        "name": "Integration Test Key",
        "scopes": ["batch:read", "stream:read"],
        "rate_limit_rpm": 300,
    }
    create_res = client.post("/api/v1/auth/api-keys", json=key_payload, headers=headers)
    assert create_res.status_code == 201
    key_data = create_res.json()
    assert "secret_key" in key_data
    key_id = key_data["id"]
    secret_key = key_data["secret_key"]

    # Access endpoint using X-API-Key
    api_headers = {"X-API-Key": secret_key}
    me_res = client.get("/api/v1/auth/me", headers=api_headers)
    assert me_res.status_code == 200
    subject = me_res.json()
    assert subject["subject_type"] == "api_key"
    assert "batch:read" in subject["direct_permissions"]

    # List API Keys
    list_res = client.get("/api/v1/auth/api-keys", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["count"] >= 1

    # Revoke API Key
    del_res = client.delete(f"/api/v1/auth/api-keys/{key_id}", headers=headers)
    assert del_res.status_code == 200


def test_rbac_check_and_audit_logs():
    login_res = client.post(
        "/api/v1/auth/login",
        json={"tenant_id": "tenant_default", "email": "user.test@dnk-e.com", "password": "SecurePassword123!"},
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # Check RBAC
    rbac_req = {
        "resource_type": "batch_job",
        "action": "read",
    }
    rbac_res = client.post("/api/v1/auth/rbac/check", json=rbac_req, headers=headers)
    assert rbac_res.status_code == 200
    decision = rbac_res.json()
    assert "allowed" in decision

    # Audit logs
    audit_res = client.get("/api/v1/auth/audit/logs", headers=headers)
    assert audit_res.status_code == 200
    assert "audit_logs" in audit_res.json()
