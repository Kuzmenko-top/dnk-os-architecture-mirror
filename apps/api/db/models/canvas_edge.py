# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_edge"
# purpose: "SQLAlchemy ORM model for Canvas Edge entity (DNK-CANVAS-002 Phase 1)"
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
    DateTime,
    JSON,
    ForeignKey,
    Index,
    CheckConstraint
)

from apps.api.db.models.workspace import Base


class CanvasEdgeModel(Base):
    __tablename__ = "canvas_edges"

    id = Column(String(128), primary_key=True, nullable=False)
    canvas_id = Column(String(128), ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False, index=True)
    source_node_id = Column(String(128), ForeignKey("canvas_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    target_node_id = Column(String(128), ForeignKey("canvas_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    source_port = Column(String(64), nullable=False, default="output")
    target_port = Column(String(64), nullable=False, default="input")
    edge_type = Column(String(32), nullable=False, default="bezier")  # bezier, orthogonal, straight, smoothstep
    label = Column(String(255), nullable=True)
    condition_expression = Column(String(1024), nullable=True)
    data_payload = Column(JSON, nullable=True, default=dict)
    style_payload = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("edge_type IN ('bezier', 'orthogonal', 'straight', 'smoothstep', 'smart_bezier')", name="check_canvas_edge_type"),
        Index("ix_canvas_edges_source_target", "canvas_id", "source_node_id", "target_node_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "source_port": self.source_port,
            "target_port": self.target_port,
            "edge_type": self.edge_type,
            "label": self.label,
            "condition_expression": self.condition_expression,
            "data": self.data_payload or {},
            "style": self.style_payload or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
