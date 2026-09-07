# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_alert_rule_advanced"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Advanced Composite Alert Rules (DNK-ANALYTICS-004)"
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
    Integer,
    DateTime,
    Index,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class AnalyticsAlertRuleAdvancedModel(Base):
    __tablename__ = "analytics_alert_rules_advanced"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    composite_logic = Column(JSON, nullable=False, default=dict)  # {"and": [...]} or {"or": [...]}
    severity = Column(String(20), nullable=False, default="warning")  # 'info', 'warning', 'critical'
    cooldown_seconds = Column(Integer, nullable=False, default=300)  # 5 min
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    alert_events = relationship(
        "AnalyticsAlertEventAdvancedModel",
        back_populates="rule",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_alert_rules_adv_ws_enabled", "workspace_id", "enabled"),
        Index("ix_alert_rules_adv_severity", "severity"),
    )
