# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_task_dlq"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Dead Letter Queue (DNK-PLATFORM-SCALE-002)"
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
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from apps.api.db.models.workspace import Base


class TaskDLQModel(Base):
    __tablename__ = "task_dlq"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_task_id = Column(String(128), nullable=False, index=True)
    queue_id = Column(String(128), ForeignKey("task_queues.id", ondelete="SET NULL"), nullable=True, index=True)
    error_message = Column(Text, nullable=False)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False, default="failed")  # failed, retrying, resolved, purged
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_task_dlq_status_created", "status", "created_at"),
    )
