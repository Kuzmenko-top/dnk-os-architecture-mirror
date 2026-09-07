# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/trace_span.py"
# purpose: "ORM Model for Trace Span in Distributed Tracing & Observability Platform (DNK-OBSERVE-001)"
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
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON

try:
    from apps.api.db.models.workspace import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class TraceSpan(Base):
    """Represents an individual OpenTelemetry-compliant trace span."""
    __tablename__ = "trace_spans"

    id = Column(String(64), primary_key=True, default=lambda: f"spn_{uuid.uuid4().hex[:16]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    trace_id = Column(String(64), nullable=False, index=True)
    span_id = Column(String(32), nullable=False, index=True)
    parent_span_id = Column(String(32), nullable=True, index=True)
    service_name = Column(String(128), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    kind = Column(String(32), default="INTERNAL", nullable=False)  # SERVER, CLIENT, PRODUCER, CONSUMER, INTERNAL
    status_code = Column(String(32), default="OK", nullable=False)  # OK, ERROR, UNSET
    status_message = Column(String(512), nullable=True)
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_ms = Column(Float, default=0.0, nullable=False)
    attributes = Column(JSON, default=dict)
    events = Column(JSON, default=list)
    links = Column(JSON, default=list)
    is_root = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    @staticmethod
    def generate_trace_id() -> str:
        """Generate a 32-hex character W3C-compliant trace ID."""
        return uuid.uuid4().hex[:32]

    @staticmethod
    def generate_span_id() -> str:
        """Generate a 16-hex character W3C-compliant span ID."""
        return uuid.uuid4().hex[:16]

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"spn_{uuid.uuid4().hex[:16]}"
        if getattr(self, "span_id", None) is None:
            self.span_id = uuid.uuid4().hex[:16]
        if getattr(self, "trace_id", None) is None:
            self.trace_id = uuid.uuid4().hex[:32]
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "kind", None) is None:
            self.kind = "INTERNAL"
        if getattr(self, "status_code", None) is None:
            self.status_code = "OK"
        if getattr(self, "duration_ms", None) is None:
            self.duration_ms = 0.0
        if getattr(self, "attributes", None) is None:
            self.attributes = {}
        if getattr(self, "events", None) is None:
            self.events = []
        if getattr(self, "links", None) is None:
            self.links = []
        if getattr(self, "is_root", None) is None:
            self.is_root = (self.parent_span_id is None)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None, timestamp: Optional[Any] = None) -> Dict[str, Any]:
        """Record a lifecycle or error event on this span."""
        if self.events is None:
            self.events = []
        event_entry = {
            "name": name,
            "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
            "attributes": attributes or {},
        }
        self.events.append(event_entry)
        return event_entry

    def add_link(self, trace_id: str, span_id: str, attributes: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Record a causal link to another span."""
        if self.links is None:
            self.links = []
        link_entry = {
            "trace_id": trace_id,
            "span_id": span_id,
            "attributes": attributes or {},
        }
        self.links.append(link_entry)
        return link_entry

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a single span attribute."""
        if self.attributes is None:
            self.attributes = {}
        self.attributes[key] = value

    def to_dict(self) -> Dict[str, Any]:
        def _fmt_time(t):
            if t is None:
                return None
            if isinstance(t, datetime):
                return t.isoformat()
            return str(t)

        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "service_name": self.service_name,
            "name": self.name,
            "kind": self.kind,
            "status_code": self.status_code,
            "status_message": self.status_message,
            "start_time": _fmt_time(self.start_time) or datetime.now(timezone.utc).isoformat(),
            "end_time": _fmt_time(self.end_time),
            "duration_ms": self.duration_ms,
            "attributes": self.attributes or {},
            "events": self.events or [],
            "links": self.links or [],
            "is_root": self.is_root,
            "created_at": _fmt_time(self.created_at) or datetime.now(timezone.utc).isoformat(),
        }
