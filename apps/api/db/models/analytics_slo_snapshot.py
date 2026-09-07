# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_analytics_slo_snapshot"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Rolling 24h SLA/SLO Snapshots"
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
    DateTime,
    ForeignKey,
    Index,
)
from apps.api.db.models.workspace import Base


class AnalyticsSLOSnapshotModel(Base):
    __tablename__ = "analytics_slo_snapshots"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    snapshot_time = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    uptime_percentage = Column(Numeric(5, 2), nullable=False)  # e.g., 99.95
    error_budget_remaining = Column(Numeric(5, 2), nullable=False)  # e.g., 0.45
    latency_p95_ms = Column(Integer, nullable=False)  # e.g., 187
    latency_slo_target_ms = Column(Integer, nullable=False, default=200)  # e.g., 200
    slo_status = Column(String(20), nullable=False)  # 'meeting', 'at_risk', 'breached'
    burn_rate = Column(Numeric(5, 2), nullable=False)  # e.g., 0.55

    __table_args__ = (
        Index("ix_analytics_slo_snapshots_ws_time", "workspace_id", "snapshot_time"),
        Index("ix_analytics_slo_snapshots_ws_status", "workspace_id", "slo_status"),
    )
