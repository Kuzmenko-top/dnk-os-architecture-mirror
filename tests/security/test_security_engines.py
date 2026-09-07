# --- DNK-MRH-HEADER ---
# mrh_id: "tests_security_test_security_engines"
# purpose: "Unit tests for Core Zero-Trust Security Engines (DNK-SECURITY-001 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timedelta, timezone
import pytest

from apps.api.services.zero_trust_policy_engine import (
    RequestContext,
    ZeroTrustPolicyEngine,
)
from apps.api.services.token_revocation_engine import TokenRevocationEngine
from apps.api.services.audit_trail_engine import AuditTrailEngine


# ---------------------------------------------------------------------------
# ZeroTrustPolicyEngine Tests
# ---------------------------------------------------------------------------

def test_policy_engine_default_closed_deny():
    engine = ZeroTrustPolicyEngine()
    ctx = RequestContext(subject_id="sub_1", roles=["viewer"], ip_address="1.2.3.4")
    res = engine.evaluate(ctx, resource="canvas:nodes", action="write", policies=[])
    assert not res.allowed
    assert res.decision == "DENIED"
    assert "Default Zero-Trust Deny" in res.reason


def test_policy_engine_role_and_wildcard_matching():
    engine = ZeroTrustPolicyEngine()
    ctx_admin = RequestContext(subject_id="admin_1", roles=["admin"], ip_address="10.0.0.1")
    ctx_viewer = RequestContext(subject_id="viewer_1", roles=["viewer"], ip_address="10.0.0.2")

    policies = [
        {
            "id": "pol_admin",
            "policy_name": "Admin Full Access",
            "effect": "ALLOW",
            "subject_roles": ["admin"],
            "resource_patterns": ["*"],
            "action_patterns": ["*"],
            "priority": 10,
        },
        {
            "id": "pol_viewer",
            "policy_name": "Viewer Read Access",
            "effect": "ALLOW",
            "subject_roles": ["viewer"],
            "resource_patterns": ["canvas:*"],
            "action_patterns": ["read"],
            "priority": 20,
        },
    ]

    # Admin can do anything
    res_adm = engine.evaluate(ctx_admin, resource="canvas:export", action="delete", policies=policies)
    assert res_adm.allowed
    assert res_adm.matched_policy_id == "pol_admin"

    # Viewer can read canvas
    res_vw_read = engine.evaluate(ctx_viewer, resource="canvas:export", action="read", policies=policies)
    assert res_vw_read.allowed
    assert res_vw_read.matched_policy_id == "pol_viewer"

    # Viewer cannot delete canvas
    res_vw_del = engine.evaluate(ctx_viewer, resource="canvas:export", action="delete", policies=policies)
    assert not res_vw_del.allowed
    assert res_vw_del.decision == "DENIED"


def test_policy_engine_ip_allowlist_and_cidr():
    engine = ZeroTrustPolicyEngine()
    policies = [
        {
            "id": "pol_cidr",
            "policy_name": "Internal CIDR Only",
            "effect": "ALLOW",
            "subject_roles": ["*"],
            "resource_patterns": ["api:v3:*"],
            "action_patterns": ["*"],
            "ip_allowlist": ["192.168.1.0/24", "10.0.0.5"],
            "priority": 10,
        }
    ]

    ctx_ok_subnet = RequestContext(subject_id="u1", roles=["user"], ip_address="192.168.1.42")
    res_ok = engine.evaluate(ctx_ok_subnet, resource="api:v3:canvas", action="get", policies=policies)
    assert res_ok.allowed

    ctx_bad_ip = RequestContext(subject_id="u2", roles=["user"], ip_address="192.168.2.1")
    res_bad = engine.evaluate(ctx_bad_ip, resource="api:v3:canvas", action="get", policies=policies)
    assert not res_bad.allowed


