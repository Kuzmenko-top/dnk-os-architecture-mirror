# --- DNK-MRH-HEADER ---
# mrh_id: "tests_workspace_test_auth_rotation"
# purpose: "Security and rotation tests for Vault dynamic JWT keys, AuthProvider IAM registration, and admin rotation API"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient
from apps.api.main import app
from apps.api.services.auth_service import auth_service
from apps.api.services.vault_client import vault_client
from apps.api.services.auth_provider import auth_provider

client = TestClient(app)


def test_auth_service_token_verification_with_vault():
    token = auth_service.generate_test_token(user_id="user_john", tenant_id="tenant_corp_a", workspace_id="ws_alpha")
    payload = auth_service.verify_access_token(token)
    assert payload["sub"] == "user_john"
    assert payload["tenant_id"] == "tenant_corp_a"
    assert payload["workspace_id"] == "ws_alpha"


def test_secret_rotation_grace_period_verification():
    # 1. Generate token before rotation
    token_old = auth_service.generate_test_token(user_id="user_john")
    
    # 2. Perform rotation
    vault_client.rotate_jwt_secret()
    
    # 3. Generate token after rotation
    token_new = auth_service.generate_test_token(user_id="user_john")
    
    # 4. Old token still verifies during grace period
    payload_old = auth_service.verify_access_token(token_old, allow_grace_period=True)
    assert payload_old["sub"] == "user_john"
    
    # 5. New token verifies
    payload_new = auth_service.verify_access_token(token_new)
    assert payload_new["sub"] == "user_john"


def test_admin_rotate_jwt_secret_endpoint():
    # Admin user token
    admin_token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha",
        roles=["admin"]
    )
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    resp = client.post("/api/v1/admin/security/rotate-jwt-secret", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert "rotated_at" in data


def test_non_admin_cannot_rotate_secret():
    viewer_token = auth_service.generate_test_token(
        user_id="usr_viewer_002",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha",
        roles=["viewer"]
    )
    headers = {"Authorization": f"Bearer {viewer_token}"}
    
    resp = client.post("/api/v1/admin/security/rotate-jwt-secret", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "ADMIN_ROLE_REQUIRED"


def test_dynamic_user_registration_and_workspace_access():
    admin_token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha",
        roles=["admin"]
    )
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Register dynamic new user
    new_user_payload = {
        "user_id": "usr_dynamic_pilot_001",
        "tenant_id": "tenant_corp_a",
        "email": "pilot@dnk-corp.io",
        "workspaces": ["ws_alpha", "ws_pilot_test"],
        "roles": ["developer"]
    }
    resp = client.post("/api/v1/admin/security/users", json=new_user_payload, headers=headers)
    assert resp.status_code == 201
    created_user = resp.json()
    assert created_user["user_id"] == "usr_dynamic_pilot_001"
    
    # Verify new dynamic user can generate and use token
    pilot_token = auth_service.generate_test_token(
        user_id="usr_dynamic_pilot_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )
    pilot_headers = {"Authorization": f"Bearer {pilot_token}"}
    workspace_resp = client.get("/api/v1/workspaces/ws_alpha", headers=pilot_headers)
    assert workspace_resp.status_code == 200
