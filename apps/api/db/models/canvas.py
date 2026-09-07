# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas"
# purpose: "SQLAlchemy ORM model for Canvas entity (DNK-CANVAS-002 Phase 1)"
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
    Float,
    DateTime,
    JSON,
    ForeignKey,
    Index,
    CheckConstraint
)

from apps.api.db.models.workspace import Base


class CanvasModel(Base):
    __tablename__ = "canvases"

    id = Column(String(128), primary_key=True, nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    viewport_x = Column(Float, nullable=False, default=0.0)
    viewport_y = Column(Float, nullable=False, default=0.0)
    zoom = Column(Float, nullable=False, default=1.0)
    grid_size = Column(Integer, nullable=False, default=20)
    snap_to_grid = Column(Integer, nullable=False, default=1)  # 1 = True, 0 = False
    background_color = Column(String(32), nullable=False, default="#121214")
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="active")
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    metadata_payload = Column(JSON, nullable=True, default=dict)

    __table_args__ = (
        CheckConstraint("status IN ('active', 'archived', 'draft')", name="check_canvas_status"),
        CheckConstraint("zoom >= 0.1 AND zoom <= 10.0", name="check_canvas_zoom_range"),
        Index("ix_canvases_workspace_status", "workspace_id", "status"),
        Index("ix_canvases_updated_at", "updated_at"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "viewport_x": self.viewport_x,
            "viewport_y": self.viewport_y,
            "zoom": self.zoom,
            "grid_size": self.grid_size,
            "snap_to_grid": bool(self.snap_to_grid),
            "background_color": self.background_color,
            "version": self.version,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata_payload or {},
        }
