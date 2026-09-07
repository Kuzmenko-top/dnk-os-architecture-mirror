# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_alert_channel_config"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Alert Channel Configs (DNK-ANALYTICS-004)"
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
    DateTime,
    Index,
    ForeignKey,
    JSON,
)

from apps.api.db.models.workspace import Base


class AnalyticsAlertChannelConfigModel(Base):
    __tablename__ = "analytics_alert_channel_configs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    channel_type = Column(String(20), nullable=False)  # 'telegram', 'slack', 'pagerduty', 'email'
    channel_config = Column(JSON, nullable=False, default=dict)  # webhook_url, bot_token, chat_id, recipients
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_alert_channel_ws_type", "workspace_id", "channel_type"),
        Index("ix_alert_channel_enabled", "enabled"),
    )
