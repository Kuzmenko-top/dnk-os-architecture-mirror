# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-MODEL-ANOMALY-ALERT"
# purpose: "Anomaly Alert ORM Model for Real-Time Outlier and Spike Tracking"
# canonical_source: true
# alters_files: ["apps/api/db/models/anomaly_alert.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, Float
from apps.api.db.models.workspace import Base


class AnomalyAlert(Base):
    """Represents detected operational anomalies and outliers in cluster telemetry."""
    __tablename__ = "anomaly_alerts"

    id = Column(String(64), primary_key=True, default=lambda: f"alt_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    cluster_id = Column(String(64), nullable=False, default="default-cluster", index=True)
    anomaly_type = Column(String(64), nullable=False, default="spike", index=True)  # spike, drift, starvation, threshold_breach
    severity = Column(String(32), nullable=False, default="warning", index=True)  # info, warning, critical
    metric_name = Column(String(64), nullable=False, default="cpu_utilization")
    detected_value = Column(Float, nullable=False, default=0.0)
    expected_value = Column(Float, nullable=False, default=0.0)
    z_score = Column(Float, nullable=False, default=0.0)
    description = Column(String(512), nullable=False, default="")
    suggested_action = Column(String(512), nullable=False, default="")
    status = Column(String(32), nullable=False, default="open", index=True)  # open, resolved, dismissed
    detected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "cluster_id": self.cluster_id,
            "anomaly_type": self.anomaly_type,
            "severity": self.severity,
            "metric_name": self.metric_name,
            "detected_value": float(self.detected_value or 0.0),
            "expected_value": float(self.expected_value or 0.0),
            "z_score": float(self.z_score or 0.0),
            "description": self.description,
            "suggested_action": self.suggested_action,
            "status": self.status,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