def test_policy_engine_ip_denylist_immediate_block():
    engine = ZeroTrustPolicyEngine()
    policies = [
        {
            "id": "pol_open",
            "policy_name": "Open Access with Blacklist",
            "effect": "ALLOW",
            "subject_roles": ["*"],
            "resource_patterns": ["*"],
            "action_patterns": ["*"],
            "ip_denylist": ["203.0.113.0/24"],
            "priority": 10,
        }
    ]

    ctx_blocked = RequestContext(subject_id="u1", roles=["user"], ip_address="203.0.113.50")
    res = engine.evaluate(ctx_blocked, resource="api:v3:canvas", action="read", policies=policies)
    assert not res.allowed
    assert "in denylist" in res.reason


def test_policy_engine_geo_country_and_trust_score():
    engine = ZeroTrustPolicyEngine()
    policies = [
        {
            "id": "pol_geo_trust",
            "policy_name": "Geo & High Trust Policy",
            "effect": "ALLOW",
            "subject_roles": ["*"],
            "resource_patterns": ["*"],
            "action_patterns": ["*"],
            "allowed_geo_countries": ["UA", "US", "DE"],
            "min_trust_score": 0.75,
            "priority": 10,
        }
    ]

    ctx_valid = RequestContext(subject_id="u1", roles=["user"], geo_country="UA", trust_score=0.9)
    assert engine.evaluate(ctx_valid, resource="api:v3:canvas", action="read", policies=policies).allowed

    ctx_bad_geo = RequestContext(subject_id="u2", roles=["user"], geo_country="CN", trust_score=0.95)
    assert not engine.evaluate(ctx_bad_geo, resource="api:v3:canvas", action="read", policies=policies).allowed

    ctx_low_trust = RequestContext(subject_id="u3", roles=["user"], geo_country="UA", trust_score=0.5)
    assert not engine.evaluate(ctx_low_trust, resource="api:v3:canvas", action="read", policies=policies).allowed


def test_policy_engine_mfa_requirement():
    engine = ZeroTrustPolicyEngine()
    policies = [
        {
            "id": "pol_mfa",
            "policy_name": "Sensitive Admin MFA",
            "effect": "ALLOW",
            "subject_roles": ["admin"],
            "resource_patterns": ["admin:security:*"],
            "action_patterns": ["*"],
            "require_mfa": True,
            "priority": 10,
        }
    ]

    ctx_no_mfa = RequestContext(subject_id="adm1", roles=["admin"], mfa_authenticated=False)
    res_no_mfa = engine.evaluate(ctx_no_mfa, resource="admin:security:policies", action="write", policies=policies)
    assert not res_no_mfa.allowed
    assert res_no_mfa.required_mfa
    assert "requires MFA" in res_no_mfa.reason

    ctx_mfa_ok = RequestContext(subject_id="adm1", roles=["admin"], mfa_authenticated=True)
    res_mfa_ok = engine.evaluate(ctx_mfa_ok, resource="admin:security:policies", action="write", policies=policies)
    assert res_mfa_ok.allowed


def test_policy_engine_velocity_limit():
    engine = ZeroTrustPolicyEngine()
    policies = [
        {
            "id": "pol_vel",
            "policy_name": "Rate Limited API",
            "effect": "ALLOW",
            "subject_roles": ["*"],
            "resource_patterns": ["*"],
            "action_patterns": ["*"],
            "max_velocity_rpm": 60,
            "priority": 10,
        }
    ]

    ctx_normal = RequestContext(subject_id="u1", roles=["user"], request_count_last_minute=30)
    assert engine.evaluate(ctx_normal, resource="api:test", action="get", policies=policies).allowed

    ctx_flooding = RequestContext(subject_id="u2", roles=["user"], request_count_last_minute=120)
    res_flood = engine.evaluate(ctx_flooding, resource="api:test", action="get", policies=policies)
    assert not res_flood.allowed
    assert "exceeds limit" in res_flood.reason


# ---------------------------------------------------------------------------
# TokenRevocationEngine Tests
# ---------------------------------------------------------------------------

def test_token_revocation_lifecycle():
    engine = TokenRevocationEngine()
    now = datetime.now(timezone.utc)
    future_exp = now + timedelta(hours=2)

    assert not engine.is_token_revoked("jti_test_123")

    revoked = engine.revoke_token(
        token_jti="jti_test_123",
        subject_id="sub_99",
        expires_at=future_exp,
        token_type="access",
        reason="Suspicious activity",
    )
    assert revoked["token_jti"] == "jti_test_123"
    assert revoked["is_revoked"] is True
    assert engine.is_token_revoked("jti_test_123")


