# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_post_purchase_upsell_config"
# purpose: "SQLAlchemy ORM model for Post-Purchase Upsell Configurations (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Index, Integer, Float
from apps.api.db.models.workspace import Base


class ShopifyPostPurchaseUpsellConfigModel(Base):
    __tablename__ = "shopify_post_purchase_upsell_configs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), nullable=False, index=True)
    checkout_config_id = Column(String(64), nullable=True)
    offer_name = Column(String(255), nullable=False)
    upsell_type = Column(String(30), nullable=False)  # 'one_click_addon', 'cross_sell', 'order_bump'
    product_ids = Column(JSON, nullable=False, default=list)  # list of target product ids/handles
    discount_percentage = Column(Float, nullable=False, default=0.0)
    max_uses_per_customer = Column(Integer, nullable=False, default=1)
    liquid_template_snippet = Column(String(4096), nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_shopify_upsell_ws", "workspace_id"),
        Index("ix_shopify_upsell_type", "workspace_id", "upsell_type"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "checkout_config_id": self.checkout_config_id,
            "offer_name": self.offer_name,
            "upsell_type": self.upsell_type,
            "product_ids": self.product_ids,
            "discount_percentage": self.discount_percentage,
            "max_uses_per_customer": self.max_uses_per_customer,
            "liquid_template_snippet": self.liquid_template_snippet,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
