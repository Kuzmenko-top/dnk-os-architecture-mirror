# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_platform_deployment_event"
# purpose: "SQLAlchemy 2.0 ORM Model for Deployment Lifecycle Audit Events (DNK-PLATFORM-SCALE-004)"
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
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class PlatformDeploymentEventModel(Base):
    __tablename__ = "platform_deployment_events"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    config_id = Column(String(128), ForeignKey("platform_deployment_configs.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)  # 'deployment_started', 'canary_step_completed', 'auto_rollback_triggered', 'promotion_completed'
    event_details = Column(JSON, nullable=False, default=dict)
    triggered_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    triggered_by = Column(String(100), nullable=False, default="system")  # 'user', 'auto_rollback', 'canary_analysis', 'system'

    # Relationships
    config = relationship("PlatformDeploymentConfigModel", back_populates="events")

    __table_args__ = (
        Index("ix_platform_deploy_events_config_time", "config_id", "triggered_at"),
    )
