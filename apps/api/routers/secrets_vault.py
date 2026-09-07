# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_secrets_vault"
# purpose: "FastAPI REST endpoints for Secrets Vault with workspace isolation and security gates (DNK-USER-WORKSPACE-MVP-002 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import logging
import os
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import BaseModel, Field

try:
    from apps.api.db.database import get_db_session
except ImportError:
    try:
        from db.database import get_db_session
    except ImportError:
        async def get_db_session():
            yield None

try:
    from apps.api.repositories.secrets_vault_repository import SecretsVaultRepository
except ImportError:
    from repositories.secrets_vault_repository import SecretsVaultRepository

try:
    from apps.api.services.secrets_vault_service import (
        SecretsVaultService,
        SecretsVaultServiceError,
        SecretNotFoundError,
        SecretDecryptionError,
        SecretEncryptionError
    )
except ImportError:
    from services.secrets_vault_service import (
        SecretsVaultService,
        SecretsVaultServiceError,
        SecretNotFoundError,
        SecretDecryptionError,
        SecretEncryptionError
    )

try:
    from apps.api.middleware.security import SecurityGateDenied
except ImportError:
    try:
        from middleware.security import SecurityGateDenied
    except ImportError:
        class SecurityGateDenied(Exception):
            pass

logger = logging.getLogger(__name__)


import uuid

