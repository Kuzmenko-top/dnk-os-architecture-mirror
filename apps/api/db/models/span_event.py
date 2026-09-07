# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/span_event.py"
# purpose: "ORM Model for Span Event / Annotation in Distributed Tracing Platform (DNK-OBSERVE-001)"
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


class SpanEvent(Base):
    """Represents a timestamped annotation or event occurring within a trace span lifecycle."""
    __tablename__ = "span_events"

    id = Column(String(64), primary_key=True, default=lambda: f"spe_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    span_id = Column(String(32), nullable=False, index=True)
    trace_id = Column(String(64), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    attributes = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"spe_{uuid.uuid4().hex[:12]}"
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "attributes", None) is None:
            self.attributes = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "span_id": self.span_id,
            "trace_id": self.trace_id,
            "name": self.name,
            "timestamp": self.timestamp.isoformat() if self.timestamp else datetime.now(timezone.utc).isoformat(),
            "attributes": self.attributes or {},
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
        }
