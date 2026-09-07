# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_ast_compilation"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Shopify AST Compilations (DNK-ECOM-003)"
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
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    Index
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class ShopifyASTCompilationModel(Base):
    __tablename__ = "shopify_ast_compilations"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    theme_config_id = Column(
        String(128),
        ForeignKey("shopify_theme_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source_file_path = Column(String(512), nullable=False)
    ast_json = Column(JSON, nullable=False)
    compilation_time_ms = Column(Integer, nullable=False, default=0)
    optimization_stats = Column(JSON, nullable=True, default=dict)
    compiled_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    theme_config = relationship("ShopifyThemeConfigModel", back_populates="compilations")

    __table_args__ = (
        Index("ix_shopify_ast_compilations_theme_config", "theme_config_id"),
        Index("ix_shopify_ast_compilations_file", "source_file_path"),
    )
