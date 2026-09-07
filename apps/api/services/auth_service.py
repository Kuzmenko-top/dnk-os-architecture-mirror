# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_auth_service"
# purpose: "Authentication & JWT Token Validation service for DNK OS User Workspace with HashiCorp Vault dynamic secrets & AuthProvider integration"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import time
import jwt
from typing import Dict, Any, Optional, Set, List
from loguru import logger

from apps.api.services.vault_client import vault_client
from apps.api.services.auth_provider import auth_provider

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "dnk-auth-service"
JWT_AUDIENCE = "dnk-workspace-api"

REVOKED_TOKENS: Set[str] = set()


class AuthService:
    def __init__(
        self,
        vault=vault_client,
        provider=auth_provider,
        algorithm: str = JWT_ALGORITHM
    ):
        self.vault = vault
        self.provider = provider
        self.algorithm = algorithm
        self.issuer = JWT_ISSUER
        self.audience = JWT_AUDIENCE

    @property
    def secret(self) -> str:
        """Dynamically fetch active JWT secret from HashiCorp Vault."""
        return self.vault.get_jwt_secret()

    def generate_test_token(
        self,
        user_id: str = "user_john",
        tenant_id: str = "tenant_corp_a",
        workspace_id: str = "ws_alpha",
        expires_in_seconds: int = 3600,
        jti: Optional[str] = None,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        roles: Optional[list] = None,
        custom_secret: Optional[str] = None
    ) -> str:
        now = int(time.time())
        user_data = self.provider.get_user(user_id) or {}
        user_roles = roles or user_data.get("roles", ["admin"])
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "roles": user_roles,
            "iss": issuer if issuer is not None else self.issuer,
            "aud": audience if audience is not None else self.audience,
            "iat": now,
            "exp": now + expires_in_seconds
        }
        if jti:
            payload["jti"] = jti

        sign_secret = custom_secret or self.secret
        return jwt.encode(payload, sign_secret, algorithm=self.algorithm)

    def revoke_token(self, jti: str):
        REVOKED_TOKENS.add(jti)
        logger.info(f"[AuthService] Token revoked: {jti}")

    def verify_access_token(self, token: str, allow_grace_period: bool = True) -> Dict[str, Any]:
        """
        Verify JWT access token against active Vault secret key (and previous rotated keys during grace period).
        """
        try:
            unverified = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False, "verify_aud": False, "verify_iss": False}
            )
            jti = unverified.get("jti")
            if jti and jti in REVOKED_TOKENS:
                raise jwt.PyJWTError("TOKEN_REVOKED")
        except jwt.PyJWTError as e:
            if str(e) == "TOKEN_REVOKED":
                raise e
            raise jwt.PyJWTError("INVALID_TOKEN")

        valid_secrets = self.vault.get_valid_jwt_secrets() if allow_grace_period else [self.secret]
        last_error: Optional[Exception] = None

        for sec in valid_secrets:
            try:
                payload = jwt.decode(
                    token,
                    sec,
                    algorithms=[self.algorithm],
                    issuer=self.issuer,
                    audience=self.audience
                )
                return payload
            except jwt.ExpiredSignatureError:
                raise jwt.PyJWTError("TOKEN_EXPIRED")
            except jwt.InvalidIssuerError:
                raise jwt.PyJWTError("INVALID_TOKEN")
            except jwt.InvalidAudienceError:
                raise jwt.PyJWTError("INVALID_TOKEN")
            except jwt.PyJWTError as e:
                last_error = e
                continue

        if last_error:
            raise jwt.PyJWTError("INVALID_TOKEN")
        raise jwt.PyJWTError("INVALID_TOKEN")

    def check_user_tenant_membership(self, user_id: str, tenant_id: str) -> bool:
        return self.provider.check_user_tenant_membership(user_id, tenant_id)

    def check_user_workspace_membership(self, user_id: str, tenant_id: str, workspace_id: str) -> bool:
        return self.provider.check_user_workspace_membership(user_id, tenant_id, workspace_id)

    def get_user_workspace_role(self, user_id: str, workspace_id: str) -> Optional[str]:
        return self.provider.get_user_workspace_role(user_id, workspace_id)


auth_service = AuthService()

# Compatibility exports
JWT_SECRET = auth_service.secret
USER_REGISTRY = auth_provider._users

generate_test_token = auth_service.generate_test_token
revoke_token = auth_service.revoke_token
verify_access_token = auth_service.verify_access_token
check_user_tenant_membership = auth_service.check_user_tenant_membership
check_user_workspace_membership = auth_service.check_user_workspace_membership
get_user_workspace_role = auth_service.get_user_workspace_role
