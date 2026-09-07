# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/stream_message.py"
# purpose: "ORM Model for Stream Message Envelope (DNK-STREAM-001)"
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
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, JSON, Text

try:
    from apps.api.db.models.workspace import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class StreamMessage(Base):
    """Represents an ingested event stream message envelope."""
    __tablename__ = "stream_messages"

    id = Column(String(64), primary_key=True, default=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    topic_name = Column(String(128), nullable=False, index=True)
    partition = Column(Integer, default=0, nullable=False, index=True)
    offset = Column(BigInteger, default=0, nullable=False, index=True)
    key = Column(String(255), nullable=True, index=True)
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, default=dict)
    schema_id = Column(String(64), nullable=True)
    dedup_hash = Column(String(64), nullable=True, index=True)
    trace_id = Column(String(64), nullable=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"msg_{uuid.uuid4().hex[:12]}"
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "partition", None) is None:
            self.partition = 0
        if getattr(self, "offset", None) is None:
            self.offset = 0
        if getattr(self, "headers", None) is None:
            self.headers = {}
        if getattr(self, "payload", None) is None:
            self.payload = {}
        if getattr(self, "timestamp", None) is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "topic_name": self.topic_name,
            "partition": self.partition,
            "offset": self.offset,
            "key": self.key,
            "payload": self.payload or {},
            "headers": self.headers or {},
            "schema_id": self.schema_id,
            "dedup_hash": self.dedup_hash,
            "trace_id": self.trace_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else datetime.now(timezone.utc).isoformat(),
        }
