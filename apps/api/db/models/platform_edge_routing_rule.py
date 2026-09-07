# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_platform_edge_routing_rule"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Edge Routing Rules (DNK-PLATFORM-SCALE-003)"
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
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from apps.api.db.models.workspace import Base


class PlatformEdgeRoutingRuleModel(Base):
    __tablename__ = "platform_edge_routing_rules"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_name = Column(String(255), nullable=False)
    geo_match_type = Column(String(20), nullable=False, default="country")  # 'country', 'continent', 'latency'
    geo_values = Column(JSON, nullable=False, default=list)  # ['US', 'CA'] or ['NA', 'EU']
    target_region = Column(String(50), ForeignKey("platform_regions.region_name", ondelete="CASCADE"), nullable=False, index=True)
    priority = Column(Integer, nullable=False, default=0)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    region = relationship("PlatformRegionModel", back_populates="edge_routing_rules")

    __table_args__ = (
        Index("ix_platform_edge_routing_rules_target", "target_region"),
        Index("ix_platform_edge_routing_rules_priority", "priority"),
        Index("ix_platform_edge_routing_rules_enabled", "enabled"),
    )
