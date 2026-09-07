# --- DNK-MRH-HEADER ---
# mrh_id: "tests/auth/test_oidc_auth_service.py"
# purpose: "Unit tests for DNK-AUTH-001 OIDC, JWT Minting, Key Rotation & Revocation Service."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import time
from apps.api.services.oidc_auth_service import OIDCAuthService
from apps.api.db.models.auth_user import AuthUser, UserAuthProvider, UserAccountStatus


def test_oidc_service_initialization_and_jwks():
    svc = OIDCAuthService(issuer="https://auth.dnk-test.com")
    jwks = svc.get_jwks()
    assert "keys" in jwks
    assert len(jwks["keys"]) == 1
    assert jwks["keys"][0]["status"] == "active"
    assert jwks["keys"][0]["alg"] == "HS256"


def test_oidc_key_rotation():
    svc = OIDCAuthService(issuer="https://auth.dnk-test.com")
    old_kid = svc._active_kid
    
    # Register user & mint token with old key
    user = svc.register_user("tenant_1", "dev@dnk.com", "Dev", password="pwd")
    old_token = svc.mint_access_token(user)
    
    # Rotate key
    new_kid = svc.rotate_signing_key()
    assert new_kid != old_kid
    
    jwks = svc.get_jwks()
    assert len(jwks["keys"]) == 2
    
    # Tokens minted before rotation still verify because old key is retained in keyring
    payload = svc.verify_token(old_token)
    assert payload["sub"] == user.id
    
    # New tokens are signed with new active key
    new_token = svc.mint_access_token(user)
    new_payload = svc.verify_token(new_token)
    assert new_payload["sub"] == user.id


def test_user_authentication_flow():
    svc = OIDCAuthService()
    user = svc.register_user(
        tenant_id="tenant_alpha",
        email="lead@company.com",
        display_name="Tech Lead",
        password="SecurePassw0rd!",
        roles=["admin"]
    )
    
    # Invalid password attempt
    with pytest.raises(ValueError, match="Invalid email or password"):
        svc.authenticate_local_user("tenant_alpha", "lead@company.com", "WrongPass")
    
    # Successful login
    access_token, refresh_token, session = svc.authenticate_local_user(
        tenant_id="tenant_alpha",
        email="lead@company.com",
        password="SecurePassw0rd!",
        ip_address="10.0.0.1",
        user_agent="PyTest-Client"
    )
    
    assert access_token is not None
    assert refresh_token is not None
    assert session.is_valid() is True
    
    # Verify access token
    claims = svc.verify_token(access_token)
    assert claims["sub"] == user.id
    assert claims["tenant_id"] == "tenant_alpha"
    assert "admin" in claims["roles"]


def test_token_refresh_and_replay_protection():
    svc = OIDCAuthService()
    user = svc.register_user("tenant_beta", "bob@example.com", "Bob", password="BobPassword123")
    
    _, refresh_token, session = svc.authenticate_local_user("tenant_beta", "bob@example.com", "BobPassword123")
    
    # Perform standard refresh
    new_access_token, new_refresh_token = svc.refresh_access_token(refresh_token)
    assert new_access_token is not None
    assert new_refresh_token is not None
    assert new_refresh_token != refresh_token
    
    # Attempting to re-use old refresh token should fail
    with pytest.raises(ValueError, match="revoked|mismatched"):
        svc.refresh_access_token(refresh_token)


def test_token_denylist_revocation():
    svc = OIDCAuthService()
    user = svc.register_user("tenant_gamma", "carol@example.com", "Carol", password="CarolPassword123")
    access_token = svc.mint_access_token(user)
    
    # Valid before revocation
    claims = svc.verify_token(access_token)
    assert claims["email"] == "carol@example.com"
    
    # Revoke token
    svc.revoke_token(access_token)
    
    # Fails after revocation
    with pytest.raises(ValueError, match="Token has been revoked"):
        svc.verify_token(access_token)
