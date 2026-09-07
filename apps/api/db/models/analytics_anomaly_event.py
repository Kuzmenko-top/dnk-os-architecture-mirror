# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_anomaly_event"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Anomaly Events (DNK-ANALYTICS-004)"
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
    DateTime,
    Index,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class AnalyticsAnomalyEventModel(Base):
    __tablename__ = "analytics_anomaly_events"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = Column(String(128), ForeignKey("analytics_anomaly_detection_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    metric_value = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=False, default=0.0)  # 0.00 - 1.00
    detector_used = Column(String(20), nullable=False)
    threshold_lower = Column(Float, nullable=True)
    threshold_upper = Column(Float, nullable=True)
    is_anomalous = Column(Boolean, nullable=False, default=True)
    event_metadata = Column("metadata", JSON, nullable=True, default=dict)

    # Relationships
    config = relationship("AnalyticsAnomalyDetectionConfigModel", back_populates="anomaly_events")

    __table_args__ = (
        Index("ix_anom_event_ws_detected", "workspace_id", "detected_at"),
        Index("ix_anom_event_config_detected", "config_id", "detected_at"),
        Index("ix_anom_event_is_anomalous", "is_anomalous"),
    )
