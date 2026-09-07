# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/stream_topic.py"
# purpose: "ORM Model for Stream Topic in Real-Time Event Streaming Platform (DNK-STREAM-001)"
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


class StreamTopic(Base):
    """Represents a stream topic configuration and partition topology."""
    __tablename__ = "stream_topics"

    id = Column(String(64), primary_key=True, default=lambda: f"top_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    name = Column(String(128), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    partitions_count = Column(Integer, default=3, nullable=False)
    replication_factor = Column(Integer, default=1, nullable=False)
    retention_hours = Column(Integer, default=168, nullable=False)  # 7 days
    cleanup_policy = Column(String(32), default="DELETE", nullable=False)  # DELETE, COMPACT
    schema_id = Column(String(64), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"top_{uuid.uuid4().hex[:12]}"
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "partitions_count", None) is None:
            self.partitions_count = 3
        if getattr(self, "replication_factor", None) is None:
            self.replication_factor = 1
        if getattr(self, "retention_hours", None) is None:
            self.retention_hours = 168
        if getattr(self, "cleanup_policy", None) is None:
            self.cleanup_policy = "DELETE"
        if getattr(self, "is_active", None) is None:
            self.is_active = True
        if getattr(self, "metadata_info", None) is None:
            self.metadata_info = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "description": self.description,
            "partitions_count": self.partitions_count,
            "replication_factor": self.replication_factor,
            "retention_hours": self.retention_hours,
            "cleanup_policy": self.cleanup_policy,
            "schema_id": self.schema_id,
            "is_active": self.is_active,
            "metadata_info": self.metadata_info or {},
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else datetime.now(timezone.utc).isoformat(),
        }
