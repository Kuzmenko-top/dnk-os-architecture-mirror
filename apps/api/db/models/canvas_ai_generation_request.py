# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_canvas_ai_generation_request"
# purpose: "ORM Model for AI-Powered Node & Flow Generation Requests on Canvas (DNK-CANVAS-003 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from apps.api.db.models.workspace import Base


class CanvasAIGenerationRequestModel(Base):
    __tablename__ = "canvas_ai_generation_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    canvas_id = Column(String(64), nullable=False, index=True)
    requester_id = Column(String(64), nullable=False, default="user")
    prompt = Column(String(1024), nullable=False)
    context_node_ids = Column(JSON, nullable=False, default=list)
    target_coordinates = Column(JSON, nullable=False, default=dict)  # {"x": 100.0, "y": 200.0}
    status = Column(String(32), nullable=False, default="PENDING")  # PENDING, PROCESSING, GENERATED, APPLIED, FAILED
    generated_nodes = Column(JSON, nullable=False, default=list)
    generated_edges = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "canvas_id": self.canvas_id,
            "requester_id": self.requester_id,
            "prompt": self.prompt,
            "context_node_ids": self.context_node_ids,
            "target_coordinates": self.target_coordinates,
            "status": self.status,
            "generated_nodes": self.generated_nodes,
            "generated_edges": self.generated_edges,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
