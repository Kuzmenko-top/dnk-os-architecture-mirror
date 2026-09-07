# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_dynamic_threshold"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Dynamic Thresholds (DNK-ANALYTICS-004)"
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
    Float,
    Integer,
    DateTime,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class AnalyticsDynamicThresholdModel(Base):
    __tablename__ = "analytics_dynamic_thresholds"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = Column(String(128), ForeignKey("analytics_anomaly_detection_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    calculated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    rolling_window_hours = Column(Integer, nullable=False, default=24)
    mean_value = Column(Float, nullable=False, default=0.0)
    std_value = Column(Float, nullable=False, default=0.0)
    percentile_p10 = Column(Float, nullable=False, default=0.0)
    percentile_p50 = Column(Float, nullable=False, default=0.0)
    percentile_p90 = Column(Float, nullable=False, default=0.0)
    lower_bound = Column(Float, nullable=False, default=0.0)
    upper_bound = Column(Float, nullable=False, default=0.0)

    # Relationships
    config = relationship("AnalyticsAnomalyDetectionConfigModel", back_populates="dynamic_thresholds")

    __table_args__ = (
        Index("ix_dyn_thresh_config_calc", "config_id", "calculated_at"),
    )
