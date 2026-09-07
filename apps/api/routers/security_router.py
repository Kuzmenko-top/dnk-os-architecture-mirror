# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_security_router"
# purpose: "FastAPI REST Router for Zero-Trust RBAC, Policy Engine, Token Blacklist & Audit Trail (DNK-SECURITY-001 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from apps.api.services.audit_trail_engine import AuditTrailEngine
from apps.api.services.token_revocation_engine import TokenRevocationEngine
from apps.api.services.zero_trust_policy_engine import (
    PolicyEvaluationResult,
    RequestContext,
    ZeroTrustPolicyEngine,
)

router = APIRouter(prefix="/api/v1/security", tags=["Security Zero-Trust"])

# In-memory singletons for API service layer
policy_engine = ZeroTrustPolicyEngine()
revocation_engine = TokenRevocationEngine()
audit_engine = AuditTrailEngine()

# In-memory storage for policies, subjects, and roles
_policies_db: Dict[str, Dict[str, Any]] = {}
_subjects_db: Dict[str, Dict[str, Any]] = {}
_roles_db: Dict[str, Dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class PolicyCreateRequest(BaseModel):
    policy_name: str = Field(..., description="Human-readable policy name")
    effect: str = Field(..., pattern="^(ALLOW|DENY)$", description="ALLOW or DENY")
    subject_roles: List[str] = Field(default_factory=list)
    resource_patterns: List[str] = Field(default_factory=lambda: ["*"])
    action_patterns: List[str] = Field(default_factory=lambda: ["*"])
    ip_allowlist: List[str] = Field(default_factory=list)
    ip_denylist: List[str] = Field(default_factory=list)
    geo_countries: List[str] = Field(default_factory=list)
    time_window_utc: Optional[str] = Field(None, description="Format HH:MM-HH:MM")
    min_trust_score: float = Field(0.0, ge=0.0, le=1.0)
    require_mfa: bool = False
    max_velocity_rpm: Optional[int] = None
    priority: int = 100
    is_active: bool = True
    workspace_id: Optional[str] = None


class PolicyResponse(PolicyCreateRequest):
    id: str
    created_at: str


class PolicyEvaluateRequest(BaseModel):
    subject_id: str
    roles: List[str] = Field(default_factory=list)
    subject_type: str = "user"
    trust_score: float = 1.0
    mfa_authenticated: bool = False
    ip_address: Optional[str] = None
    geo_country: Optional[str] = None
    user_agent: Optional[str] = None
    velocity_rpm: Optional[int] = None
    workspace_id: Optional[str] = None
    resource: str
    action: str


class TokenRevokeRequest(BaseModel):
    token_jti: str
    subject_id: Optional[str] = "unknown"
    reason: str = "Admin revocation"
    expires_at: Optional[datetime] = None


class SubjectCreateRequest(BaseModel):
    subject_id: str
    subject_type: str = Field("user", pattern="^(user|service|agent)$")
    roles: List[str] = Field(default_factory=list)
    trust_score: float = Field(1.0, ge=0.0, le=1.0)
    mfa_enabled: bool = False
    workspace_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RoleCreateRequest(BaseModel):
    role_key: str
    role_name: str
    permissions: List[str] = Field(default_factory=list)
    parent_role_key: Optional[str] = None
    workspace_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Policy Endpoints
# ---------------------------------------------------------------------------

@router.post("/policies", response_model=PolicyResponse, status_code=status.HTTP_201_CREATED)
def create_policy(payload: PolicyCreateRequest):
    policy_id = f"pol_{uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()
    record = payload.model_dump()
    record["id"] = policy_id
    record["created_at"] = now_iso
    _policies_db[policy_id] = record
    return record


@router.get("/policies", response_model=List[PolicyResponse])
def list_policies(workspace_id: Optional[str] = Query(None)):
    if workspace_id:
        return [p for p in _policies_db.values() if p.get("workspace_id") == workspace_id]
    return list(_policies_db.values())


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
def get_policy(policy_id: str):
    if policy_id not in _policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")
    return _policies_db[policy_id]


@router.delete("/policies/{policy_id}", status_code=status.HTTP_200_OK)
def delete_policy(policy_id: str):
    if policy_id not in _policies_db:
        raise HTTPException(status_code=404, detail="Policy not found")
    del _policies_db[policy_id]
    return {"status": "deleted", "policy_id": policy_id}


@router.post("/evaluate")
def evaluate_access(req: PolicyEvaluateRequest):
    ctx = RequestContext(
        subject_id=req.subject_id,
        subject_type=req.subject_type,
        roles=req.roles,
        trust_score=req.trust_score,
        mfa_authenticated=req.mfa_authenticated,
        ip_address=req.ip_address or "127.0.0.1",
        geo_country=req.geo_country,
        user_agent=req.user_agent,
        request_count_last_minute=req.velocity_rpm or 1,
        attributes={"workspace_id": req.workspace_id} if req.workspace_id else {},
    )
    active_policies = list(_policies_db.values())
    eval_result: PolicyEvaluationResult = policy_engine.evaluate(
        context=ctx,
        resource=req.resource,
        action=req.action,
        policies=active_policies,
    )

    decision_str = "ALLOWED" if eval_result.allowed else "DENIED"
    # Log to audit trail
    audit_engine.record_event(
        workspace_id=req.workspace_id or "ws_default",
        subject_id=req.subject_id,
        action=req.action,
        resource=req.resource,
        decision=decision_str,
        reason=eval_result.reason,
        ip_address=req.ip_address or "127.0.0.1",
        geo_country=req.geo_country,
        user_agent=req.user_agent,
        trust_score=req.trust_score,
        policy_id=eval_result.matched_policy_id,
        extra_context={
            "roles": req.roles,
            "mfa_authenticated": req.mfa_authenticated,
            "policy_name": eval_result.matched_policy_name,
        },
    )

    return {
        "allowed": eval_result.allowed,
        "decision": decision_str,
        "matched_policy_id": eval_result.matched_policy_id,
        "matched_policy_name": eval_result.matched_policy_name,
        "reason": eval_result.reason,
        "required_mfa": eval_result.required_mfa,
    }


# ---------------------------------------------------------------------------
# Token Revocation Endpoints
# ---------------------------------------------------------------------------

@router.post("/tokens/revoke", status_code=status.HTTP_200_OK)
def revoke_token(payload: TokenRevokeRequest):
    expiry = payload.expires_at or (datetime.now(timezone.utc) + timedelta(days=1))
    revocation_engine.revoke_token(
        token_jti=payload.token_jti,
        subject_id=payload.subject_id or "unknown",
        expires_at=expiry,
        reason=payload.reason,
    )
    return {
        "status": "revoked",
        "token_jti": payload.token_jti,
        "subject_id": payload.subject_id,
    }


@router.get("/tokens/is-revoked/{token_jti}")
def check_is_revoked(token_jti: str):
    revoked = revocation_engine.is_token_revoked(token_jti)
    return {"token_jti": token_jti, "is_revoked": revoked}


@router.get("/tokens/stats")
def get_revocation_stats():
    return revocation_engine.get_revocation_stats()


@router.post("/tokens/cleanup")
def cleanup_tokens():
    pruned = revocation_engine.cleanup_expired_tokens()
    return {"status": "cleaned", "pruned_count": pruned}


# ---------------------------------------------------------------------------
# Audit Trail Endpoints
# ---------------------------------------------------------------------------

@router.get("/audit/logs")
def query_audit_logs(
    subject_id: Optional[str] = Query(None),
    decision: Optional[str] = Query(None),
    resource: Optional[str] = Query(None),
    workspace_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    logs = audit_engine.query_logs(
        subject_id=subject_id,
        decision=decision,
        resource=resource,
        workspace_id=workspace_id,
        limit=limit,
    )
    return {"total": len(logs), "logs": logs}


@router.get("/audit/verify-chain")
def verify_audit_chain():
    result = audit_engine.verify_chain_integrity()
    return result


# ---------------------------------------------------------------------------
# Subject & Role Management Endpoints
# ---------------------------------------------------------------------------

@router.post("/subjects", status_code=status.HTTP_201_CREATED)
def create_subject(payload: SubjectCreateRequest):
    record = payload.model_dump()
    record["created_at"] = datetime.now(timezone.utc).isoformat()
    _subjects_db[payload.subject_id] = record
    return record


@router.get("/subjects")
def list_subjects(workspace_id: Optional[str] = Query(None)):
    if workspace_id:
        return [s for s in _subjects_db.values() if s.get("workspace_id") == workspace_id]
    return list(_subjects_db.values())


@router.get("/subjects/{subject_id}")
def get_subject(subject_id: str):
    if subject_id not in _subjects_db:
        raise HTTPException(status_code=404, detail="Subject not found")
    return _subjects_db[subject_id]


@router.post("/roles", status_code=status.HTTP_201_CREATED)
def create_role(payload: RoleCreateRequest):
    record = payload.model_dump()
    record["created_at"] = datetime.now(timezone.utc).isoformat()
    _roles_db[payload.role_key] = record
    return record


@router.get("/roles")
def list_roles():
    return list(_roles_db.values())
