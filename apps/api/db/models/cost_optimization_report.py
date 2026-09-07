# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-MODEL-COST-OPTIMIZATION"
# purpose: "Cost Optimization Report ORM Model for Workload Expenditure & Spot Analytics"
# canonical_source: true
# alters_files: ["apps/api/db/models/cost_optimization_report.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Float
from apps.api.db.models.workspace import Base


class CostOptimizationReport(Base):
    """Represents infrastructure expenditure analysis and cost-reduction opportunities."""
    __tablename__ = "cost_optimization_reports"

    id = Column(String(64), primary_key=True, default=lambda: f"cost_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    cluster_id = Column(String(64), nullable=False, default="default-cluster", index=True)
    billing_period = Column(String(32), nullable=False, default="daily")  # hourly, daily, monthly
    current_spend_usd = Column(Float, nullable=False, default=0.0)
    optimized_spend_usd = Column(Float, nullable=False, default=0.0)
    potential_savings_usd = Column(Float, nullable=False, default=0.0)
    savings_percentage = Column(Float, nullable=False, default=0.0)
    spot_instance_ratio = Column(Float, nullable=False, default=0.0)
    idle_resource_cost_usd = Column(Float, nullable=False, default=0.0)
    optimization_opportunities = Column(JSON, nullable=False, default=list)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "cluster_id": self.cluster_id,
            "billing_period": self.billing_period,
            "current_spend_usd": float(self.current_spend_usd or 0.0),
            "optimized_spend_usd": float(self.optimized_spend_usd or 0.0),
            "potential_savings_usd": float(self.potential_savings_usd or 0.0),
            "savings_percentage": float(self.savings_percentage or 0.0),
            "spot_instance_ratio": float(self.spot_instance_ratio or 0.0),
            "idle_resource_cost_usd": float(self.idle_resource_cost_usd or 0.0),
            "optimization_opportunities": self.optimization_opportunities or [],
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
