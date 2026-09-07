# --- DNK-MRH-HEADER ---
# mrh_id: "tests/auth/test_rbac_policy_engine.py"
# purpose: "Unit tests for DNK-AUTH-001 Dynamic RBAC/ABAC Authorization Policy Engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.rbac_policy_engine import (
    RBACPolicyEngine,
    AuthSubject,
    AccessEvaluationContext,
)
from apps.api.db.models.auth_api_key import AuthApiKey
from apps.api.db.models.auth_role import AuthRole, RoleScope


def test_rbac_superadmin_access():
    engine = RBACPolicyEngine()
    subject = AuthSubject(
        subject_id="usr_super",
        tenant_id="tenant_system",
        is_superadmin=True
    )
    context = AccessEvaluationContext(
        target_resource_type="security",
        target_action="purge_audit_logs",
        target_tenant_id="tenant_other"
    )
    result = engine.evaluate(subject, context)
    assert result.allowed is True
    assert "Superadmin" in result.reason


def test_rbac_role_hierarchy_and_wildcard_matching():
    engine = RBACPolicyEngine()
    
    # Developer inherits 'viewer' (*:read) and has direct batch:read, batch:execute, stream:read
    dev_subject = AuthSubject(
        subject_id="usr_dev_1",
        tenant_id="tenant_acme",
        roles=["developer"]
    )
    
    # Should be allowed to read batch jobs
    ctx_read_batch = AccessEvaluationContext(
        target_resource_type="batch",
        target_action="read",
        target_tenant_id="tenant_acme"
    )
    res = engine.evaluate(dev_subject, ctx_read_batch)
    assert res.allowed is True
    
    # Should be allowed to execute batch
    ctx_exec_batch = AccessEvaluationContext(
        target_resource_type="batch",
        target_action="execute",
        target_tenant_id="tenant_acme"
    )
    res = engine.evaluate(dev_subject, ctx_exec_batch)
    assert res.allowed is True
    
    # Inherited from viewer: observe:read
    ctx_read_observe = AccessEvaluationContext(
        target_resource_type="observe",
        target_action="read",
        target_tenant_id="tenant_acme"
    )
    res = engine.evaluate(dev_subject, ctx_read_observe)
    assert res.allowed is True
    
    # Should NOT be allowed to delete resources
    ctx_delete_batch = AccessEvaluationContext(
        target_resource_type="batch",
        target_action="delete",
        target_tenant_id="tenant_acme"
    )
    res = engine.evaluate(dev_subject, ctx_delete_batch)
    assert res.allowed is False


def test_abac_cross_tenant_isolation_boundary():
    engine = RBACPolicyEngine()
    tenant_admin_subject = AuthSubject(
        subject_id="usr_admin_acme",
        tenant_id="tenant_acme",
        roles=["tenant_admin"]
    )
    
    # Attempting to access resources of tenant_beta
    cross_tenant_ctx = AccessEvaluationContext(
        target_resource_type="batch",
        target_action="read",
        target_tenant_id="tenant_beta"
    )
    res = engine.evaluate(tenant_admin_subject, cross_tenant_ctx)
    assert res.allowed is False
    assert "Cross-tenant access forbidden" in res.reason


def test_abac_resource_ownership_enforcement():
    engine = RBACPolicyEngine()
    user_subject = AuthSubject(
        subject_id="usr_alice",
        tenant_id="tenant_acme",
        roles=["viewer"],
        direct_permissions=["document:delete"]
    )
    
    # Action requiring ownership on resource owned by bob
    ctx_delete_bob = AccessEvaluationContext(
        target_resource_type="document",
        target_action="delete",
        target_tenant_id="tenant_acme",
        resource_owner_id="usr_bob",
        request_attributes={"require_ownership": True}
    )
    res = engine.evaluate(user_subject, ctx_delete_bob)
    assert res.allowed is False
    assert "Ownership check failed" in res.reason
    
    # Action on resource owned by alice
    ctx_delete_alice = AccessEvaluationContext(
        target_resource_type="document",
        target_action="delete",
        target_tenant_id="tenant_acme",
        resource_owner_id="usr_alice",
        request_attributes={"require_ownership": True}
    )
    res = engine.evaluate(user_subject, ctx_delete_alice)
    assert res.allowed is True


def test_api_key_evaluation_and_ip_allowlist():
    engine = RBACPolicyEngine()
    _, prefix, key_hash = AuthApiKey.generate_key_pair()
    
    api_key = AuthApiKey(
        name="Production Ingestion Key",
        tenant_id="tenant_gamma",
        prefix=prefix,
        key_hash=key_hash,
        scopes=["stream:*", "batch:read"],
        allowed_ips=["192.168.1.50"]
    )
    
    # Request from allowed IP
    ctx_stream = AccessEvaluationContext(
        target_resource_type="stream",
        target_action="publish",
        target_tenant_id="tenant_gamma"
    )
    res = engine.evaluate_api_key(api_key, ctx_stream, client_ip="192.168.1.50")
    assert res.allowed is True
    
    # Request from unauthorized IP
    res_ip_blocked = engine.evaluate_api_key(api_key, ctx_stream, client_ip="10.0.0.99")
    assert res_ip_blocked.allowed is False
    assert "forbidden by tenant policy" in res_ip_blocked.reason