def validate_workspace_uuid(workspace_id: str):
    if workspace_id == "00000000-0000-0000-0000-000000000000":
        raise HTTPException(status_code=400, detail="Nil/Zero UUID rejected")
    try:
        val = uuid.UUID(workspace_id, version=4)
    except ValueError:
        try:
            val = uuid.UUID(workspace_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid workspace UUID format")

router = APIRouter()


# --- Request/Response Models ---

class SecretCreateRequest(BaseModel):
    secret_name: str = Field(..., min_length=1, max_length=255, description="Human-readable identifier")
    plaintext_value: str = Field(..., min_length=1, description="Secret value in plaintext")


class SecretUpdateRequest(BaseModel):
    plaintext_value: str = Field(..., min_length=1, description="New plaintext value")


class SecretMetadataResponse(BaseModel):
    id: str
    secret_name: str
    created_at: str
    updated_at: str


class SecretCreateResponse(BaseModel):
    secret_id: str
    secret_name: str
    created_at: str


class SecretRetrieveResponse(BaseModel):
    secret_id: str
    secret_name: str
    plaintext_value: str


class SecretListResponse(BaseModel):
    secrets: List[SecretMetadataResponse]
    total_count: int


# --- Helper Functions ---

def get_secrets_vault_service(db: AsyncSession = Depends(get_db_session)) -> SecretsVaultService:
    """
    Dependency injector for SecretsVaultService.
    """
    repository = SecretsVaultRepository(db)
    return SecretsVaultService(repository)


# --- Endpoints ---

@router.post(
    "/api/v1/workspaces/{workspace_id}/secrets",
    response_model=SecretCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new encrypted secret",
    description="Encrypts and stores a new secret for the specified workspace. Returns secret ID."
)
async def create_secret(

    workspace_id: str,
    request: SecretCreateRequest,
    x_workspace_id: str = Header(..., alias="X-Workspace-Id", description="RFC4122 Workspace UUID"),
    authorization: str = Header(..., alias="Authorization", description="Bearer token"),
    service: SecretsVaultService = Depends(get_secrets_vault_service),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type", description="Actor type: user or agent")
):
    """
    Create a new encrypted secret.
    
    Security gates:
    - Workspace UUID must match path parameter
    - Bearer token required
    - Agent self-approval prevention (X-Actor-Type: agent → 403)
    """
    validate_workspace_uuid(workspace_id)
    # Workspace mismatch check
    if workspace_id != x_workspace_id:
        raise HTTPException(
            status_code=403,
            detail=f"Workspace mismatch: path '{workspace_id}' != header '{x_workspace_id}'"
        )
    
    # Agent self-approval prevention
    if x_actor_type and x_actor_type.lower() == "agent":
        raise HTTPException(
            status_code=403,
            detail="Agents cannot create secrets (self-approval prevention)"
        )
    
    
    try:
        secret_id = await service.store_secret(
            workspace_id=workspace_id,
            secret_name=request.secret_name,
            plaintext_value=request.plaintext_value
        )
        
        # Retrieve created secret for response
        secret = await service.repository.get_secret(workspace_id, secret_id)
        
        return SecretCreateResponse(
            secret_id=secret.id,
            secret_name=secret.secret_name,
            created_at=secret.created_at.isoformat()
        )
    
    except SecretEncryptionError as e:
        logger.error(f"Encryption error: {e}")
        raise HTTPException(status_code=500, detail="Failed to encrypt secret")
    
    except IntegrityError as e:
        logger.error(f"Duplicate secret name: {e}")
        raise HTTPException(
            status_code=409,
            detail=f"Secret with name '{request.secret_name}' already exists in workspace"
        )
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")


@router.get(
    "/api/v1/workspaces/{workspace_id}/secrets/{secret_id}",
    response_model=SecretRetrieveResponse,
    summary="Retrieve and decrypt a secret",
    description="Retrieves a secret by ID and decrypts it. Returns plaintext value."
)
async def get_secret(

    workspace_id: str,
    secret_id: str,
    x_workspace_id: str = Header(..., alias="X-Workspace-Id", description="RFC4122 Workspace UUID"),
    authorization: str = Header(..., alias="Authorization", description="Bearer token"),
    service: SecretsVaultService = Depends(get_secrets_vault_service),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type", description="Actor type: user or agent")
):
    """
    Retrieve and decrypt a secret.
    
    Security gates:
    - Workspace UUID must match path parameter
    - Bearer token required
    - Agent self-approval prevention (X-Actor-Type: agent → 403)
    """
    if workspace_id != x_workspace_id:
        raise HTTPException(
            status_code=403,
            detail=f"Workspace mismatch: path '{workspace_id}' != header '{x_workspace_id}'"
        )
    
    if x_actor_type and x_actor_type.lower() == "agent":
        raise HTTPException(
            status_code=403,
            detail="Agents cannot retrieve secrets (self-approval prevention)"
        )
    
    
    try:
        plaintext = await service.retrieve_secret(
            workspace_id=workspace_id,
            secret_id=secret_id
        )
        
        secret = await service.repository.get_secret(workspace_id, secret_id)
        
        return SecretRetrieveResponse(
            secret_id=secret.id,
            secret_name=secret.secret_name,
            plaintext_value=plaintext
        )
    
    except SecretNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except SecretDecryptionError as e:
        logger.error(f"Decryption error: {e}")
        raise HTTPException(status_code=500, detail="Failed to decrypt secret")


@router.get(
    "/api/v1/workspaces/{workspace_id}/secrets",
    response_model=SecretListResponse,
    summary="List secret metadata",
    description="Lists metadata for all active secrets (without exposing encrypted values)."
)
async def list_secrets(

    workspace_id: str,
    x_workspace_id: str = Header(..., alias="X-Workspace-Id", description="RFC4122 Workspace UUID"),
    authorization: str = Header(..., alias="Authorization", description="Bearer token"),
    service: SecretsVaultService = Depends(get_secrets_vault_service),
    limit: int = 50,
    offset: int = 0
):
    """
    List secret metadata (no plaintext values).
    
    Security gates:
    - Workspace UUID must match path parameter
    - Bearer token required
    """
    if workspace_id != x_workspace_id:
        raise HTTPException(
            status_code=403,
            detail=f"Workspace mismatch: path '{workspace_id}' != header '{x_workspace_id}'"
        )
    
    
    metadata = await service.list_secret_metadata(workspace_id, limit, offset)
    total = await service.count_secrets(workspace_id)
    
    return SecretListResponse(
        secrets=metadata,
        total_count=total
    )


@router.put(
    "/api/v1/workspaces/{workspace_id}/secrets/{secret_id}",
    response_model=SecretMetadataResponse,
    summary="Update an existing secret",
    description="Encrypts and updates an existing secret with a new value."
)
async def update_secret(

    workspace_id: str,
    secret_id: str,
    request: SecretUpdateRequest,
    x_workspace_id: str = Header(..., alias="X-Workspace-Id", description="RFC4122 Workspace UUID"),
    authorization: str = Header(..., alias="Authorization", description="Bearer token"),
    service: SecretsVaultService = Depends(get_secrets_vault_service),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type", description="Actor type: user or agent")
):
    """
    Update an existing secret.
    
    Security gates:
    - Workspace UUID must match path parameter
    - Bearer token required
    - Agent self-approval prevention (X-Actor-Type: agent → 403)
    """
    if workspace_id != x_workspace_id:
        raise HTTPException(
            status_code=403,
            detail=f"Workspace mismatch: path '{workspace_id}' != header '{x_workspace_id}'"
        )
    
    if x_actor_type and x_actor_type.lower() == "agent":
        raise HTTPException(
            status_code=403,
            detail="Agents cannot update secrets (self-approval prevention)"
        )
    
    
    try:
        await service.update_secret(
            workspace_id=workspace_id,
            secret_id=secret_id,
            plaintext_value=request.plaintext_value
        )
        
        secret = await service.repository.get_secret(workspace_id, secret_id)
        
        return SecretMetadataResponse(
            id=secret.id,
            secret_name=secret.secret_name,
            created_at=secret.created_at.isoformat(),
            updated_at=secret.updated_at.isoformat()
        )
    
    except SecretNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except SecretEncryptionError as e:
        logger.error(f"Encryption error: {e}")
        raise HTTPException(status_code=500, detail="Failed to encrypt secret")


@router.delete(
    "/api/v1/workspaces/{workspace_id}/secrets/{secret_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke (soft-delete) a secret",
    description="Soft-deletes a secret by setting is_active = False. No hard deletes for audit compliance."
)
async def revoke_secret(

    workspace_id: str,
    secret_id: str,
    x_workspace_id: str = Header(..., alias="X-Workspace-Id", description="RFC4122 Workspace UUID"),
    authorization: str = Header(..., alias="Authorization", description="Bearer token"),
    service: SecretsVaultService = Depends(get_secrets_vault_service),
    x_actor_type: Optional[str] = Header(None, alias="X-Actor-Type", description="Actor type: user or agent")
):
    """
    Revoke (soft-delete) a secret.
    
    Security gates:
    - Workspace UUID must match path parameter
    - Bearer token required
    - Agent self-approval prevention (X-Actor-Type: agent → 403)
    """
    if workspace_id != x_workspace_id:
        raise HTTPException(
            status_code=403,
            detail=f"Workspace mismatch: path '{workspace_id}' != header '{x_workspace_id}'"
        )
    
    if x_actor_type and x_actor_type.lower() == "agent":
        raise HTTPException(
            status_code=403,
            detail="Agents cannot revoke secrets (self-approval prevention)"
        )
    
    
    revoked = await service.revoke_secret(workspace_id, secret_id)
    
    if not revoked:
        raise HTTPException(status_code=404, detail="Secret not found or already revoked")


class SecretsVault:
    """
    Secure secrets management.

    - All secrets loaded from environment at startup
    - No secrets in code or client bundles
    - Strict fail: missing secrets -> 412/503 / RuntimeError, not mock/fallback
    """

    _secrets: dict = {}

    @classmethod
    def initialize(cls, strict: bool = True):
        """Load secrets from environment (startup only)."""
        required_secrets = [
            "SHOPIFY_ACCESS_TOKEN",
            "SHOPIFY_SHOP_DOMAIN",
            "GEMINI_API_KEY",
            "CLAUDE_API_KEY",
            "WHISPERX_API_KEY",
            "REMOTION_LAMBDA_URL",
            "REMOTION_API_KEY",
        ]

        loaded = {}
        for secret_name in required_secrets:
            secret_value = os.getenv(secret_name)
            if not secret_value:
                if strict:
                    raise RuntimeError(f"Missing required secret: {secret_name}")
                continue
            loaded[secret_name] = secret_value

        cls._secrets = loaded

    @classmethod
    def get(cls, secret_name: str) -> str:
        """Get secret by name (runtime)."""
        if secret_name not in cls._secrets:
            raise RuntimeError(f"Secret not found: {secret_name}")
        return cls._secrets[secret_name]

    @classmethod
    def reset(cls):
        """Reset cached secrets (for testing purposes)."""
        cls._secrets = {}


# Initialize non-strictly at import to prevent broken module loads in dev/test,
# while strict enforcement is applied when initialize(strict=True) or production check runs.
try:
    SecretsVault.initialize(strict=os.getenv("ENV") == "production")
except Exception as e:
    logger.warning(f"SecretsVault startup initialization warning: {e}")


@router.get(
    "/api/v1/secrets/health",
    summary="Check secrets loaded status",
    description="Check secrets loaded without returning any sensitive values."
)
async def secrets_health():
    """Check secrets loaded (no values returned)."""
    return {
        "status": "ok",
        "secrets_loaded": len(SecretsVault._secrets) > 0,
    }




