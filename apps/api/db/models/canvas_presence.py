# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_presence"
# purpose: "ORM Model for Real-Time Canvas User Presence & Selection Awareness (DNK-CANVAS-003 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON
from apps.api.db.models.workspace import Base


class CanvasPresenceModel(Base):
    __tablename__ = "canvas_presences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canvas_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    user_name = Column(String(128), nullable=False, default="Anonymous")
    user_color = Column(String(32), nullable=False, default="#3b82f6")
    cursor_x = Column(Float, nullable=False, default=0.0)
    cursor_y = Column(Float, nullable=False, default=0.0)
    viewport_bounds = Column(JSON, nullable=False, default=dict)
    selected_node_ids = Column(JSON, nullable=False, default=list)
    active_tool = Column(String(32), nullable=False, default="select")
    last_heartbeat_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_online = Column(Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_color": self.user_color,
            "cursor_x": self.cursor_x,
            "cursor_y": self.cursor_y,
            "viewport_bounds": self.viewport_bounds,
            "selected_node_ids": self.selected_node_ids,
            "active_tool": self.active_tool,
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            "is_online": self.is_online,
        }
