# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_platform_gslb_config"
# purpose: "SQLAlchemy 2.0 ORM Declarative Model for Global Server Load Balancer Config (DNK-PLATFORM-SCALE-003)"
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
    Index,
)

from apps.api.db.models.workspace import Base


class PlatformGSLBConfigModel(Base):
    __tablename__ = "platform_gslb_configs"

    id = Column(String(128), primary_key=True, default=lambda: str(uuid.uuid4()))
    dns_provider = Column(String(20), nullable=False, default="route53")  # 'route53', 'cloud_dns', 'cloudflare'
    routing_policy = Column(String(20), nullable=False, default="latency")  # 'geolocation', 'latency', 'weighted', 'failover'
    health_check_interval_seconds = Column(Integer, nullable=False, default=30)
    failover_threshold = Column(Integer, nullable=False, default=3)
    ttl_seconds = Column(Integer, nullable=False, default=60)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_platform_gslb_configs_provider", "dns_provider"),
        Index("ix_platform_gslb_configs_policy", "routing_policy"),
    )
