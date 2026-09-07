# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_alert_rule"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Workspace Alerting Rules"
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
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from apps.api.db.models.workspace import Base


class AnalyticsAlertRuleModel(Base):
    __tablename__ = "analytics_alert_rules"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    metric_type = Column(String(50), nullable=False)  # 'error_rate', 'latency_p95', 'inactivity', 'resource'
    operator = Column(String(10), nullable=False)  # 'gt', 'lt', 'gte', 'lte', 'eq'
    threshold_value = Column(Numeric(10, 4), nullable=False)
    window_seconds = Column(Integer, nullable=False, default=300)
    composite_logic = Column(JSON, nullable=True)  # {"and": [...], "or": [...]}
    severity = Column(String(20), nullable=False, default="warning")  # 'info', 'warning', 'critical'
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_analytics_alert_rules_ws_metric", "workspace_id", "metric_type"),
        Index("ix_analytics_alert_rules_ws_enabled", "workspace_id", "enabled"),
    )
