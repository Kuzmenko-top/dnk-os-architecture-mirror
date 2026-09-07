# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_dynamic_discount_rule"
# purpose: "SQLAlchemy ORM model for Shopify Dynamic Discount Rules (DNK-ECOM-005)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Float, Integer, Index
from apps.api.db.models.workspace import Base


class ShopifyDynamicDiscountRuleModel(Base):
    __tablename__ = "shopify_dynamic_discount_rules"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), nullable=False, index=True)
    function_id = Column(String(128), nullable=False, index=True)
    discount_title = Column(String(255), nullable=False)
    discount_type = Column(String(64), nullable=False)  # tiered_volume, b2b_wholesale, vip_customer, bxgy
    conditions = Column(JSON, nullable=False, default=dict)  # min_quantity, min_subtotal_cents, customer_tags, product_ids
    discount_value_type = Column(String(32), nullable=False, default="percentage")  # percentage, fixed_amount
    discount_value = Column(Float, nullable=False, default=0.0)
    max_applications = Column(Integer, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_shopify_disc_rule_ws", "workspace_id"),
        Index("ix_shopify_disc_rule_fn", "workspace_id", "function_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "function_id": self.function_id,
            "discount_title": self.discount_title,
            "discount_type": self.discount_type,
            "conditions": self.conditions,
            "discount_value_type": self.discount_value_type,
            "discount_value": self.discount_value,
            "max_applications": self.max_applications,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
