# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_theme_config"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Shopify Theme Configurations (DNK-ECOM-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    text
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class ShopifyThemeConfigModel(Base):
    __tablename__ = "shopify_theme_configs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    theme_name = Column(String(255), nullable=False)
    theme_version = Column(String(50), nullable=False, default="1.0.0")
    liquid_version = Column(String(20), nullable=False, default="2024")
    optimization_level = Column(String(20), nullable=False, default="aggressive")
    tree_shaking_enabled = Column(Boolean, nullable=False, default=True)
    minification_enabled = Column(Boolean, nullable=False, default=True)
    tailwind_jit_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    compilations = relationship(
        "ShopifyASTCompilationModel",
        back_populates="theme_config",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_shopify_theme_configs_workspace", "workspace_id"),
        Index("ix_shopify_theme_configs_name", "theme_name"),
    )
