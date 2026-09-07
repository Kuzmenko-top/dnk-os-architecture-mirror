# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_worker_instance"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Worker Instances (DNK-PLATFORM-SCALE-002)"
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
    Index,
)
from apps.api.db.models.workspace import Base


class WorkerInstanceModel(Base):
    __tablename__ = "worker_instances"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    pool_id = Column(String(128), ForeignKey("worker_pools.id", ondelete="CASCADE"), nullable=False, index=True)
    worker_id = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False, default="starting")  # starting, running, draining, stopped
    last_heartbeat = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    tasks_completed = Column(Integer, nullable=False, default=0)
    tasks_failed = Column(Integer, nullable=False, default=0)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    stopped_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_worker_instances_pool_status", "pool_id", "status"),
    )
