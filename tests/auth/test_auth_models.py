# --- DNK-MRH-HEADER ---
# mrh_id: "tests/auth/test_auth_models.py"
# purpose: "Unit tests for DNK-AUTH-001 Multi-Tenant Authentication & Authorization ORM Models."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone, timedelta
from apps.api.db.models.auth_tenant import AuthTenant, TenantStatus, TenantTier
from apps.api.db.models.auth_user import AuthUser, UserAccountStatus, UserAuthProvider
from apps.api.db.models.auth_role import AuthRole, RoleScope
from apps.api.db.models.auth_permission import AuthPermission, PermissionAction
from apps.api.db.models.auth_api_key import AuthApiKey, ApiKeyStatus
from apps.api.db.models.auth_audit_log import AuthAuditLog, AuditEventType, AuditSeverity
from apps.api.db.models.auth_session import AuthSession, SessionStatus


def test_auth_tenant_lifecycle():
    tenant = AuthTenant(
        name="Acme Corporation",
        slug="acme-corp",
        tier=TenantTier.ENTERPRISE,
        max_users=100
    )
    assert tenant.is_active() is True
    assert tenant.slug == "acme-corp"
    assert tenant.tier == TenantTier.ENTERPRISE
    
    tenant.update_status(TenantStatus.SUSPENDED)
    assert tenant.is_active() is False
    
    data = tenant.to_dict()
    assert data["name"] == "Acme Corporation"
    assert data["status"] == "SUSPENDED"


def test_auth_user_password_hashing_and_verification():
    raw_pwd = "SuperSecretPassword123!"
    hash_val, salt = AuthUser.hash_password(raw_pwd)
    
    user = AuthUser(
        tenant_id="tenant_123",
        email="dev@acme.com",
        display_name="Senior Dev",
        password_hash=hash_val,
        salt=salt,
        provider=UserAuthProvider.LOCAL,
        roles=["developer"]
    )
    assert user.is_active() is True
    assert user.verify_password("SuperSecretPassword123!") is True
    assert user.verify_password("WrongPassword") is False
    
    data = user.to_dict(include_secrets=False)
    assert "password_hash" not in data
    assert data["email"] == "dev@acme.com"
    assert data["roles"] == ["developer"]


def test_auth_role_and_permission_matching():
    perm = AuthPermission(
        code="batch:jobs:read",
        resource="batch",
        action=PermissionAction.READ
    )
    assert perm.matches("batch:jobs:read") is True
    assert perm.matches("batch:jobs:write") is False
    
    wildcard_perm = AuthPermission(
        code="stream:*",
        resource="stream",
        action=PermissionAction.ALL
    )
    assert wildcard_perm.matches("stream:events:read") is True
    assert wildcard_perm.matches("stream:topics:create") is True
    assert wildcard_perm.matches("batch:jobs:read") is False
    
    role = AuthRole(
        name="batch_operator",
        display_name="Batch Operator",
        permissions=["batch:*", "observe:traces:read"],
        inherited_roles=["viewer"]
    )
    assert role.has_direct_permission("batch:jobs:create") is True
    assert role.has_direct_permission("batch:workflows:execute") is True
    assert role.has_direct_permission("observe:traces:read") is True
    assert role.has_direct_permission("security:audit:delete") is False


def test_auth_api_key_generation_and_validation():
    full_token, prefix, key_hash = AuthApiKey.generate_key_pair(prefix_name="dnk_live")
    assert full_token.startswith("dnk_live_")
    assert prefix == full_token[:12]
    
    api_key = AuthApiKey(
        name="Production Agent Key",
        tenant_id="tenant_acme",
        prefix=prefix,
        key_hash=key_hash,
        scopes=["batch:*", "stream:read"],
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    
    assert api_key.is_valid() is True
    assert api_key.verify_token(full_token) is True
    assert api_key.verify_token("invalid_token_12345") is False
    
    api_key.revoke()
    assert api_key.is_valid() is False
    assert api_key.verify_token(full_token) is False


def test_auth_audit_log_tamper_evidence():
    log = AuthAuditLog(
        tenant_id="tenant_acme",
        actor_id="usr_admin_1",
        actor_type="user",
        event_type=AuditEventType.USER_LOGIN_SUCCESS,
        severity=AuditSeverity.INFO,
        resource="auth",
        action="login",
        details={"ip": "192.168.1.100", "auth_method": "password"}
    )
    log.seal()
    assert log.checksum is not None
    assert log.verify_integrity() is True
    
    # Tampering attempt
    log.details["ip"] = "10.0.0.99"
    assert log.verify_integrity() is False


def test_auth_session_management():
    now = datetime.now(timezone.utc)
    session = AuthSession(
        tenant_id="tenant_acme",
        user_id="usr_123",
        expires_at=now + timedelta(hours=2),
        device_fingerprint="fp_hash_abc123"
    )
    assert session.is_valid() is True
    
    session.touch()
    assert session.last_active_at >= now
    
    session.revoke()
    assert session.is_valid() is False
