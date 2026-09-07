# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_session"
# purpose: "SQLAlchemy ORM model for Canvas Real-Time Collaboration Session (DNK-CANVAS-002 Phase 1)"
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
    ForeignKey,
    Index,
    CheckConstraint
)

from apps.api.db.models.workspace import Base


class CanvasSessionModel(Base):
    __tablename__ = "canvas_sessions"

    id = Column(String(128), primary_key=True, nullable=False)
    canvas_id = Column(String(128), ForeignKey("canvases.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    active_peers_count = Column(Integer, nullable=False, default=1)
    current_version = Column(Integer, nullable=False, default=1)
    state_snapshot = Column(JSON, nullable=True, default=dict)
    active_locks = Column(JSON, nullable=True, default=list)  # List of locked node IDs with user_id
    status = Column(String(32), nullable=False, default="active")  # active, closed, archived
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    last_activity_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("status IN ('active', 'closed', 'archived')", name="check_canvas_session_status"),
        Index("ix_canvas_sessions_canvas_status", "canvas_id", "status"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "workspace_id": self.workspace_id,
            "active_peers_count": self.active_peers_count,
            "current_version": self.current_version,
            "state_snapshot": self.state_snapshot or {},
            "active_locks": self.active_locks or [],
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "last_activity_at": self.last_activity_at.isoformat() if self.last_activity_at else None,
        }
