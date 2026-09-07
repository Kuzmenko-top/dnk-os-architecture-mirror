# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_forecast_accuracy"
# purpose: "SQLAlchemy 2.0 ORM Model for Forecast Accuracy Tracking (MAE, RMSE, MAPE, R2 Score)"
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


class AnalyticsForecastAccuracyModel(Base):
    __tablename__ = "analytics_forecast_accuracy"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_id = Column(String(128), ForeignKey("analytics_forecast_models.id", ondelete="CASCADE"), nullable=False, index=True)
    evaluation_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    mae = Column(Numeric(10, 4), nullable=False)  # Mean Absolute Error
    rmse = Column(Numeric(10, 4), nullable=False)  # Root Mean Squared Error
    mape = Column(Numeric(5, 2), nullable=False)  # Mean Absolute Percentage Error (%)
    r2_score = Column(Numeric(5, 4), nullable=False)  # R-squared score
    evaluation_window_hours = Column(Integer, nullable=False, default=24)

    __table_args__ = (
        Index("ix_analytics_forecast_acc_model_time", "model_id", "evaluation_time"),
    )
