# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_component"
# purpose: "SQLAlchemy ORM model for Canvas Generative UI Component entity (DNK-CANVAS-002 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    JSON,
    Text,
    ForeignKey,
    Index,
    CheckConstraint
)

from apps.api.db.models.workspace import Base


class CanvasComponentModel(Base):
    __tablename__ = "canvas_components"

    id = Column(String(128), primary_key=True, nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    framework = Column(String(32), nullable=False, default="react")  # react, vue, svelte, html
    category = Column(String(64), nullable=False, default="general")
    source_code = Column(Text, nullable=False)
    props_schema = Column(JSON, nullable=True, default=dict)
    default_props = Column(JSON, nullable=True, default=dict)
    preview_image_url = Column(String(1024), nullable=True)
    is_generative = Column(Integer, nullable=False, default=1)  # Generated via AI
    ai_prompt = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="published")
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("framework IN ('react', 'vue', 'svelte', 'html', 'tailwind')", name="check_canvas_component_framework"),
        CheckConstraint("status IN ('draft', 'published', 'deprecated')", name="check_canvas_component_status"),
        Index("ix_canvas_components_workspace_cat", "workspace_id", "category"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "framework": self.framework,
            "category": self.category,
            "source_code": self.source_code,
            "props_schema": self.props_schema or {},
            "default_props": self.default_props or {},
            "preview_image_url": self.preview_image_url,
            "is_generative": bool(self.is_generative),
            "ai_prompt": self.ai_prompt,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
