# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_admin_security"
# purpose: "FastAPI REST endpoints for Admin Security & Vault operations, secret rotation, and IAM user registry"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status, Header
from loguru import logger

from apps.api.services.vault_client import vault_client
from apps.api.services.auth_provider import auth_provider
from apps.api.services.auth_service import auth_service
from apps.api.middleware.tenant_authorization import require_tenant_and_workspace

router = APIRouter(prefix="/api/v1/admin/security", tags=["Admin Security & Vault"])


class RotateSecretResponse(BaseModel):
    status: str
    message: str
    rotated_at: int
    secret_path: str
    vault_mode: str


class RegisterUserRequest(BaseModel):
    user_id: str
    tenant_id: str
    email: Optional[str] = None
    workspaces: List[str] = Field(default_factory=list)
    roles: List[str] = Field(default_factory=lambda: ["developer"])


class UserResponse(BaseModel):
    user_id: str
    tenant_id: str
    email: str
    workspaces: List[str]
    roles: List[str]
    is_active: bool


def require_admin_role(auth_context: Dict[str, Any] = Depends(require_tenant_and_workspace)) -> Dict[str, Any]:
    roles = auth_context.get("payload", {}).get("roles", [])
    if "admin" not in roles and auth_context.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "ADMIN_ROLE_REQUIRED", "message": "Operation requires admin privileges"}
        )
    return auth_context


@router.get("/vault-status")
async def get_vault_status(auth_context: Dict[str, Any] = Depends(require_admin_role)):
    """
    Get HashiCorp Vault connectivity and operating mode.
    """
    status_info = vault_client.get_status()
    return {
        "status": "success",
        "data": status_info
    }


@router.post("/rotate-jwt-secret", response_model=RotateSecretResponse)
async def rotate_jwt_secret(
    path: str = "secret/data/jwt",
    auth_context: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Rotate active JWT secret in HashiCorp Vault.
    Requires admin privileges.
    """
    user_id = auth_context.get("user_id")
    logger.info(f"[SecurityAudit] Admin {user_id} triggered JWT secret rotation for path {path}")
    
    new_secret = vault_client.rotate_jwt_secret(path)
    status_info = vault_client.get_status()
    
    return RotateSecretResponse(
        status="success",
        message="JWT secret successfully rotated in Vault",
        rotated_at=int(time.time()),
        secret_path=path,
        vault_mode=status_info.get("mode", "in_memory_fallback")
    )


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    tenant_id: Optional[str] = None,
    auth_context: Dict[str, Any] = Depends(require_admin_role)
):
    """
    List registered IAM users. Defaults to admin's tenant.
    """
    target_tenant = tenant_id or auth_context.get("tenant_id")
    users = auth_provider.list_users(tenant_id=target_tenant)
    return [UserResponse(**u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterUserRequest,
    auth_context: Dict[str, Any] = Depends(require_admin_role)
):
    """
    Register a new IAM user with tenant and workspace bindings.
    """
    caller_tenant = auth_context.get("tenant_id")
    if body.tenant_id != caller_tenant and caller_tenant != "tenant_corp_a":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "TENANT_MISMATCH", "message": "Cannot register user outside authorized tenant"}
        )

    user = auth_provider.register_user(
        user_id=body.user_id,
        tenant_id=body.tenant_id,
        workspaces=body.workspaces,
        roles=body.roles,
        email=body.email
    )
    return UserResponse(**user)
