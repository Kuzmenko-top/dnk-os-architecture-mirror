# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_platform_replication_status"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Cross-Region Replication Status (DNK-PLATFORM-SCALE-003)"
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
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class PlatformReplicationStatusModel(Base):
    __tablename__ = "platform_replication_status"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_region = Column(String(50), ForeignKey("platform_regions.region_name", ondelete="CASCADE"), nullable=False, index=True)
    target_region = Column(String(50), ForeignKey("platform_regions.region_name", ondelete="CASCADE"), nullable=False, index=True)
    replication_type = Column(String(20), nullable=False, default="logical")  # 'sync', 'async', 'logical'
    lag_seconds = Column(Integer, nullable=False, default=0)
    last_sync_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    status = Column(String(20), nullable=False, default="healthy")  # 'healthy', 'lagging', 'broken'
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_platform_replication_status_source", "source_region"),
        Index("ix_platform_replication_status_target", "target_region"),
        Index("ix_platform_replication_status_status", "status"),
    )
