# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_node"
# purpose: "SQLAlchemy ORM model for Canvas Node entity (DNK-CANVAS-002 Phase 1)"
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


class CanvasNodeModel(Base):
    __tablename__ = "canvas_nodes"

    id = Column(String(128), primary_key=True, nullable=False)
    canvas_id = Column(String(128), ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False, index=True)
    node_type = Column(String(64), nullable=False, default="component")  # component, agent, text, shape, container
    title = Column(String(255), nullable=False)
    pos_x = Column(Float, nullable=False, default=0.0)
    pos_y = Column(Float, nullable=False, default=0.0)
    width = Column(Float, nullable=False, default=240.0)
    height = Column(Float, nullable=False, default=160.0)
    z_index = Column(Integer, nullable=False, default=1)
    is_locked = Column(Integer, nullable=False, default=0)
    parent_node_id = Column(String(128), nullable=True, index=True)
    component_id = Column(String(128), nullable=True)  # Reference to canvas_components if applicable
    data_payload = Column(JSON, nullable=True, default=dict)
    style_payload = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("node_type IN ('component', 'agent', 'text', 'shape', 'container', 'group', 'input', 'output')", name="check_canvas_node_type"),
        Index("ix_canvas_nodes_canvas_zindex", "canvas_id", "z_index"),
        Index("ix_canvas_nodes_parent", "canvas_id", "parent_node_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "node_type": self.node_type,
            "title": self.title,
            "position": {"x": self.pos_x, "y": self.pos_y},
            "dimensions": {"width": self.width, "height": self.height},
            "z_index": self.z_index,
            "is_locked": bool(self.is_locked),
            "parent_node_id": self.parent_node_id,
            "component_id": self.component_id,
            "data": self.data_payload or {},
            "style": self.style_payload or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
