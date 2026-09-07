# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/stream_dead_letter_event.py"
# purpose: "ORM Model for Stream Dead Letter Event (DLQ) (DNK-STREAM-001)"
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
from sqlalchemy import Column, String, Integer, DateTime, JSON, Text

try:
    from apps.api.db.models.workspace import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class StreamDeadLetterEvent(Base):
    """Represents a failed / poisoned message quarantined into DLQ."""
    __tablename__ = "stream_dead_letter_events"

    id = Column(String(64), primary_key=True, default=lambda: f"dlq_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    original_topic = Column(String(128), nullable=False, index=True)
    consumer_group = Column(String(128), nullable=True, index=True)
    partition = Column(Integer, default=0, nullable=False)
    offset = Column(Integer, default=0, nullable=False)
    payload = Column(JSON, nullable=False)
    headers = Column(JSON, default=dict)
    error_reason = Column(Text, nullable=False)
    error_stack = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="QUARANTINED", nullable=False)  # QUARANTINED, REPLAYED, DISCARDED
    replayed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"dlq_{uuid.uuid4().hex[:12]}"
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
        if getattr(self, "retry_count", None) is None:
            self.retry_count = 0
        if getattr(self, "status", None) is None:
            self.status = "QUARANTINED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "original_topic": self.original_topic,
            "consumer_group": self.consumer_group,
            "partition": self.partition,
            "offset": self.offset,
            "payload": self.payload or {},
            "headers": self.headers or {},
            "error_reason": self.error_reason,
            "error_stack": self.error_stack,
            "retry_count": self.retry_count,
            "status": self.status,
            "replayed_at": self.replayed_at.isoformat() if self.replayed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
        }
