# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/trace_context.py"
# purpose: "ORM Model for W3C Trace Context Propagation in Distributed Tracing Platform (DNK-OBSERVE-001)"
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
from sqlalchemy import Column, String, Boolean, DateTime, JSON

try:
    from apps.api.db.models.workspace import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class TraceContext(Base):
    """Represents a persisted W3C Trace Context state for cross-session/async task propagation."""
    __tablename__ = "trace_contexts"

    id = Column(String(64), primary_key=True, default=lambda: f"ctx_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    trace_id = Column(String(64), nullable=False, unique=True, index=True)
    span_id = Column(String(32), nullable=False, index=True)
    trace_flags = Column(String(8), default="01", nullable=False)
    trace_state = Column(String(512), nullable=True)
    baggage = Column(JSON, default=dict)
    sampled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"ctx_{uuid.uuid4().hex[:12]}"
        if getattr(self, "trace_id", None) is None:
            self.trace_id = uuid.uuid4().hex[:32]
        if getattr(self, "span_id", None) is None:
            self.span_id = uuid.uuid4().hex[:16]
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "trace_flags", None) is None:
            self.trace_flags = "01"
        if getattr(self, "sampled", None) is None:
            self.sampled = True
        if getattr(self, "baggage", None) is None:
            self.baggage = {}

    @staticmethod
    def generate_trace_id() -> str:
        """Generate a 32-hex character W3C-compliant trace ID."""
        return uuid.uuid4().hex[:32]

    @staticmethod
    def generate_span_id() -> str:
        """Generate a 16-hex character W3C-compliant span ID."""
        return uuid.uuid4().hex[:16]

    @property
    def traceparent(self) -> str:
        """Serializes context to standard W3C traceparent header format."""
        return self.to_w3c_traceparent()

    def to_w3c_traceparent(self) -> str:
        """Serializes context to standard W3C traceparent header format."""
        return f"00-{self.trace_id.lower()}-{self.span_id.lower()}-{self.trace_flags.lower()}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "trace_flags": self.trace_flags,
            "trace_state": self.trace_state,
            "traceparent": self.to_w3c_traceparent(),
            "baggage": self.baggage or {},
            "sampled": self.sampled,
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else datetime.now(timezone.utc).isoformat(),
        }
