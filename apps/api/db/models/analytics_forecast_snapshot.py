# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_forecast_snapshot"
# purpose: "SQLAlchemy 2.0 ORM Model for Predictive Analytics Forecast Snapshots (p10, p50, p90 confidence bands)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    DateTime,
    ForeignKey,
    Index,
)
from apps.api.db.models.workspace import Base


class AnalyticsForecastSnapshotModel(Base):
    __tablename__ = "analytics_forecast_snapshots"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # 'queue_depth', 'worker_count', 'latency_p95', 'error_rate'
    forecast_horizon_minutes = Column(Integer, nullable=False)  # 15, 60, 360, 1440
    predicted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    target_time = Column(DateTime(timezone=True), nullable=False)
    predicted_value = Column(Numeric(10, 4), nullable=False)
    confidence_p10 = Column(Numeric(10, 4), nullable=False)
    confidence_p50 = Column(Numeric(10, 4), nullable=False)
    confidence_p90 = Column(Numeric(10, 4), nullable=False)
    model_used = Column(String(50), nullable=False)  # 'linear', 'polynomial', 'holt_winters', 'arima', 'ensemble'
    confidence_score = Column(Numeric(3, 2), nullable=False, default=1.00)  # 0.00 – 1.00
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_analytics_forecast_snapshots_ws_metric", "workspace_id", "metric_type"),
        Index("ix_analytics_forecast_snapshots_ws_target", "workspace_id", "target_time"),
    )
