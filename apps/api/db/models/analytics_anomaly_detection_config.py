# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_anomaly_detection_config"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Anomaly Detection Configs (DNK-ANALYTICS-004)"
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
    Boolean,
    Float,
    Integer,
    DateTime,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class AnalyticsAnomalyDetectionConfigModel(Base):
    __tablename__ = "analytics_anomaly_detection_configs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)  # 'latency_p95', 'error_rate', 'queue_depth', 'request_count'
    detector_type = Column(String(20), nullable=False)  # 'zscore', 'iqr', 'holt_winters', 'isolation_forest'
    sensitivity = Column(Float, nullable=False, default=0.80)  # 0.00 - 1.00
    rolling_window_hours = Column(Integer, nullable=False, default=24)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    dynamic_thresholds = relationship(
        "AnalyticsDynamicThresholdModel",
        back_populates="config",
        cascade="all, delete-orphan",
    )
    anomaly_events = relationship(
        "AnalyticsAnomalyEventModel",
        back_populates="config",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_anom_det_conf_ws_metric", "workspace_id", "metric_type"),
        Index("ix_anom_det_conf_detector", "detector_type"),
        Index("ix_anom_det_conf_enabled", "enabled"),
    )
