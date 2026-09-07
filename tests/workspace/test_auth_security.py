# --- DNK-MRH-HEADER ---
# mrh_id: "tests_workspace_test_auth_security"
# purpose: "Security negative test suite verifying workspace JWT validation, tenant isolation, non-member rejection, and header tampering"
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


def test_unauthenticated_workspace_request_denied():
    resp = client.get("/api/v1/workspaces/ws_alpha")
    assert resp.status_code == 401
    assert resp.json()["detail"]["error_code"] == "UNAUTHORIZED"


def test_expired_jwt_denied():
    token = auth_service.generate_test_token(expires_in_seconds=-10)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/workspaces/ws_alpha", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["detail"]["error_code"] == "TOKEN_EXPIRED"


def test_revoked_jwt_denied():
    jti = "revoked_jti_test_123"
    token = auth_service.generate_test_token(jti=jti)
    auth_service.revoke_token(jti)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/workspaces/ws_alpha", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["detail"]["error_code"] == "TOKEN_REVOKED"


def test_invalid_issuer_denied():
    token = auth_service.generate_test_token(issuer="untrusted-issuer")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/workspaces/ws_alpha", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["detail"]["error_code"] == "INVALID_TOKEN"


def test_invalid_audience_denied():
    token = auth_service.generate_test_token(audience="wrong-audience")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/workspaces/ws_alpha", headers=headers)
    assert resp.status_code == 401
    assert resp.json()["detail"]["error_code"] == "INVALID_TOKEN"


def test_non_member_tenant_denied():
    token = auth_service.generate_test_token(user_id="user_bob", tenant_id="tenant_corp_b")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/workspaces/ws_alpha", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "WORKSPACE_ACCESS_DENIED"


def test_non_member_workspace_denied():
    token = auth_service.generate_test_token(user_id="user_john", tenant_id="tenant_corp_a")
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get("/api/v1/workspaces/ws_forbidden", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "WORKSPACE_ACCESS_DENIED"


def test_header_tenant_mismatch_tampering_denied():
    token = auth_service.generate_test_token(user_id="user_john", tenant_id="tenant_corp_a")
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": "tenant_hacked_b"
    }
    resp = client.get("/api/v1/workspaces/ws_alpha", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "TENANT_MISMATCH"
