# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_semantic_group"
# purpose: "ORM Model for Canvas Semantic Multi-Node Clustering & Grouping (DNK-CANVAS-003 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from apps.api.db.models.workspace import Base


class CanvasSemanticGroupModel(Base):
    __tablename__ = "canvas_semantic_groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canvas_id = Column(String(64), nullable=False, index=True)
    title = Column(String(128), nullable=False)
    description = Column(String(512), nullable=True)
    color = Column(String(32), nullable=False, default="#6366f1")
    node_ids = Column(JSON, nullable=False, default=list)
    bounding_box = Column(JSON, nullable=False, default=dict)  # {"min_x": 0, "min_y": 0, "max_x": 100, "max_y": 100}
    is_collapsed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "title": self.title,
            "description": self.description,
            "color": self.color,
            "node_ids": self.node_ids,
            "bounding_box": self.bounding_box,
            "is_collapsed": self.is_collapsed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
