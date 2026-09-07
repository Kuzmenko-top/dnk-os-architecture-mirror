# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_platform_region_health_metric"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Region Health Metrics (DNK-PLATFORM-SCALE-003)"
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
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class PlatformRegionHealthMetricModel(Base):
    __tablename__ = "platform_region_health_metrics"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    region_name = Column(String(50), ForeignKey("platform_regions.region_name", ondelete="CASCADE"), nullable=False, index=True)
    metric_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    latency_p50_ms = Column(Integer, nullable=False, default=0)
    latency_p95_ms = Column(Integer, nullable=False, default=0)
    latency_p99_ms = Column(Integer, nullable=False, default=0)
    error_rate = Column(Numeric(5, 4), nullable=False, default=0.0)  # 0.0000 - 1.0000
    request_count = Column(Integer, nullable=False, default=0)
    health_score = Column(Numeric(3, 2), nullable=False, default=1.0)  # 0.00 - 1.00

    # Relationships
    region = relationship("PlatformRegionModel", back_populates="health_metrics")

    __table_args__ = (
        Index("ix_platform_region_health_metrics_region_time", "region_name", "metric_time"),
    )
