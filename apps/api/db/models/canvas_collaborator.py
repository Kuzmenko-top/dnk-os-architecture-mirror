# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_collaborator"
# purpose: "SQLAlchemy ORM model for Canvas Real-Time Collaborator / Peer (DNK-CANVAS-002 Phase 1)"
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
    Float,
    DateTime,
    JSON,
    ForeignKey,
    Index,
    CheckConstraint
)

from apps.api.db.models.workspace import Base


class CanvasCollaboratorModel(Base):
    __tablename__ = "canvas_collaborators"

    id = Column(String(128), primary_key=True, nullable=False)
    session_id = Column(String(128), ForeignKey("canvas_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    canvas_id = Column(String(128), ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    user_name = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="editor")  # editor, viewer, agent
    color = Column(String(32), nullable=False, default="#3b82f6")
    cursor_x = Column(Float, nullable=False, default=0.0)
    cursor_y = Column(Float, nullable=False, default=0.0)
    selected_node_ids = Column(JSON, nullable=True, default=list)
    client_metadata = Column(JSON, nullable=True, default=dict)
    connected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_ping_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("role IN ('editor', 'viewer', 'agent', 'supervisor')", name="check_canvas_collaborator_role"),
        Index("ix_canvas_collaborators_canvas_user", "canvas_id", "user_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "canvas_id": self.canvas_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "role": self.role,
            "color": self.color,
            "cursor": {"x": self.cursor_x, "y": self.cursor_y},
            "selected_node_ids": self.selected_node_ids or [],
            "client_metadata": self.client_metadata or {},
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_ping_at": self.last_ping_at.isoformat() if self.last_ping_at else None,
        }
