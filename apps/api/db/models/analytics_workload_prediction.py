# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_workload_prediction"
# purpose: "SQLAlchemy 2.0 ORM Model for Workload Predictions and Proactive Scaling Triggers"
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
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from apps.api.db.models.workspace import Base


class AnalyticsWorkloadPredictionModel(Base):
    __tablename__ = "analytics_workload_predictions"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    pool_id = Column(String(128), ForeignKey("worker_pools.id", ondelete="CASCADE"), nullable=True, index=True)
    predicted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    target_time = Column(DateTime(timezone=True), nullable=False)
    predicted_queue_depth = Column(Integer, nullable=False)
    recommended_worker_count = Column(Integer, nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=False, default=1.00)
    triggered_scaling = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_analytics_workload_pred_ws_pool", "workspace_id", "pool_id"),
        Index("ix_analytics_workload_pred_target", "workspace_id", "target_time"),
    )
