# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_platform_deployment_config"
# purpose: "SQLAlchemy 2.0 ORM Model for Blue/Green & Canary Deployment Configs (DNK-PLATFORM-SCALE-004)"
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
    Integer,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class PlatformDeploymentConfigModel(Base):
    __tablename__ = "platform_deployment_configs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    deployment_name = Column(String(255), nullable=False, index=True)
    deployment_strategy = Column(String(50), nullable=False, default="canary")  # 'blue_green', 'canary'
    blue_service_name = Column(String(255), nullable=False)
    green_service_name = Column(String(255), nullable=False)
    active_environment = Column(String(20), nullable=False, default="blue")  # 'blue', 'green'
    canary_enabled = Column(Boolean, nullable=False, default=False)
    canary_traffic_percentage = Column(Integer, nullable=False, default=0)  # 0-100
    canary_steps = Column(JSON, nullable=False, default=lambda: [1, 5, 25, 50, 100])
    auto_rollback_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    environments = relationship(
        "PlatformDeploymentEnvironmentModel",
        back_populates="config",
        cascade="all, delete-orphan",
    )
    health_probes = relationship(
        "PlatformHealthProbeConfigModel",
        back_populates="config",
        cascade="all, delete-orphan",
    )
    analysis_results = relationship(
        "PlatformCanaryAnalysisResultModel",
        back_populates="config",
        cascade="all, delete-orphan",
    )
    events = relationship(
        "PlatformDeploymentEventModel",
        back_populates="config",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_platform_deploy_workspace_name", "workspace_id", "deployment_name"),
    )
