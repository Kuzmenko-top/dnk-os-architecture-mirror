# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_checkout_conversion_event"
# purpose: "SQLAlchemy ORM model for Checkout & Post-Purchase Conversion Tracking (DNK-ECOM-006 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    Index,
    CheckConstraint
)

from apps.api.db.models.workspace import Base


class CheckoutConversionEventModel(Base):
    __tablename__ = "checkout_conversion_events"

    id = Column(String(128), primary_key=True, nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_domain = Column(String(255), nullable=False, index=True)
    checkout_token = Column(String(255), nullable=False, index=True)
    order_id = Column(String(128), nullable=True, index=True)
    offer_id = Column(String(128), nullable=True, index=True)
    extension_id = Column(String(128), nullable=True, index=True)
    event_type = Column(String(64), nullable=False)  # IMPRESSION, CLICK, ACCEPT, DECLINE, CHECKOUT_COMPLETED
    channel = Column(String(64), nullable=False, default="checkout_ui")  # checkout_ui, post_purchase, thank_you
    revenue_impact = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default="USD")
    metadata_payload = Column(JSON, nullable=True, default=dict)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('IMPRESSION', 'CLICK', 'ACCEPT', 'DECLINE', 'CHECKOUT_COMPLETED')",
            name="check_conversion_event_type"
        ),
        Index("idx_conv_event_shop_time", "shop_domain", "timestamp"),
        Index("idx_conv_event_offer_type", "offer_id", "event_type"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "shop_domain": self.shop_domain,
            "checkout_token": self.checkout_token,
            "order_id": self.order_id,
            "offer_id": self.offer_id,
            "extension_id": self.extension_id,
            "event_type": self.event_type,
            "channel": self.channel,
            "revenue_impact": self.revenue_impact,
            "currency": self.currency,
            "metadata_payload": self.metadata_payload or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
