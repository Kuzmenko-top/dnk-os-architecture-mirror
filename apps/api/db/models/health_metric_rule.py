# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_health_metric_rule"
# purpose: "ORM Model for Health Metric Threshold Rules (DNK-HEALTH-001 Phase 1)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON
from apps.api.db.models.workspace import Base


class HealthMetricRule(Base):
    __tablename__ = "health_metric_rules"

    id = Column(String(64), primary_key=True, default=lambda: f"hmr_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    service_name = Column(String(128), nullable=False, index=True)
    metric_name = Column(String(128), nullable=False, index=True)  # e.g., cpu_usage_pct, p95_latency_ms, error_rate_pct
    comparator = Column(String(8), nullable=False, default=">")    # >, >=, <, <=, ==, !=
    warning_threshold = Column(Float, nullable=False)
    critical_threshold = Column(Float, nullable=False)
    evaluation_window_seconds = Column(Integer, default=60)
    consecutive_breaches_required = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    labels = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"hmr_{uuid.uuid4().hex[:12]}"
        if getattr(self, "is_active", None) is None:
            self.is_active = True
        if getattr(self, "labels", None) is None:
            self.labels = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id or f"hmr_{uuid.uuid4().hex[:12]}",
            "workspace_id": self.workspace_id or "ws-default",
            "service_name": self.service_name,
            "metric_name": self.metric_name,
            "comparator": self.comparator or ">",
            "warning_threshold": self.warning_threshold,
            "critical_threshold": self.critical_threshold,
            "evaluation_window_seconds": self.evaluation_window_seconds or 60,
            "consecutive_breaches_required": self.consecutive_breaches_required or 3,
            "is_active": self.is_active if self.is_active is not None else True,
            "labels": self.labels or {},
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else datetime.now(timezone.utc).isoformat(),
        }
