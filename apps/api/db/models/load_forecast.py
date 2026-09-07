# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-MODEL-LOAD-FORECAST"
# purpose: "Load Forecast ORM Model for Predictive Time-Series Analytics"
# canonical_source: true
# alters_files: ["apps/api/db/models/load_forecast.py"]
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


class LoadForecast(Base):
    """Represents ML-driven time-series predictions for capacity planning."""
    __tablename__ = "load_forecasts"

    id = Column(String(64), primary_key=True, default=lambda: f"fc_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    cluster_id = Column(String(64), nullable=False, default="default-cluster", index=True)
    metric_name = Column(String(64), nullable=False, index=True)  # e.g., 'cpu', 'memory', 'tokens', 'queue'
    forecast_horizon = Column(String(32), nullable=False, default="1h")  # '15m', '1h', '24h', '7d'
    predicted_value_p50 = Column(Float, nullable=False, default=0.0)
    predicted_value_p90 = Column(Float, nullable=False, default=0.0)
    predicted_value_p99 = Column(Float, nullable=False, default=0.0)
    confidence_score = Column(Float, nullable=False, default=0.95)
    model_algorithm = Column(String(64), nullable=False, default="holt_winters")
    forecast_series = Column(JSON, nullable=False, default=list)  # list of {timestamp, p50, p90, p99}
    forecast_generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "cluster_id": self.cluster_id,
            "metric_name": self.metric_name,
            "forecast_horizon": self.forecast_horizon,
            "predicted_value_p50": float(self.predicted_value_p50 or 0.0),
            "predicted_value_p90": float(self.predicted_value_p90 or 0.0),
            "predicted_value_p99": float(self.predicted_value_p99 or 0.0),
            "confidence_score": float(self.confidence_score or 0.0),
            "model_algorithm": self.model_algorithm,
            "forecast_series": self.forecast_series or [],
            "forecast_generated_at": self.forecast_generated_at.isoformat() if self.forecast_generated_at else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
