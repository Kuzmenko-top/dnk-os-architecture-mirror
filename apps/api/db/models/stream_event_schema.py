# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/stream_event_schema.py"
# purpose: "ORM Model for Stream Event Schema in Schema Registry (DNK-STREAM-001)"
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
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON

try:
    from apps.api.db.models.workspace import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class StreamEventSchema(Base):
    """Represents a registered event schema in Schema Registry."""
    __tablename__ = "stream_event_schemas"

    id = Column(String(64), primary_key=True, default=lambda: f"sch_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    subject = Column(String(128), nullable=False, index=True)  # e.g., "orders.created-value"
    version = Column(Integer, default=1, nullable=False)
    schema_format = Column(String(32), default="JSON_SCHEMA", nullable=False)  # JSON_SCHEMA, AVRO, PROTOBUF
    schema_definition = Column(JSON, nullable=False)
    compatibility_mode = Column(String(32), default="BACKWARD", nullable=False)  # NONE, BACKWARD, FORWARD, FULL
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"sch_{uuid.uuid4().hex[:12]}"
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "version", None) is None:
            self.version = 1
        if getattr(self, "schema_format", None) is None:
            self.schema_format = "JSON_SCHEMA"
        if getattr(self, "compatibility_mode", None) is None:
            self.compatibility_mode = "BACKWARD"
        if getattr(self, "is_active", None) is None:
            self.is_active = True
        if getattr(self, "schema_definition", None) is None:
            self.schema_definition = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "subject": self.subject,
            "version": self.version,
            "schema_format": self.schema_format,
            "schema_definition": self.schema_definition or {},
            "compatibility_mode": self.compatibility_mode,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else datetime.now(timezone.utc).isoformat(),
        }
