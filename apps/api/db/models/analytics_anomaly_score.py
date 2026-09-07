# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_anomaly_score"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Time-Series Anomaly Detection Scores"
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


class AnalyticsAnomalyScoreModel(Base):
    __tablename__ = "analytics_anomaly_scores"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False)
    score = Column(Numeric(4, 3), nullable=False)  # 0.000 - 1.000
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    algorithm = Column(String(20), nullable=False)  # 'zscore', 'ewma', 'hybrid'
    window_seconds = Column(Integer, nullable=False, default=300)

    __table_args__ = (
        Index("ix_analytics_anomaly_scores_ws_time", "workspace_id", "detected_at"),
        Index("ix_analytics_anomaly_scores_ws_metric", "workspace_id", "metric_type"),
    )
