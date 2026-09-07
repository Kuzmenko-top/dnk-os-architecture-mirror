# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_spatial_index"
# purpose: "ORM Model for Canvas Spatial Bounding Box & R-Tree Indexing (DNK-CANVAS-003 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from apps.api.db.models.workspace import Base


class CanvasSpatialIndexModel(Base):
    __tablename__ = "canvas_spatial_indices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canvas_id = Column(String(64), nullable=False, index=True)
    node_id = Column(String(64), nullable=True, index=True)
    group_id = Column(String(64), nullable=True, index=True)
    min_x = Column(Float, nullable=False, default=0.0)
    min_y = Column(Float, nullable=False, default=0.0)
    max_x = Column(Float, nullable=False, default=0.0)
    max_y = Column(Float, nullable=False, default=0.0)
    lod_level = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def intersects(self, bbox: tuple[float, float, float, float]) -> bool:
        """bbox is (min_x, min_y, max_x, max_y)"""
        b_min_x, b_min_y, b_max_x, b_max_y = bbox
        return not (
            self.max_x < b_min_x
            or self.min_x > b_max_x
            or self.max_y < b_min_y
            or self.min_y > b_max_y
        )

    def to_dict(self):
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "node_id": self.node_id,
            "group_id": self.group_id,
            "min_x": self.min_x,
            "min_y": self.min_y,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "lod_level": self.lod_level,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
