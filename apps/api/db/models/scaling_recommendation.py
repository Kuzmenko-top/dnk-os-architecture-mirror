# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-MODEL-SCALING-RECOMMENDATION"
# purpose: "Scaling Recommendation ORM Model for Autonomous Horizontal Cluster Scaling"
# canonical_source: true
# alters_files: ["apps/api/db/models/scaling_recommendation.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, Float, Integer
from apps.api.db.models.workspace import Base


class ScalingRecommendation(Base):
    """Represents ML-driven recommendations for horizontal worker scaling."""
    __tablename__ = "scaling_recommendations"

    id = Column(String(64), primary_key=True, default=lambda: f"rec_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    cluster_id = Column(String(64), nullable=False, default="default-cluster", index=True)
    recommendation_type = Column(String(32), nullable=False, default="scale_out", index=True)  # scale_out, scale_in, rebalance
    current_replicas = Column(Integer, nullable=False, default=1)
    recommended_replicas = Column(Integer, nullable=False, default=2)
    target_metric = Column(String(64), nullable=False, default="cpu_utilization")
    estimated_cost_delta_usd_per_hour = Column(Float, nullable=False, default=0.0)
    rationale = Column(String(512), nullable=False, default="")
    urgency = Column(String(32), nullable=False, default="medium")  # low, medium, high, critical
    status = Column(String(32), nullable=False, default="pending", index=True)  # pending, approved, executed, dismissed
    recommended_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "cluster_id": self.cluster_id,
            "recommendation_type": self.recommendation_type,
            "current_replicas": int(self.current_replicas or 0),
            "recommended_replicas": int(self.recommended_replicas or 0),
            "target_metric": self.target_metric,
            "estimated_cost_delta_usd_per_hour": float(self.estimated_cost_delta_usd_per_hour or 0.0),
            "rationale": self.rationale,
            "urgency": self.urgency,
            "status": self.status,
            "recommended_at": self.recommended_at.isoformat() if self.recommended_at else None,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
