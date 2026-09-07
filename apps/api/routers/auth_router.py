# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/auth_router.py"
# purpose: "REST API Router for DNK-AUTH-001 Multi-Tenant Authentication & Dynamic RBAC Platform."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from pydantic import BaseModel, Field, EmailStr

from apps.api.db.models.auth_tenant import AuthTenant, TenantTier, TenantStatus
from apps.api.db.models.auth_user import AuthUser, UserAccountStatus, UserAuthProvider
from apps.api.db.models.auth_api_key import AuthApiKey, ApiKeyStatus
from apps.api.db.models.auth_role import AuthRole
from apps.api.db.models.auth_session import AuthSession
from apps.api.services.oidc_auth_service import OIDCAuthService
from apps.api.services.rbac_policy_engine import (
    RBACPolicyEngine,
    AuthSubject,
    AccessEvaluationContext,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Multi-Tenant Authentication & Authorization"])

# In-memory singletons / repository for demonstration & runtime persistence
_oidc_service = OIDCAuthService()
_rbac_engine = RBACPolicyEngine()

# Data stores
_tenants_db: Dict[str, AuthTenant] = {
    "tenant_default": AuthTenant(
        id="tenant_default",
        name="Default Organization",
        slug="default-org",
        tier=TenantTier.ENTERPRISE,
    )
}
_users_db: Dict[str, AuthUser] = {}
_api_keys_db: Dict[str, AuthApiKey] = {}
_raw_api_keys: Dict[str, str] = {}  # key_id -> raw_secret (for testing)


# --- Pydantic Schemas ---

class UserRegisterRequest(BaseModel):
    tenant_id: str = "tenant_default"
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    roles: List[str] = Field(default_factory=lambda: ["viewer"])


class UserLoginRequest(BaseModel):
    tenant_id: str = "tenant_default"
    email: str
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    tenant_id: str
    roles: List[str]


class CreateApiKeyRequest(BaseModel):
    tenant_id: str = "tenant_default"
    name: str
    scopes: List[str] = Field(default_factory=lambda: ["batch:read", "stream:read"])
    rate_limit_rpm: int = 600
    allowed_ips: List[str] = Field(default_factory=list)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    secret_key: Optional[str] = None
    tenant_id: str
    scopes: List[str]
    created_at: str


class RBACCheckRequest(BaseModel):
    resource_type: str
    action: str
    target_resource_id: Optional[str] = None
    target_tenant_id: Optional[str] = None
    resource_owner_id: Optional[str] = None


class RBACCheckResponse(BaseModel):
    allowed: bool
    reason: str
    matched_permission: Optional[str] = None
    matched_role: Optional[str] = None


# --- FastAPI Dependency Providers ---

def get_current_principal(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
) -> AuthSubject:
    """Extract authenticated Subject from Bearer JWT or X-API-Key."""
    client_ip = request.client.host if request.client else "127.0.0.1"

    # 1. Check API Key Header
    if x_api_key:
        matched_key = None
        for key in _api_keys_db.values():
            if key.verify_key(x_api_key):
                matched_key = key
                break

        if not matched_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

        if not matched_key.is_valid():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API Key expired or inactive")

        # Update last used
        matched_key.record_usage(client_ip)

        return AuthSubject(
            subject_id=matched_key.id,
            tenant_id=matched_key.tenant_id,
            subject_type="api_key",
            direct_permissions=matched_key.scopes,
            client_ip=client_ip,
            metadata={"allowed_ips": matched_key.allowed_ips},
        )

    # 2. Check Bearer Token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = _oidc_service.verify_token(token)
            user_id = payload["sub"]
            user = _users_db.get(user_id)
            if not user or not user.is_active():
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or not found")

            return AuthSubject(
                subject_id=user.id,
                tenant_id=user.tenant_id,
                subject_type="user",
                roles=user.roles,
                direct_permissions=user.direct_permissions,
                is_superadmin=user.is_superadmin,
                client_ip=client_ip,
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid or expired token: {str(e)}")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing Authorization Bearer header or X-API-Key header",
    )


def require_permission(resource_type: str, action: str):
    """FastAPI Dependency for enforcing RBAC/ABAC permissions."""
    def _dependency(subject: AuthSubject = Depends(get_current_principal)) -> AuthSubject:
        context = AccessEvaluationContext(
            target_resource_type=resource_type,
            target_action=action,
            target_tenant_id=subject.tenant_id,
        )
        decision = _rbac_engine.evaluate(subject, context)
        if not decision.allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {decision.reason}",
            )
        return subject
    return _dependency


