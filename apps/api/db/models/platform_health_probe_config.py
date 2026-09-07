# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_platform_health_probe_config"
# purpose: "SQLAlchemy 2.0 ORM Model for Health Probes & SLO Thresholds (DNK-PLATFORM-SCALE-004)"
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
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class PlatformHealthProbeConfigModel(Base):
    __tablename__ = "platform_health_probe_configs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = Column(String(128), ForeignKey("platform_deployment_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    probe_type = Column(String(50), nullable=False)  # 'liveness', 'readiness', 'startup', 'slo'
    endpoint_path = Column(String(255), nullable=False)
    probe_interval_seconds = Column(Integer, nullable=False, default=10)
    timeout_seconds = Column(Integer, nullable=False, default=5)
    failure_threshold = Column(Integer, nullable=False, default=3)
    slo_latency_p95_ms = Column(Integer, nullable=True)  # for SLO probes
    slo_latency_p99_ms = Column(Integer, nullable=True)  # for SLO probes
    slo_error_rate_threshold = Column(Float, nullable=True)  # e.g., 0.01 = 1%
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    config = relationship("PlatformDeploymentConfigModel", back_populates="health_probes")

    __table_args__ = (
        Index("ix_platform_probe_config_type", "config_id", "probe_type"),
    )
