# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_platform_canary_analysis_result"
# purpose: "SQLAlchemy 2.0 ORM Model for Canary Statistical Analysis Results (DNK-PLATFORM-SCALE-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
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
    Text,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class PlatformCanaryAnalysisResultModel(Base):
    __tablename__ = "platform_canary_analysis_results"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = Column(String(128), ForeignKey("platform_deployment_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    blue_metric_snapshot = Column(JSON, nullable=False)  # {latency_p50, latency_p95, latency_p99, error_rate, request_count}
    green_metric_snapshot = Column(JSON, nullable=False)
    statistical_test = Column(String(50), nullable=False, default="mann_whitney_u")  # 'mann_whitney_u', 't_test', 'threshold'
    p_value = Column(Float, nullable=True)
    is_significant = Column(Boolean, nullable=False, default=False)
    recommendation = Column(String(50), nullable=False, default="wait")  # 'promote', 'rollback', 'wait'
    analysis_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    config = relationship("PlatformDeploymentConfigModel", back_populates="analysis_results")

    __table_args__ = (
        Index("ix_platform_canary_analysis_config_time", "config_id", "analysis_time"),
    )
