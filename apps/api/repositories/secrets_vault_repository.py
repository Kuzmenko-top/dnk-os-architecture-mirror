# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_repositories_secrets_vault_repository"
# purpose: "Async SQLAlchemy 2.0 repository for Secrets Vault with workspace isolation (DNK-USER-WORKSPACE-MVP-002 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
try:
    from apps.api.models.secrets_vault import SecretsVault
except ImportError:
    from models.secrets_vault import SecretsVault

from datetime import datetime, timezone
import uuid
import logging

logger = logging.getLogger(__name__)


class SecretsVaultRepository:
    """
    Async repository for secure secrets management with workspace-level isolation.
    
    All operations are scoped to workspace_id to enforce tenant isolation.
    Soft delete via is_active flag; no hard deletes for audit compliance.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_secret(
        self,
        workspace_id: str,
        secret_name: str,
        encrypted_value: str
    ) -> SecretsVault:
        """
        Store a new encrypted secret for a workspace.
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            secret_name: Human-readable identifier (e.g., 'shopify_api_key')
            encrypted_value: Fernet-encrypted secret (base64-encoded)
        
        Returns:
            Created SecretsVault instance
        
        Raises:
            IntegrityError: If duplicate secret_name exists for workspace
            SQLAlchemyError: On database errors
        """
        secret = SecretsVault(
            id=str(uuid.uuid4()),
            workspace_id=workspace_id,
            secret_name=secret_name,
            encrypted_value=encrypted_value,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        self.session.add(secret)
        await self.session.commit()
        await self.session.refresh(secret)
        
        logger.info(f"Created secret '{secret_name}' for workspace {workspace_id}")
        return secret
    
    async def get_secret(
        self,
        workspace_id: str,
        secret_id: str
    ) -> Optional[SecretsVault]:
        """
        Retrieve an active secret by workspace and secret ID.
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            secret_id: Secret UUID
        
        Returns:
            SecretsVault instance if found and active, None otherwise
        """
        result = await self.session.execute(
            select(SecretsVault).where(
                SecretsVault.workspace_id == workspace_id,
                SecretsVault.id == secret_id,
                SecretsVault.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def get_secret_by_name(
        self,
        workspace_id: str,
        secret_name: str
    ) -> Optional[SecretsVault]:
        """
        Retrieve an active secret by workspace and secret name.
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            secret_name: Human-readable identifier
        
        Returns:
            SecretsVault instance if found and active, None otherwise
        """
        result = await self.session.execute(
            select(SecretsVault).where(
                SecretsVault.workspace_id == workspace_id,
                SecretsVault.secret_name == secret_name,
                SecretsVault.is_active == True
            )
        )
        return result.scalar_one_or_none()
    
    async def list_secrets(
        self,
        workspace_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[SecretsVault]:
        """
        List active secrets for a workspace (metadata only, no values).
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            limit: Max results (default 50)
            offset: Pagination offset
        
        Returns:
            List of SecretsVault instances (encrypted_value included but should not be exposed)
        """
        result = await self.session.execute(
            select(SecretsVault)
            .where(
                SecretsVault.workspace_id == workspace_id,
                SecretsVault.is_active == True
            )
            .order_by(SecretsVault.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def update_secret(
        self,
        workspace_id: str,
        secret_id: str,
        encrypted_value: str
    ) -> bool:
        """
        Update an existing secret's encrypted value.
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            secret_id: Secret UUID
            encrypted_value: New Fernet-encrypted secret
        
        Returns:
            True if updated, False if not found
        """
        stmt = (
            update(SecretsVault)
            .where(
                SecretsVault.workspace_id == workspace_id,
                SecretsVault.id == secret_id,
                SecretsVault.is_active == True
            )
            .values(
                encrypted_value=encrypted_value,
                updated_at=datetime.now(timezone.utc)
            )
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        updated = (result.rowcount or 0) > 0
        if updated:
            logger.info(f"Updated secret {secret_id} for workspace {workspace_id}")
        return updated
    
    async def deactivate_secret(
        self,
        workspace_id: str,
        secret_id: str
    ) -> bool:
        """
        Soft-delete a secret by setting is_active = False.
        
        Args:
            workspace_id: RFC4122 Workspace UUID
            secret_id: Secret UUID
        
        Returns:
            True if deactivated, False if not found
        """
        stmt = (
            update(SecretsVault)
            .where(
                SecretsVault.workspace_id == workspace_id,
                SecretsVault.id == secret_id,
                SecretsVault.is_active == True
            )
            .values(
                is_active=False,
                updated_at=datetime.now(timezone.utc)
            )
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        deactivated = (result.rowcount or 0) > 0
        if deactivated:
            logger.info(f"Deactivated secret {secret_id} for workspace {workspace_id}")
        return deactivated
    
    async def count_secrets(self, workspace_id: str) -> int:
        """
        Count active secrets for a workspace.
        
        Args:
            workspace_id: RFC4122 Workspace UUID
        
        Returns:
            Number of active secrets
        """
        result = await self.session.execute(
            select(func.count()).select_from(SecretsVault).where(
                SecretsVault.workspace_id == workspace_id,
                SecretsVault.is_active == True
            )
        )
        return result.scalar() or 0
