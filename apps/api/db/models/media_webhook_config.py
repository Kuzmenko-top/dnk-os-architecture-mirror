# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_media_webhook_config"
# purpose: "SQLAlchemy ORM Model for Media Webhook Configurations (DNK-MEDIA-002)"
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
    JSON,
    DateTime,
    ForeignKey,
    Index,
)

from apps.api.db.models.workspace import Base


class MediaWebhookConfigModel(Base):
    __tablename__ = "media_webhook_configs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    webhook_url = Column(String(512), nullable=False)
    event_types = Column(
        JSON,
        nullable=False,
        default=lambda: ["job.completed", "job.failed", "chunk.completed", "task.completed"],
    )
    secret_token = Column(String(255), nullable=True)  # For HMAC-SHA256 signature
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_media_webhook_workspace_enabled", "workspace_id", "enabled"),
    )
