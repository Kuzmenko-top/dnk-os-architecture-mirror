# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_platform_region"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Multi-Region Platform Deployment (DNK-PLATFORM-SCALE-003)"
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
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class PlatformRegionModel(Base):
    __tablename__ = "platform_regions"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    region_name = Column(String(50), nullable=False, unique=True, index=True)
    cloud_provider = Column(String(20), nullable=False)  # 'aws', 'gcp', 'azure'
    is_primary = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    health_check_endpoint = Column(String(255), nullable=False)
    failover_priority = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    health_metrics = relationship(
        "PlatformRegionHealthMetricModel",
        back_populates="region",
        cascade="all, delete-orphan",
    )
    edge_routing_rules = relationship(
        "PlatformEdgeRoutingRuleModel",
        back_populates="region",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_platform_regions_provider", "cloud_provider"),
        Index("ix_platform_regions_active", "is_active"),
        Index("ix_platform_regions_primary", "is_primary"),
    )
