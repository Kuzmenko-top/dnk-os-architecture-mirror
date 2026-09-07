# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_history_snapshot"
# purpose: "ORM Model for Canvas State History Snapshots & Time-Travel Diffs (DNK-CANVAS-003 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, JSON
from apps.api.db.models.workspace import Base


class CanvasHistorySnapshotModel(Base):
    __tablename__ = "canvas_history_snapshots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canvas_id = Column(String(64), nullable=False, index=True)
    version_index = Column(Integer, nullable=False, default=1)
    snapshot_tag = Column(String(64), nullable=True)  # e.g., "v1.0.0-milestone", "auto-save"
    author_id = Column(String(64), nullable=False, default="system")
    nodes_count = Column(Integer, nullable=False, default=0)
    edges_count = Column(Integer, nullable=False, default=0)
    state_diff_json = Column(JSON, nullable=False, default=dict)
    parent_snapshot_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "version_index": self.version_index,
            "snapshot_tag": self.snapshot_tag,
            "author_id": self.author_id,
            "nodes_count": self.nodes_count,
            "edges_count": self.edges_count,
            "state_diff_json": self.state_diff_json,
            "parent_snapshot_id": self.parent_snapshot_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
