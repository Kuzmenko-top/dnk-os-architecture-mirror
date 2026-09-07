# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_post_purchase_offer"
# purpose: "SQLAlchemy ORM model for Post-Purchase Upsell Offer entity (DNK-ECOM-006 Phase 1)"
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
    Integer,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    Index,
    CheckConstraint
)

from apps.api.db.models.workspace import Base


class PostPurchaseOfferModel(Base):
    __tablename__ = "post_purchase_offers"

    id = Column(String(128), primary_key=True, nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_domain = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    headline = Column(String(512), nullable=False)
    product_id = Column(String(128), nullable=False)
    variant_id = Column(String(128), nullable=True)
    discount_type = Column(String(32), nullable=False, default="percentage")  # percentage, fixed_amount, free_shipping
    discount_value = Column(Float, nullable=False, default=15.0)
    original_price = Column(Float, nullable=False, default=0.0)
    offer_price = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), nullable=False, default="USD")
    priority = Column(Integer, nullable=False, default=1)
    status = Column(String(32), nullable=False, default="active")  # active, paused, draft
    trigger_rules = Column(JSON, nullable=True, default=dict)
    timer_seconds = Column(Integer, nullable=False, default=300)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'draft')", name="check_post_purchase_offer_status"),
        CheckConstraint("discount_type IN ('percentage', 'fixed_amount', 'free_shipping')", name="check_post_purchase_discount_type"),
        CheckConstraint("discount_value >= 0.0", name="check_post_purchase_discount_value_positive"),
        Index("idx_post_purchase_shop_status", "shop_domain", "status"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "shop_domain": self.shop_domain,
            "name": self.name,
            "headline": self.headline,
            "product_id": self.product_id,
            "variant_id": self.variant_id,
            "discount_type": self.discount_type,
            "discount_value": self.discount_value,
            "original_price": self.original_price,
            "offer_price": self.offer_price,
            "currency": self.currency,
            "priority": self.priority,
            "status": self.status,
            "trigger_rules": self.trigger_rules or {},
            "timer_seconds": self.timer_seconds,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
