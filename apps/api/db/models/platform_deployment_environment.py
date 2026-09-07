# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_platform_deployment_environment"
# purpose: "SQLAlchemy 2.0 ORM Model for Deployment Environments (Blue/Green/Canary) (DNK-PLATFORM-SCALE-004)"
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
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class PlatformDeploymentEnvironmentModel(Base):
    __tablename__ = "platform_deployment_environments"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = Column(String(128), ForeignKey("platform_deployment_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    environment_name = Column(String(50), nullable=False)  # 'blue', 'green', 'canary'
    kubernetes_namespace = Column(String(255), nullable=False, default="default")
    kubernetes_service_name = Column(String(255), nullable=False)
    image_tag = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="inactive")  # 'active', 'inactive', 'deploying', 'rolling_back'
    traffic_percentage = Column(Integer, nullable=False, default=0)
    deployed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    config = relationship("PlatformDeploymentConfigModel", back_populates="environments")

    __table_args__ = (
        Index("ix_platform_deploy_env_config_name", "config_id", "environment_name"),
    )
