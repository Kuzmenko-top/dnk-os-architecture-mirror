# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_remediation_action"
# purpose: "ORM Model for Self-Healing Remediation Actions (DNK-HEALTH-001 Phase 1)"
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


class RemediationAction(Base):
    __tablename__ = "remediation_actions"

    id = Column(String(64), primary_key=True, default=lambda: f"act_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    incident_id = Column(String(64), nullable=False, index=True)
    policy_id = Column(String(64), nullable=True, index=True)
    service_name = Column(String(128), nullable=False, index=True)
    action_type = Column(String(64), nullable=False)  # restart_service, drain_traffic, clear_cache, scale_replicas, trip_circuit_breaker
    status = Column(String(32), default="PENDING")    # PENDING, IN_PROGRESS, SUCCEEDED, FAILED, TIMED_OUT, ROLLED_BACK
    parameters = Column(JSON, default=dict)
    execution_result = Column(JSON, default=dict)
    execution_time_ms = Column(Float, nullable=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"act_{uuid.uuid4().hex[:12]}"
        if getattr(self, "status", None) is None:
            self.status = "PENDING"
        if getattr(self, "parameters", None) is None:
            self.parameters = {}
        if getattr(self, "execution_result", None) is None:
            self.execution_result = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id or f"act_{uuid.uuid4().hex[:12]}",
            "workspace_id": self.workspace_id or "ws-default",
            "incident_id": self.incident_id,
            "policy_id": self.policy_id,
            "service_name": self.service_name,
            "action_type": self.action_type,
            "status": self.status or "PENDING",
            "parameters": self.parameters or {},
            "execution_result": self.execution_result or {},
            "execution_time_ms": self.execution_time_ms,
            "started_at": self.started_at.isoformat() if self.started_at else datetime.now(timezone.utc).isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
