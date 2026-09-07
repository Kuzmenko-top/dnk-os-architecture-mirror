# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/span_link.py"
# purpose: "ORM Model for Span Link (Causal Relationship) in Distributed Tracing Platform (DNK-OBSERVE-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, DateTime, JSON

try:
    from apps.api.db.models.workspace import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class SpanLink(Base):
    """Represents a causal link between spans (e.g., across batch items or async worker jobs)."""
    __tablename__ = "span_links"

    id = Column(String(64), primary_key=True, default=lambda: f"spl_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    source_span_id = Column(String(32), nullable=False, index=True)
    linked_trace_id = Column(String(64), nullable=False, index=True)
    linked_span_id = Column(String(32), nullable=False, index=True)
    relationship_type = Column(String(64), default="CAUSAL", nullable=False)  # CAUSAL, BATCH_ITEM, ASYNC_FOLLOW
    attributes = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"spl_{uuid.uuid4().hex[:12]}"
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "relationship_type", None) is None:
            self.relationship_type = "CAUSAL"
        if getattr(self, "attributes", None) is None:
            self.attributes = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "source_span_id": self.source_span_id,
            "linked_trace_id": self.linked_trace_id,
            "linked_span_id": self.linked_span_id,
            "relationship_type": self.relationship_type,
            "attributes": self.attributes or {},
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
        }
