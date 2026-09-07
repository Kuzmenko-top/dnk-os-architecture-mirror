# --- DNK-MRH-HEADER ---
# mrh_id: "tests_security_test_security_middleware"
# purpose: "Unit & Integration Tests for Zero-Trust Middleware & Token Signature Verifier (DNK-SECURITY-001 Phase 3)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timedelta, timezone
import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from apps.api.middleware.zero_trust_middleware import ZeroTrustMiddleware
from apps.api.services.audit_trail_engine import AuditTrailEngine
from apps.api.services.token_revocation_engine import TokenRevocationEngine
from apps.api.services.token_signature_verifier import TokenSignatureVerifier
from apps.api.services.zero_trust_policy_engine import ZeroTrustPolicyEngine


# ---------------------------------------------------------------------------
# TokenSignatureVerifier Tests
# ---------------------------------------------------------------------------

def test_token_verifier_success_and_claims():
    verifier = TokenSignatureVerifier(secret_key="test-secret-12345")
    token = verifier.create_token(
        subject_id="user_test_1",
        workspace_id="ws_alpha",
        roles=["editor", "viewer"],
        subject_type="user",
        trust_score=0.88,
        mfa_authenticated=True,
        expires_in_seconds=3600,
        custom_claims={"team": "engineering"},
    )
    assert isinstance(token, str)

    result = verifier.verify_token(token)
    assert result.valid is True
    assert result.payload is not None
    assert result.payload.sub == "user_test_1"
    assert result.payload.workspace_id == "ws_alpha"
    assert "editor" in result.payload.roles
    assert result.payload.trust_score == 0.88
    assert result.payload.mfa_authenticated is True
    assert result.payload.custom_claims.get("team") == "engineering"


def test_token_verifier_invalid_signature():
    verifier_a = TokenSignatureVerifier(secret_key="secret-key-A")
    verifier_b = TokenSignatureVerifier(secret_key="secret-key-B")

    token_a = verifier_a.create_token(subject_id="user_1")
    result = verifier_b.verify_token(token_a)

    assert result.valid is False
    assert result.error_code == "INVALID_SIGNATURE"


def test_token_verifier_expired_token():
    verifier = TokenSignatureVerifier(secret_key="test-secret")
    # Token with negative expiry
    token = verifier.create_token(subject_id="user_1", expires_in_seconds=-10)

    result = verifier.verify_token(token)
    assert result.valid is False
    assert result.error_code == "EXPIRED"


def test_token_verifier_malformed_token():
    verifier = TokenSignatureVerifier(secret_key="test-secret")
    assert verifier.verify_token("invalid.token").valid is False
    assert verifier.verify_token("").valid is False


# ---------------------------------------------------------------------------
# ZeroTrustMiddleware Integration Tests
# ---------------------------------------------------------------------------

@pytest.fixture
def test_setup():
    app = FastAPI()
    policy_engine = ZeroTrustPolicyEngine()
    revocation_engine = TokenRevocationEngine()
    audit_engine = AuditTrailEngine()
    token_verifier = TokenSignatureVerifier(secret_key="integration-secret")

    test_policies = []

    def policies_provider():
        return test_policies

    app.add_middleware(
        ZeroTrustMiddleware,
        policy_engine=policy_engine,
        revocation_engine=revocation_engine,
        audit_engine=audit_engine,
        token_verifier=token_verifier,
        policies_provider=policies_provider,
        exempt_paths=["/health", "/docs", "/openapi.json"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/v1/resource")
    def get_resource(request: Request):
        return {
            "status": "success",
            "subject": request.state.security_subject.sub,
            "roles": request.state.security_subject.roles,
        }

    @app.post("/api/v1/resource")
    def create_resource(request: Request):
        return {"status": "created", "subject": request.state.security_subject.sub}

    client = TestClient(app)

    return {
        "app": app,
        "client": client,
        "policies": test_policies,
        "policy_engine": policy_engine,
        "revocation_engine": revocation_engine,
        "audit_engine": audit_engine,
        "token_verifier": token_verifier,
    }


def test_middleware_exempt_path(test_setup):
    client = test_setup["client"]
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_middleware_missing_auth_header(test_setup):
    client = test_setup["client"]
    resp = client.get("/api/v1/resource")
    assert resp.status_code == 401
    assert "Missing or invalid Bearer token" in resp.json()["detail"]


def test_middleware_revoked_token(test_setup):
    client = test_setup["client"]
    verifier = test_setup["token_verifier"]
    revocation = test_setup["revocation_engine"]

    token = verifier.create_token(subject_id="user_revoked", jti="jti_bad_token")
    revocation.revoke_token(token_jti="jti_bad_token", subject_id="user_revoked", expires_at=datetime.now(timezone.utc) + timedelta(hours=1))

    resp = client.get("/api/v1/resource", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401
    assert resp.json()["error_code"] == "REVOKED"


def test_middleware_default_closed_deny(test_setup):
    client = test_setup["client"]
    verifier = test_setup["token_verifier"]
    # No policies configured -> default deny
    token = verifier.create_token(subject_id="user_clean", roles=["user"])

    resp = client.get("/api/v1/resource", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    assert "Forbidden" in resp.json()["detail"]


def test_middleware_policy_allow_and_audit(test_setup):
    client = test_setup["client"]
    verifier = test_setup["token_verifier"]
    audit = test_setup["audit_engine"]
    audit.clear()

    # Add ALLOW policy
    test_setup["policies"].append({
        "id": "pol_allow_read",
        "policy_name": "Allow Read API Resource",
        "effect": "ALLOW",
        "subject_roles": ["reader", "admin"],
        "resource_patterns": ["api:api:v1:resource"],
        "action_patterns": ["get"],
        "priority": 10,
    })

    token = verifier.create_token(subject_id="user_reader", roles=["reader"])
    resp = client.get("/api/v1/resource", headers={"Authorization": f"Bearer {token}"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["subject"] == "user_reader"

    # Verify audit log recorded ALLOWED event
    logs = audit.query_logs(limit=5)
    assert len(logs) >= 1
    assert logs[0]["decision"] == "ALLOWED"
    assert logs[0]["subject_id"] == "user_reader"


def test_middleware_mfa_required_policy(test_setup):
    client = test_setup["client"]
    verifier = test_setup["token_verifier"]

    test_setup["policies"].append({
        "id": "pol_admin_write_mfa",
        "policy_name": "Admin Write Requires MFA",
        "effect": "ALLOW",
        "subject_roles": ["admin"],
        "resource_patterns": ["api:api:v1:resource"],
        "action_patterns": ["post"],
        "require_mfa": True,
        "priority": 10,
    })

    # Token WITHOUT MFA
    token_no_mfa = verifier.create_token(subject_id="admin_1", roles=["admin"], mfa_authenticated=False)
    resp_no_mfa = client.post("/api/v1/resource", headers={"Authorization": f"Bearer {token_no_mfa}"})
    assert resp_no_mfa.status_code == 403
    assert resp_no_mfa.json()["required_mfa"] is True

    # Token WITH MFA
    token_with_mfa = verifier.create_token(subject_id="admin_1", roles=["admin"], mfa_authenticated=True)
    resp_with_mfa = client.post("/api/v1/resource", headers={"Authorization": f"Bearer {token_with_mfa}"})
    assert resp_with_mfa.status_code == 200
    assert resp_with_mfa.json()["status"] == "created"
