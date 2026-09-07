# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_middleware_tenant_authorization"
# purpose: "Tenant & Workspace authorization middleware / dependency enforcing membership & zero cross-tenant leakage"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from apps.api.services.auth_service import auth_service

security_bearer = HTTPBearer(auto_error=False)


async def require_tenant_and_workspace(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)
) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "UNAUTHORIZED", "message": "Missing Authorization header"}
        )

    token = credentials.credentials
    try:
        payload = auth_service.verify_access_token(token)
    except jwt.PyJWTError as e:
        err_str = str(e)
        if err_str == "TOKEN_EXPIRED":
            raise HTTPException(
                status_code=401,
                detail={"error_code": "TOKEN_EXPIRED", "message": "Token has expired"}
            )
        elif err_str == "TOKEN_REVOKED":
            raise HTTPException(
                status_code=401,
                detail={"error_code": "TOKEN_REVOKED", "message": "Token has been revoked"}
            )
        else:
            raise HTTPException(
                status_code=401,
                detail={"error_code": "INVALID_TOKEN", "message": "Invalid JWT token"}
            )

    user_id = payload.get("sub")
    jwt_tenant_id = payload.get("tenant_id")
    roles = payload.get("roles", ["developer"])

    if not user_id or not jwt_tenant_id:
        raise HTTPException(
            status_code=401,
            detail={"error_code": "INVALID_TOKEN", "message": "Missing claims in token"}
        )

    # Header tenant tampering check
    header_tenant_id = request.headers.get("X-Tenant-Id")
    if header_tenant_id and header_tenant_id != jwt_tenant_id:
        raise HTTPException(
            status_code=403,
            detail={"error_code": "TENANT_MISMATCH", "message": "X-Tenant-Id header does not match JWT tenant claim"}
        )

    # Resolve workspace_id from path params
    workspace_id = request.path_params.get("workspace_id")
    if not workspace_id:
        workspace_id = request.headers.get("X-Workspace-Id")

    # Membership checks
    if not auth_service.check_user_tenant_membership(user_id, jwt_tenant_id):
        raise HTTPException(
            status_code=403,
            detail={"error_code": "WORKSPACE_ACCESS_DENIED", "message": "User does not belong to specified tenant"}
        )

    if workspace_id and not auth_service.check_user_workspace_membership(user_id, jwt_tenant_id, workspace_id):
        raise HTTPException(
            status_code=403,
            detail={"error_code": "WORKSPACE_ACCESS_DENIED", "message": "User does not have access to specified workspace"}
        )

    user_role = auth_service.get_user_workspace_role(user_id, workspace_id or "") or (roles[0] if roles else "viewer")

    return {
        "user_id": user_id,
        "tenant_id": jwt_tenant_id,
        "workspace_id": workspace_id,
        "role": user_role,
        "payload": payload
    }
