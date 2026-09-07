# --- DNK-MRH-HEADER ---
# mrh_id: "tests_security_test_security_models"
# purpose: "Unit tests for Zero-Trust Security ORM Models (DNK-SECURITY-001 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone, timedelta
from apps.api.db.models.security_subject import SecuritySubjectModel
from apps.api.db.models.security_role import SecurityRoleModel
from apps.api.db.models.security_permission import SecurityPermissionModel
from apps.api.db.models.security_policy import SecurityPolicyModel
from apps.api.db.models.security_audit_log import SecurityAuditLogModel
from apps.api.db.models.security_token_revocation import SecurityTokenRevocationModel


def test_security_subject_model():
    subject = SecuritySubjectModel(
        workspace_id="ws-sec-01",
        subject_type="agent",
        subject_identifier="agent-audit-001",
        display_name="Auditor Agent",
        status="active",
        trust_score=0.95,
        mfa_enabled=True,
        roles=["auditor_role", "viewer_role"],
        attributes={"clearance": "top_secret", "dept": "secops"},
    )
    d = subject.to_dict()
    assert d["workspace_id"] == "ws-sec-01"
    assert d["subject_type"] == "agent"
    assert d["subject_identifier"] == "agent-audit-001"
    assert d["trust_score"] == 0.95
    assert d["mfa_enabled"] is True
    assert "auditor_role" in d["roles"]
    assert d["attributes"]["clearance"] == "top_secret"


def test_security_role_model():
    role = SecurityRoleModel(
        workspace_id="ws-sec-01",
        role_name="admin",
        description="Full administrative access",
        is_system_role=True,
        parent_role_id=None,
        permissions=["canvas:*", "system:*", "security:*"],
        metadata_json={"tier": 1},
    )
    d = role.to_dict()
    assert d["role_name"] == "admin"
    assert d["is_system_role"] is True
    assert len(d["permissions"]) == 3
    assert d["metadata_json"]["tier"] == 1


def test_security_permission_model():
    perm = SecurityPermissionModel(
        resource="canvas",
        action="write",
        permission_key="canvas:write",
        description="Allows modifying canvas nodes and state",
        is_system=True,
    )
    d = perm.to_dict()
    assert d["resource"] == "canvas"
    assert d["action"] == "write"
    assert d["permission_key"] == "canvas:write"
    assert d["is_system"] is True


def test_security_policy_model():
    policy = SecurityPolicyModel(
        workspace_id="ws-sec-01",
        policy_name="Enforce-MFA-Admin-Policy",
        description="Requires MFA and high trust score for admin resources",
        effect="ALLOW",
        priority=10,
        is_active=True,
        subject_roles=["admin"],
        subject_types=["user", "agent"],
        min_trust_score=0.8,
        resource_patterns=["api:v3:canvas:*", "system:*"],
        action_patterns=["write", "delete", "admin"],
        ip_allowlist=["10.0.0.0/8", "192.168.1.0/24"],
        ip_denylist=[],
        allowed_geo_countries=["UA", "DE", "US"],
        time_window_start_utc="06:00:00",
        time_window_end_utc="22:00:00",
        require_mfa=True,
        max_velocity_rpm=120,
    )
    d = policy.to_dict()
    assert d["policy_name"] == "Enforce-MFA-Admin-Policy"
    assert d["effect"] == "ALLOW"
    assert d["priority"] == 10
    assert d["min_trust_score"] == 0.8
    assert d["require_mfa"] is True
    assert "10.0.0.0/8" in d["ip_allowlist"]


def test_security_audit_log_model():
    log_entry = SecurityAuditLogModel(
        workspace_id="ws-sec-01",
        subject_id="sub-123",
        subject_type="user",
        action="canvas:delete_node",
        resource="canvas:node-99",
        decision="DENIED",
        reason="Trust score below required threshold",
        policy_id="pol-001",
        ip_address="203.0.113.195",
        geo_country="UA",
        user_agent="Mozilla/5.0",
        trust_score=0.45,
        extra_context={"anomaly": "unusual_velocity"},
        prev_hash="0" * 64,
        current_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    d = log_entry.to_dict()
    assert d["subject_id"] == "sub-123"
    assert d["decision"] == "DENIED"
    assert d["prev_hash"] == "0" * 64
    assert len(d["current_hash"]) == 64


def test_security_token_revocation_model():
    exp = datetime.now(timezone.utc) + timedelta(hours=2)
    revocation = SecurityTokenRevocationModel(
        token_jti="jti-test-abc-123",
        subject_id="sub-123",
        token_type="access",
        revocation_reason="Suspicious activity detected by firewall",
        is_revoked=True,
        expires_at=exp,
    )
    d = revocation.to_dict()
    assert d["token_jti"] == "jti-test-abc-123"
    assert d["is_revoked"] is True
    assert d["token_type"] == "access"
    assert d["expires_at"] is not None
