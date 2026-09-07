# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_auto_healing_policy"
# purpose: "ORM Model for Auto-Healing Recovery Policies (DNK-HEALTH-001 Phase 1)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON
from apps.api.db.models.workspace import Base


class AutoHealingPolicy(Base):
    __tablename__ = "auto_healing_policies"

    id = Column(String(64), primary_key=True, default=lambda: f"ahp_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    service_name = Column(String(128), nullable=False, index=True)
    incident_type = Column(String(128), nullable=False, index=True)
    remediation_playbook = Column(String(64), nullable=False)  # restart_service, drain_traffic, clear_cache, scale_replicas, trip_circuit_breaker
    max_retries = Column(Integer, default=3)
    cooldown_seconds = Column(Integer, default=300)
    flap_detection_window_s = Column(Integer, default=600)
    is_enabled = Column(Boolean, default=True)
    playbook_config = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"ahp_{uuid.uuid4().hex[:12]}"
        if getattr(self, "is_enabled", None) is None:
            self.is_enabled = True
        if getattr(self, "playbook_config", None) is None:
            self.playbook_config = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id or f"ahp_{uuid.uuid4().hex[:12]}",
            "workspace_id": self.workspace_id or "ws-default",
            "service_name": self.service_name,
            "incident_type": self.incident_type,
            "remediation_playbook": self.remediation_playbook,
            "max_retries": self.max_retries or 3,
            "cooldown_seconds": self.cooldown_seconds or 300,
            "flap_detection_window_s": self.flap_detection_window_s or 600,
            "is_enabled": self.is_enabled if self.is_enabled is not None else True,
            "playbook_config": self.playbook_config or {},
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else datetime.now(timezone.utc).isoformat(),
        }
