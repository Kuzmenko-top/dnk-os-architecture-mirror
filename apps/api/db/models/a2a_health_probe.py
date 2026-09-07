# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_a2a_health_probe"
# purpose: "ORM Model for Heartbeat & Synthetic Health Probes in A2A Mesh (DNK-A2A-004 Phase 1)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, Float, Boolean, Integer, JSON
from apps.api.db.models.workspace import Base


class A2AHealthProbe(Base):
    """Stores heartbeat, telemetry metrics and synthetic health check results for mesh nodes."""
    __tablename__ = "a2a_health_probes"

    id = Column(String(64), primary_key=True, default=lambda: f"probe_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    agent_id = Column(String(64), nullable=False, index=True)
    probe_type = Column(String(32), nullable=False, default="heartbeat")  # heartbeat, synthetic_rpc, ping, memory_check
    is_healthy = Column(Boolean, nullable=False, default=True)
    latency_ms = Column(Float, nullable=False, default=0.0)
    cpu_percent = Column(Float, nullable=False, default=0.0)
    memory_mb = Column(Float, nullable=False, default=0.0)
    status_code = Column(Integer, nullable=False, default=200)
    error_message = Column(String(512), nullable=True)
    probe_details = Column(JSON, nullable=False, default=dict)
    probed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id or "ws-default",
            "agent_id": self.agent_id,
            "probe_type": self.probe_type or "heartbeat",
            "is_healthy": bool(self.is_healthy),
            "latency_ms": self.latency_ms if self.latency_ms is not None else 0.0,
            "cpu_percent": self.cpu_percent if self.cpu_percent is not None else 0.0,
            "memory_mb": self.memory_mb if self.memory_mb is not None else 0.0,
            "status_code": self.status_code if self.status_code is not None else 200,
            "error_message": self.error_message,
            "probe_details": self.probe_details or {},
            "probed_at": self.probed_at.isoformat() if self.probed_at else None,
        }
