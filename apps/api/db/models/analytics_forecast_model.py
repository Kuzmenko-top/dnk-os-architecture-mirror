# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_forecast_model"
# purpose: "SQLAlchemy 2.0 ORM Model for Predictive Analytics Forecast Model Configurations"
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
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from apps.api.db.models.workspace import Base


class AnalyticsForecastModelModel(Base):
    __tablename__ = "analytics_forecast_models"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)
    model_name = Column(String(50), nullable=False)  # 'linear', 'polynomial', 'holt_winters', 'arima', 'ensemble'
    model_params = Column(JSON, nullable=False, default=dict)  # hyperparameters
    training_window_days = Column(Integer, nullable=False, default=7)
    retrain_frequency_hours = Column(Integer, nullable=False, default=6)
    enabled = Column(Boolean, nullable=False, default=True)
    last_trained_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_analytics_forecast_models_ws_metric", "workspace_id", "metric_type"),
        Index("ix_analytics_forecast_models_ws_enabled", "workspace_id", "enabled"),
    )
