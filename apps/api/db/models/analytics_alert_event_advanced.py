# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_alert_event_advanced"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Advanced Alert Events (DNK-ANALYTICS-004)"
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
    Text,
    DateTime,
    Index,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class AnalyticsAlertEventAdvancedModel(Base):
    __tablename__ = "analytics_alert_events_advanced"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(128), ForeignKey("analytics_alert_rules_advanced.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    triggered_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    severity = Column(String(20), nullable=False)
    channels_delivered = Column(JSON, nullable=False, default=list)  # ['telegram', 'slack', 'pagerduty', 'email']
    delivery_status = Column(JSON, nullable=False, default=dict)  # {"telegram": "sent", "slack": "failed"}
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSON, nullable=True, default=dict)

    # Relationships
    rule = relationship("AnalyticsAlertRuleAdvancedModel", back_populates="alert_events")

    __table_args__ = (
        Index("ix_alert_event_adv_ws_triggered", "workspace_id", "triggered_at"),
        Index("ix_alert_event_adv_rule_triggered", "rule_id", "triggered_at"),
        Index("ix_alert_event_adv_severity", "severity"),
    )
