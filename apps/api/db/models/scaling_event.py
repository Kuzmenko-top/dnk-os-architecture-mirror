# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_scaling_event"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Scaling Events Audit Log (DNK-PLATFORM-SCALE-002)"
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
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from apps.api.db.models.workspace import Base


class ScalingEventModel(Base):
    __tablename__ = "scaling_events"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    pool_id = Column(String(128), ForeignKey("worker_pools.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(20), nullable=False)  # scale_up, scale_down, drain, emergency_stop
    worker_count_before = Column(Integer, nullable=False)
    worker_count_after = Column(Integer, nullable=False)
    trigger_reason = Column(String(255), nullable=False)  # queue_depth, idle_timeout, manual, circuit_breaker
    triggered_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    metadata_json = Column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_scaling_events_pool_triggered", "pool_id", "triggered_at"),
    )