def test_token_revocation_expired_cleanup():
    engine = TokenRevocationEngine()
    now = datetime.now(timezone.utc)
    past_exp = now - timedelta(minutes=10)
    future_exp = now + timedelta(hours=1)

    engine.revoke_token("jti_expired", "sub_1", past_exp, reason="old token")
    engine.revoke_token("jti_active", "sub_2", future_exp, reason="active token")

    stats_before = engine.get_revocation_stats()
    assert stats_before["total_entries"] == 2
    assert stats_before["active_revocations"] == 1
    assert stats_before["stale_expired_entries"] == 1

    pruned = engine.cleanup_expired_tokens(now)
    assert pruned == 1

    stats_after = engine.get_revocation_stats()
    assert stats_after["total_entries"] == 1
    assert stats_after["active_revocations"] == 1
    assert stats_after["stale_expired_entries"] == 0
    assert not engine.is_token_revoked("jti_expired")
    assert engine.is_token_revoked("jti_active")


# ---------------------------------------------------------------------------
# AuditTrailEngine Tests
# ---------------------------------------------------------------------------

def test_audit_trail_chain_and_verification():
    engine = AuditTrailEngine()
    engine.clear()

    # Empty chain verification
    assert engine.verify_chain_integrity()["is_valid"] is True

    # Record 3 events
    e1 = engine.record_event(
        workspace_id="ws_1",
        subject_id="sub_1",
        action="login",
        resource="auth:session",
        decision="ALLOWED",
        reason="Valid credentials",
        ip_address="10.0.0.1",
    )
    assert e1["prev_hash"] == AuditTrailEngine.GENESIS_HASH

    e2 = engine.record_event(
        workspace_id="ws_1",
        subject_id="sub_1",
        action="read",
        resource="canvas:node_1",
        decision="ALLOWED",
        reason="Role viewer allowed",
        ip_address="10.0.0.1",
    )
    assert e2["prev_hash"] == e1["current_hash"]

    e3 = engine.record_event(
        workspace_id="ws_1",
        subject_id="sub_2",
        action="delete",
        resource="canvas:node_1",
        decision="DENIED",
        reason="Insufficient role permissions",
        ip_address="203.0.113.4",
    )
    assert e3["prev_hash"] == e2["current_hash"]

    # Verify chain integrity
    integrity = engine.verify_chain_integrity()
    assert integrity["is_valid"] is True
    assert integrity["total_checked"] == 3
    assert integrity["tampered_index"] is None


def test_audit_trail_tamper_detection():
    engine = AuditTrailEngine()
    engine.clear()

    engine.record_event("ws_1", "sub_1", "read", "doc_1", "ALLOWED", "ok", "10.0.0.1")
    engine.record_event("ws_1", "sub_2", "delete", "doc_2", "DENIED", "blocked", "10.0.0.2")
    engine.record_event("ws_1", "sub_1", "write", "doc_3", "ALLOWED", "ok", "10.0.0.1")

    # Get raw logs and simulate malicious modification of index 1
    logs = [dict(log) for log in engine.query_logs(limit=10)]
    logs.reverse()  # query_logs returns reversed (newest first), so restore chronological order

    # Case 1: Tamper with data content
    logs_tampered = [dict(e) for e in logs]
    logs_tampered[1]["decision"] = "ALLOWED"  # Attacker flipped DENIED -> ALLOWED

    res_tamper = engine.verify_chain_integrity(logs_tampered)
    assert res_tamper["is_valid"] is False
    assert res_tamper["tampered_index"] == 1
    assert "data tampering detected" in res_tamper["message"]

    # Case 2: Tamper with broken link (prev_hash corrupted)
    logs_broken_chain = [dict(e) for e in logs]
    logs_broken_chain[2]["prev_hash"] = "badhash000000000000000000000000000000000000000000000000000000000"

    res_broken = engine.verify_chain_integrity(logs_broken_chain)
    assert res_broken["is_valid"] is False
    assert res_broken["tampered_index"] == 2
    assert "Broken chain link" in res_broken["message"]
