# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_alert_event"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Workspace Alert Events (Immutable Audit Log)"
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
    Numeric,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index,
)
from apps.api.db.models.workspace import Base


class AnalyticsAlertEventModel(Base):
    __tablename__ = "analytics_alert_events"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(128), ForeignKey("analytics_alert_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    triggered_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    metric_value = Column(Numeric(10, 4), nullable=False)
    threshold_value = Column(Numeric(10, 4), nullable=False)
    severity = Column(String(20), nullable=False)  # 'info', 'warning', 'critical'
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_note = Column(Text, nullable=True)
    metadata_context = Column(JSON, nullable=True)  # snapshot of metric context

    __table_args__ = (
        Index("ix_analytics_alert_events_ws_time", "workspace_id", "triggered_at"),
        Index("ix_analytics_alert_events_rule_time", "rule_id", "triggered_at"),
    )
