# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_task_queue"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Task Queues (DNK-PLATFORM-SCALE-002)"
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


class TaskQueueModel(Base):
    __tablename__ = "task_queues"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, default="default")
    priority = Column(Integer, nullable=False, default=1)  # 0 (P0: highest) to 3 (P3: lowest)
    tenant_partition = Column(String(255), nullable=True)
    max_rate_per_second = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_task_queues_ws_priority", "workspace_id", "priority"),
    )
