# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/trace_service.py"
# purpose: "ORM Model for Trace Service Registry in Distributed Tracing Platform (DNK-OBSERVE-001)"
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


class TraceService(Base):
    """Represents a registered microservice / agent participating in distributed tracing."""
    __tablename__ = "trace_services"

    id = Column(String(64), primary_key=True, default=lambda: f"srv_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    name = Column(String(128), nullable=False, unique=True, index=True)
    environment = Column(String(32), default="production", nullable=False)
    version = Column(String(32), default="1.0.0", nullable=False)
    runtime = Column(String(64), default="Python 3.12 / FastAPI", nullable=False)
    health_status = Column(String(32), default="HEALTHY", nullable=False)  # HEALTHY, DEGRADED, CRITICAL
    metadata_info = Column(JSON, default=dict)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"srv_{uuid.uuid4().hex[:12]}"
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "environment", None) is None:
            self.environment = "production"
        if getattr(self, "version", None) is None:
            self.version = "1.0.0"
        if getattr(self, "runtime", None) is None:
            self.runtime = "Python 3.12 / FastAPI"
        if getattr(self, "health_status", None) is None:
            self.health_status = "HEALTHY"
        if getattr(self, "metadata_info", None) is None:
            self.metadata_info = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "service_name": self.name,
            "environment": self.environment,
            "version": self.version,
            "runtime": self.runtime,
            "health_status": self.health_status,
            "metadata_info": self.metadata_info or {},
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
