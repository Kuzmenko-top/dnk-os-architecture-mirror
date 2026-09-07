# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_worker_pool"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Worker Pools (DNK-PLATFORM-SCALE-002)"
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


class WorkerPoolModel(Base):
    __tablename__ = "worker_pools"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    min_workers = Column(Integer, nullable=False, default=1)
    max_workers = Column(Integer, nullable=False, default=10)
    target_queue_depth = Column(Integer, nullable=False, default=50)
    scale_up_threshold = Column(Integer, nullable=False, default=80)
    scale_down_idle_seconds = Column(Integer, nullable=False, default=300)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_worker_pools_workspace_id", "workspace_id"),
        Index("ix_worker_pools_name", "name"),
    )
