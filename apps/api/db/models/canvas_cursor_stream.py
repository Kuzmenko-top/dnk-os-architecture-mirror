# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_cursor_stream"
# purpose: "ORM Model for Ephemeral Canvas Cursor Events & Delta Streams (DNK-CANVAS-003 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, JSON
from apps.api.db.models.workspace import Base


class CanvasCursorStreamModel(Base):
    __tablename__ = "canvas_cursor_streams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canvas_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(32), nullable=False, default="POINTER_MOVE")  # POINTER_MOVE, SELECTION_CHANGE, VIEWPORT_PAN, NODE_DRAG
    x = Column(Float, nullable=False, default=0.0)
    y = Column(Float, nullable=False, default=0.0)
    payload = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "x": self.x,
            "y": self.y,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
