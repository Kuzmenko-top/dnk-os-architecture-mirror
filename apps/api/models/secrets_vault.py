# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_models_secrets_vault"
# purpose: "SQLAlchemy 2.0 ORM model for Secrets Vault table (DNK-USER-WORKSPACE-MVP-002 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from sqlalchemy import String, Text, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, declarative_base
from datetime import datetime, timezone
import uuid

Base = declarative_base()


class SecretsVault(Base):
    """
    Secure storage for encrypted workspace secrets (API keys, tokens, credentials).
    
    Security properties:
    - Row-level isolation by workspace_id
    - Encrypted values only (plaintext never stored)
    - Soft delete via is_active flag
    - Audit trail via created_at/updated_at
    """
    
    __tablename__ = "secrets_vault"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="RFC4122 Workspace UUID for tenant isolation"
    )
    
    secret_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable identifier (e.g., 'shopify_api_key', 'stripe_secret')"
    )
    
    encrypted_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Fernet-encrypted secret value (base64-encoded)"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Soft delete flag; False = revoked"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        comment="UTC timestamp of creation"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment="UTC timestamp of last update"
    )
    
    # Composite index for efficient workspace-scoped queries
    __table_args__ = (
        Index("ix_secrets_vault_workspace_active", "workspace_id", "is_active"),
        {"comment": "Secure vault for workspace-level encrypted secrets"},
    )
    
    def __repr__(self) -> str:
        return f"<SecretsVault(id={self.id}, workspace={self.workspace_id}, name={self.secret_name}, active={self.is_active})>"