# --- Router Endpoints ---

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(req: UserRegisterRequest):
    """Register a new user inside a tenant organization."""
    if req.tenant_id not in _tenants_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant does not exist")

    try:
        user = _oidc_service.register_user(
            tenant_id=req.tenant_id,
            email=req.email,
            display_name=req.display_name or req.email.split("@")[0],
            password=req.password,
            roles=req.roles,
            provider=UserAuthProvider.LOCAL,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    _users_db[user.id] = user

    return {
        "status": "success",
        "user_id": user.id,
        "email": user.email,
        "tenant_id": user.tenant_id,
        "roles": user.roles,
    }


@router.post("/login", response_model=TokenResponse)
def login_user(req: UserLoginRequest, request: Request):
    """Authenticate with email & password, returning JWT access & refresh tokens."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent", "unknown")

    try:
        access_token, refresh_token, session = _oidc_service.authenticate_local_user(
            tenant_id=req.tenant_id,
            email=req.email,
            password=req.password,
            ip_address=client_ip,
            user_agent=user_agent,
        )
        user = _oidc_service.get_user_by_id(session.user_id)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=_oidc_service.access_token_ttl_seconds,
            user_id=user.id if user else session.user_id,
            tenant_id=req.tenant_id,
            roles=user.roles if user else [],
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ve))


@router.post("/refresh", response_model=TokenResponse)
def refresh_token_endpoint(req: TokenRefreshRequest):
    """Rotate and refresh access token using a valid refresh token."""
    try:
        new_access_token, new_refresh_token = _oidc_service.refresh_access_token(
            refresh_token=req.refresh_token
        )
        payload = _oidc_service._verify_jwt(new_access_token)
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=_oidc_service.access_token_ttl_seconds,
            user_id=payload["sub"],
            tenant_id=payload["tenant_id"],
            roles=payload.get("roles", []),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/logout")
def logout_endpoint(
    req: TokenRefreshRequest,
    principal: AuthSubject = Depends(get_current_principal),
):
    """Revoke refresh token and terminate active session."""
    _oidc_service.revoke_token(req.refresh_token, reason="user_logout")
    return {"status": "success", "message": "Logged out and tokens revoked"}


@router.get("/me")
def get_current_user_profile(principal: AuthSubject = Depends(get_current_principal)):
    """Return authenticated subject identity and permissions."""
    return {
        "subject_id": principal.subject_id,
        "tenant_id": principal.tenant_id,
        "subject_type": principal.subject_type,
        "roles": principal.roles,
        "direct_permissions": principal.direct_permissions,
        "is_superadmin": principal.is_superadmin,
    }


@router.get("/jwks.json")
def get_jwks():
    """Return public JSON Web Key Set for verifying JWT tokens."""
    return _oidc_service.get_jwks()


@router.post("/rotate-keys")
def rotate_signing_keys(principal: AuthSubject = Depends(get_current_principal)):
    """Admin-triggered active cryptographic signing key rotation."""
    if not principal.is_superadmin and "tenant_admin" not in principal.roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required to rotate keys")

    new_kid = _oidc_service.rotate_key()
    return {"status": "success", "active_kid": new_kid, "rotated_at": datetime.now(timezone.utc).isoformat()}


@router.post("/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    req: CreateApiKeyRequest,
    principal: AuthSubject = Depends(get_current_principal),
):
    """Generate a new secure API Key with scoped access."""
    if principal.tenant_id != req.tenant_id and not principal.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create API key for another tenant")

    raw_secret, prefix, key_hash = AuthApiKey.generate_key_pair()
    api_key = AuthApiKey(
        name=req.name,
        tenant_id=req.tenant_id,
        user_id=principal.subject_id if principal.subject_type == "user" else None,
        prefix=prefix,
        key_hash=key_hash,
        scopes=req.scopes,
        rate_limit_rpm=req.rate_limit_rpm,
        allowed_ips=req.allowed_ips,
    )
    _api_keys_db[api_key.id] = api_key
    _raw_api_keys[api_key.id] = raw_secret

    return ApiKeyResponse(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        secret_key=raw_secret,  # Only shown once on creation
        tenant_id=api_key.tenant_id,
        scopes=api_key.scopes,
        created_at=api_key.created_at.isoformat(),
    )


@router.get("/api-keys")
def list_api_keys(principal: AuthSubject = Depends(get_current_principal)):
    """List all API keys belonging to the current tenant."""
    keys = [k.to_dict() for k in _api_keys_db.values() if k.tenant_id == principal.tenant_id]
    return {"status": "success", "count": len(keys), "api_keys": keys}


@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: str,
    principal: AuthSubject = Depends(get_current_principal),
):
    """Revoke an API Key."""
    key = _api_keys_db.get(key_id)
    if not key or (key.tenant_id != principal.tenant_id and not principal.is_superadmin):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API Key not found")

    key.revoke()
    return {"status": "success", "message": f"API Key {key_id} revoked"}


@router.post("/rbac/check", response_model=RBACCheckResponse)
def check_rbac_permission(
    req: RBACCheckRequest,
    principal: AuthSubject = Depends(get_current_principal),
):
    """Dynamically evaluate RBAC & ABAC policy permissions for current subject."""
    context = AccessEvaluationContext(
        target_resource_type=req.resource_type,
        target_action=req.action,
        target_resource_id=req.target_resource_id,
        target_tenant_id=req.target_tenant_id or principal.tenant_id,
        resource_owner_id=req.resource_owner_id,
    )
    decision = _rbac_engine.evaluate(principal, context)
    return RBACCheckResponse(
        allowed=decision.allowed,
        reason=decision.reason,
        matched_permission=decision.matched_permission,
        matched_role=decision.matched_role,
    )


@router.get("/audit/logs")
def get_security_audit_logs(principal: AuthSubject = Depends(get_current_principal)):
    """Retrieve security audit events for current tenant."""
    tenant_filter = None if principal.is_superadmin else principal.tenant_id
    logs = _rbac_engine.get_audit_logs(tenant_id=tenant_filter)
    return {"status": "success", "count": len(logs), "audit_logs": logs}
