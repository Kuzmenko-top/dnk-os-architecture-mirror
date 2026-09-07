# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/rbac_policy_engine.py"
# purpose: "Dynamic RBAC/ABAC Authorization Policy Engine & Context Evaluator for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from apps.api.db.models.auth_role import AuthRole, RoleScope
from apps.api.db.models.auth_permission import AuthPermission, PermissionAction
from apps.api.db.models.auth_api_key import AuthApiKey
from apps.api.db.models.auth_audit_log import AuthAuditLog, AuditEventType, AuditSeverity


class AuthSubject:
    """Represents an authenticated principal (User or API Key or Agent)."""
    def __init__(
        self,
        subject_id: str,
        tenant_id: str,
        subject_type: str = "user",  # "user", "api_key", "agent"
        roles: Optional[List[str]] = None,
        direct_permissions: Optional[List[str]] = None,
        is_superadmin: bool = False,
        client_ip: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.subject_id = subject_id
        self.tenant_id = tenant_id
        self.subject_type = subject_type
        self.roles = roles or []
        self.direct_permissions = direct_permissions or []
        self.is_superadmin = is_superadmin
        self.client_ip = client_ip
        self.metadata = metadata or {}


class AccessEvaluationContext:
    """Represents contextual metadata for ABAC evaluation."""
    def __init__(
        self,
        target_resource_type: str,
        target_action: str,
        target_resource_id: Optional[str] = None,
        target_tenant_id: Optional[str] = None,
        resource_owner_id: Optional[str] = None,
        request_attributes: Optional[Dict[str, Any]] = None,
    ):
        self.target_resource_type = target_resource_type
        self.target_action = target_action
        self.target_resource_id = target_resource_id
        self.target_tenant_id = target_tenant_id
        self.resource_owner_id = resource_owner_id
        self.request_attributes = request_attributes or {}


class PolicyEvaluationResult:
    """Result of RBAC/ABAC evaluation with detailed decision reasons."""
    def __init__(
        self,
        allowed: bool,
        reason: str,
        matched_permission: Optional[str] = None,
        matched_role: Optional[str] = None,
    ):
        self.allowed = allowed
        self.reason = reason
        self.matched_permission = matched_permission
        self.matched_role = matched_role

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "matched_permission": self.matched_permission,
            "matched_role": self.matched_role,
        }


