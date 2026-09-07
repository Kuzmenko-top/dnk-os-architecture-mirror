# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/stream_consumer_group.py"
# purpose: "ORM Model for Stream Consumer Group & Offset State (DNK-STREAM-001)"
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
from sqlalchemy import Column, String, Integer, DateTime, JSON

try:
    from apps.api.db.models.workspace import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class StreamConsumerGroup(Base):
    """Represents a consumer group with committed offsets and member state."""
    __tablename__ = "stream_consumer_groups"

    id = Column(String(64), primary_key=True, default=lambda: f"grp_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    group_name = Column(String(128), nullable=False, index=True)
    topic_name = Column(String(128), nullable=False, index=True)
    state = Column(String(32), default="STABLE", nullable=False)  # STABLE, REBALANCING, DEAD, EMPTY
    generation_id = Column(Integer, default=1, nullable=False)
    protocol_type = Column(String(32), default="consumer", nullable=False)
    members = Column(JSON, default=list)  # list of {member_id, client_id, partitions}
    committed_offsets = Column(JSON, default=dict)  # {"partition_0": offset, ...}
    last_heartbeat_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"grp_{uuid.uuid4().hex[:12]}"
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "state", None) is None:
            self.state = "STABLE"
        if getattr(self, "generation_id", None) is None:
            self.generation_id = 1
        if getattr(self, "protocol_type", None) is None:
            self.protocol_type = "consumer"
        if getattr(self, "members", None) is None:
            self.members = []
        if getattr(self, "committed_offsets", None) is None:
            self.committed_offsets = {}
        if getattr(self, "last_heartbeat_at", None) is None:
            self.last_heartbeat_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "group_name": self.group_name,
            "topic_name": self.topic_name,
            "state": self.state,
            "generation_id": self.generation_id,
            "protocol_type": self.protocol_type,
            "members": self.members or [],
            "committed_offsets": self.committed_offsets or {},
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else datetime.now(timezone.utc).isoformat(),
        }
