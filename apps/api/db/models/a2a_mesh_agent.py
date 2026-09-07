# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-MODEL-AGENT"
# purpose: "A2A Mesh Agent Node ORM Model for P2P Discovery and Status Tracking"
# canonical_source: true
# alters_files: ["apps/api/db/models/a2a_mesh_agent.py"]
# triggers_tasks: ["DNK-A2A-003-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Float, Boolean
from apps.api.db.models.workspace import Base


class A2AMeshAgent(Base):
    """Represents an active agent node registered within the peer-to-peer mesh topology."""
    __tablename__ = "a2a_mesh_agents"

    id = Column(String(64), primary_key=True, default=lambda: f"agent_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    agent_name = Column(String(128), nullable=False, index=True)
    role = Column(String(64), nullable=False, default="worker")
    capabilities = Column(JSON, nullable=False, default=list)  # list of str e.g. ["codegen", "audit"]
    status = Column(String(32), nullable=False, default="online", index=True)  # online, busy, offline
    cpu_utilization = Column(Float, nullable=False, default=0.0)
    memory_utilization = Column(Float, nullable=False, default=0.0)
    active_tasks_count = Column(Float, nullable=False, default=0.0)
    reputation_score = Column(Float, nullable=False, default=1.0)
    endpoint_url = Column(String(256), nullable=True)
    is_leader = Column(Boolean, nullable=False, default=False)
    last_heartbeat_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "agent_name": self.agent_name,
            "role": self.role,
            "capabilities": self.capabilities or [],
            "status": self.status or "online",
            "cpu_utilization": self.cpu_utilization if self.cpu_utilization is not None else 0.0,
            "memory_utilization": self.memory_utilization if self.memory_utilization is not None else 0.0,
            "active_tasks_count": self.active_tasks_count if self.active_tasks_count is not None else 0.0,
            "reputation_score": self.reputation_score if self.reputation_score is not None else 1.0,
            "endpoint_url": self.endpoint_url,
            "is_leader": bool(self.is_leader),
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