class RBACPolicyEngine:
    """
    Dynamic RBAC/ABAC Policy Evaluation Engine.
    Evaluates role hierarchies, permission wildcards, tenant boundaries, and fine-grained ABAC rules.
    """

    def __init__(self):
        self._roles: Dict[str, AuthRole] = {}  # role_name -> AuthRole
        self._permissions: Dict[str, AuthPermission] = {}  # permission_code -> AuthPermission
        self._audit_logs: List[AuthAuditLog] = []
        
        # Load default system roles & permissions
        self._bootstrap_system_roles()

    def _bootstrap_system_roles(self) -> None:
        """Seed foundational system roles and hierarchical links."""
        # Permissions
        admin_perm = AuthPermission(code="*", resource="*", action=PermissionAction.ALL, description="Superuser access")
        batch_admin_perm = AuthPermission(code="batch:*", resource="batch", action=PermissionAction.ALL)
        stream_admin_perm = AuthPermission(code="stream:*", resource="stream", action=PermissionAction.ALL)
        observe_admin_perm = AuthPermission(code="observe:*", resource="observe", action=PermissionAction.ALL)
        viewer_perm = AuthPermission(code="*:read", resource="*", action=PermissionAction.READ)

        for p in [admin_perm, batch_admin_perm, stream_admin_perm, observe_admin_perm, viewer_perm]:
            self._permissions[p.code] = p

        # Roles
        super_admin_role = AuthRole(
            name="superadmin",
            display_name="Global Super Administrator",
            scope=RoleScope.SYSTEM,
            permissions=["*"],
        )
        tenant_admin_role = AuthRole(
            name="tenant_admin",
            display_name="Tenant Administrator",
            scope=RoleScope.TENANT,
            permissions=["batch:*", "stream:*", "observe:*", "*:read"],
        )
        developer_role = AuthRole(
            name="developer",
            display_name="Developer",
            scope=RoleScope.TENANT,
            permissions=["batch:read", "batch:execute", "stream:read", "observe:read"],
            inherited_roles=["viewer"],
        )
        viewer_role = AuthRole(
            name="viewer",
            display_name="Read-Only Viewer",
            scope=RoleScope.TENANT,
            permissions=["*:read"],
        )

        for r in [super_admin_role, tenant_admin_role, developer_role, viewer_role]:
            self._roles[r.name] = r

    def register_role(self, role: AuthRole) -> None:
        self._roles[role.name] = role

    def register_permission(self, permission: AuthPermission) -> None:
        self._permissions[permission.code] = permission

    def get_effective_permissions(self, role_names: List[str]) -> Set[str]:
        """Traverse role inheritance hierarchy and compute deduplicated union of permissions."""
        effective_perms: Set[str] = set()
        visited_roles: Set[str] = set()

        def _traverse(rname: str):
            if rname in visited_roles:
                return
            visited_roles.add(rname)
            role = self._roles.get(rname)
            if not role or not role.is_active:
                return

            for p in role.permissions:
                effective_perms.add(p)

            for inherited in role.inherited_roles:
                _traverse(inherited)

        for r in role_names:
            _traverse(r)

        return effective_perms

    def _match_permission_pattern(self, pattern: str, required_permission: str) -> bool:
        """Evaluate permission matching supporting wildcards (* and :*)."""
        if pattern == "*" or pattern == required_permission:
            return True

        regex_pattern = "^" + pattern.replace("*", ".*") + "$"
        return bool(re.match(regex_pattern, required_permission))

    def evaluate(
        self,
        subject: AuthSubject,
        context: AccessEvaluationContext,
    ) -> PolicyEvaluationResult:
        """
        Evaluate full RBAC & ABAC policy rules against subject and context.
        """
        required_permission = f"{context.target_resource_type}:{context.target_action}"

        # 1. Superadmin fast-path
        if subject.is_superadmin:
            return PolicyEvaluationResult(
                allowed=True,
                reason="Access granted via Superadmin privilege",
                matched_permission="*",
                matched_role="superadmin",
            )

        # 2. ABAC: Multi-Tenant Boundary Check
        # A tenant subject CANNOT access resources of a different tenant
        if context.target_tenant_id and context.target_tenant_id != subject.tenant_id:
            self._record_decision_audit(
                subject, context, allowed=False, reason=f"Tenant boundary violation: subject {subject.tenant_id} != resource {context.target_tenant_id}"
            )
            return PolicyEvaluationResult(
                allowed=False,
                reason=f"Cross-tenant access forbidden: {subject.tenant_id} -> {context.target_tenant_id}",
            )

        # 3. RBAC: Compute effective permissions across roles + direct permissions
        effective_perms = self.get_effective_permissions(subject.roles)
        effective_perms.update(subject.direct_permissions)

        matched_perm = None
        for perm in effective_perms:
            if self._match_permission_pattern(perm, required_permission):
                matched_perm = perm
                break

        if not matched_perm:
            self._record_decision_audit(
                subject, context, allowed=False, reason=f"Missing required permission '{required_permission}'"
            )
            return PolicyEvaluationResult(
                allowed=False,
                reason=f"Subject lacks permission '{required_permission}'",
            )

        # 4. ABAC: Resource Ownership Check (if action requires ownership, e.g. edit/delete)
        if context.request_attributes.get("require_ownership", False):
            if context.resource_owner_id and context.resource_owner_id != subject.subject_id:
                # Unless subject has admin role
                if "tenant_admin" not in subject.roles and "superadmin" not in subject.roles:
                    self._record_decision_audit(
                        subject, context, allowed=False, reason="Resource ownership requirement not met"
                    )
                    return PolicyEvaluationResult(
                        allowed=False,
                        reason="Ownership check failed: resource belongs to another user",
                    )

        # 5. ABAC: IP Allowlist Restriction (if defined in metadata)
        allowed_ips = subject.metadata.get("allowed_ips")
        if allowed_ips and subject.client_ip:
            if subject.client_ip not in allowed_ips:
                self._record_decision_audit(
                    subject, context, allowed=False, reason=f"IP {subject.client_ip} not in allowed CIDR/list"
                )
                return PolicyEvaluationResult(
                    allowed=False,
                    reason=f"Client IP '{subject.client_ip}' forbidden by tenant policy",
                )

        # Successful authorization
        return PolicyEvaluationResult(
            allowed=True,
            reason=f"Permission granted via '{matched_perm}'",
            matched_permission=matched_perm,
        )

    def evaluate_api_key(
        self,
        api_key: AuthApiKey,
        context: AccessEvaluationContext,
        client_ip: Optional[str] = None,
    ) -> PolicyEvaluationResult:
        """Evaluate access rights for an API Key subject."""
        if not api_key.is_valid():
            return PolicyEvaluationResult(allowed=False, reason="API Key is inactive or expired")

        subject = AuthSubject(
            subject_id=api_key.id,
            tenant_id=api_key.tenant_id,
            subject_type="api_key",
            direct_permissions=api_key.scopes,
            client_ip=client_ip,
            metadata={"allowed_ips": api_key.allowed_ips},
        )
        return self.evaluate(subject, context)

    def _record_decision_audit(
        self,
        subject: AuthSubject,
        context: AccessEvaluationContext,
        allowed: bool,
        reason: str,
    ) -> None:
        event_type = AuditEventType.ROLE_ASSIGNED if allowed else AuditEventType.PERMISSION_DENIED
        severity = AuditSeverity.INFO if allowed else AuditSeverity.WARNING

        log = AuthAuditLog(
            tenant_id=subject.tenant_id,
            actor_id=subject.subject_id,
            actor_type=subject.subject_type,
            event_type=event_type,
            severity=severity,
            resource=context.target_resource_type,
            action=context.target_action,
            ip_address=subject.client_ip,
            details={
                "reason": reason,
                "target_resource_id": context.target_resource_id,
                "target_tenant_id": context.target_tenant_id,
            },
        )
        log.seal()
        self._audit_logs.append(log)

    def get_audit_logs(self, tenant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        logs = self._audit_logs
        if tenant_id:
            logs = [l for l in logs if l.tenant_id == tenant_id]
        return [l.to_dict() for l in logs]
