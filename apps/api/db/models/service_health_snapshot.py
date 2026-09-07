# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_service_health_snapshot"
# purpose: "ORM Model for Service Health State Snapshots (DNK-HEALTH-001 Phase 1)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, Float, DateTime, JSON
from apps.api.db.models.workspace import Base


class ServiceHealthSnapshot(Base):
    __tablename__ = "service_health_snapshots"

    id = Column(String(64), primary_key=True, default=lambda: f"shs_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    service_name = Column(String(128), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="HEALTHY")  # HEALTHY, DEGRADED, UNHEALTHY, FLAPPING
    cpu_usage_pct = Column(Float, nullable=True)
    memory_usage_pct = Column(Float, nullable=True)
    error_rate_pct = Column(Float, nullable=True)
    p95_latency_ms = Column(Float, nullable=True)
    active_incidents_count = Column(Float, default=0.0)
    metrics_payload = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id or f"shs_{uuid.uuid4().hex[:12]}",
            "workspace_id": self.workspace_id or "ws-default",
            "service_name": self.service_name,
            "status": self.status or "HEALTHY",
            "cpu_usage_pct": self.cpu_usage_pct,
            "memory_usage_pct": self.memory_usage_pct,
            "error_rate_pct": self.error_rate_pct,
            "p95_latency_ms": self.p95_latency_ms,
            "active_incidents_count": self.active_incidents_count or 0.0,
            "metrics_payload": self.metrics_payload or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else datetime.now(timezone.utc).isoformat(),
        }
