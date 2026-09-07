# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_system_incident"
# purpose: "ORM Model for Tracked System Incidents (DNK-HEALTH-001 Phase 1)"
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


class SystemIncident(Base):
    __tablename__ = "system_incidents"

    id = Column(String(64), primary_key=True, default=lambda: f"inc_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    service_name = Column(String(128), nullable=False, index=True)
    rule_id = Column(String(64), nullable=True, index=True)
    severity = Column(String(32), nullable=False, default="WARNING")  # WARNING, CRITICAL, FATAL
    status = Column(String(32), nullable=False, default="OPEN")      # OPEN, MITIGATING, RESOLVED, SUPPRESSED
    title = Column(String(255), nullable=False)
    description = Column(String(1024), nullable=True)
    metric_name = Column(String(128), nullable=False)
    observed_value = Column(Float, nullable=False)
    threshold_value = Column(Float, nullable=False)
    context_data = Column(JSON, default=dict)
    opened_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"inc_{uuid.uuid4().hex[:12]}"
        if getattr(self, "severity", None) is None:
            self.severity = "WARNING"
        if getattr(self, "status", None) is None:
            self.status = "OPEN"
        if getattr(self, "context_data", None) is None:
            self.context_data = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id or f"inc_{uuid.uuid4().hex[:12]}",
            "workspace_id": self.workspace_id or "ws-default",
            "service_name": self.service_name,
            "rule_id": self.rule_id,
            "severity": self.severity or "WARNING",
            "status": self.status or "OPEN",
            "title": self.title,
            "description": self.description or "",
            "metric_name": self.metric_name,
            "observed_value": self.observed_value,
            "threshold_value": self.threshold_value,
            "context_data": self.context_data or {},
            "opened_at": self.opened_at.isoformat() if self.opened_at else datetime.now(timezone.utc).isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
