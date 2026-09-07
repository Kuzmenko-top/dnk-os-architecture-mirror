# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_checkout_extension_config"
# purpose: "SQLAlchemy ORM model for Shopify Checkout UI & Extension Configs (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Index, ForeignKey
from sqlalchemy.orm import relationship
from apps.api.db.models.workspace import Base


class ShopifyCheckoutExtensionConfigModel(Base):
    __tablename__ = "shopify_checkout_extension_configs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), nullable=False, index=True)
    extension_name = Column(String(255), nullable=False)
    extension_type = Column(String(50), nullable=False)  # 'checkout_ui', 'post_purchase', 'payment_gateway'
    shopify_app_id = Column(String(100), nullable=False)
    api_version = Column(String(20), nullable=False, default="2024-07")
    target_placement = Column(String(100), nullable=True, default="purchase.checkout.shipping-option-list.render-after")
    custom_fields_schema = Column(JSON, nullable=False, default=dict)  # field definitions, validation rules
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_shopify_checkout_ext_ws", "workspace_id"),
        Index("ix_shopify_checkout_ext_type", "workspace_id", "extension_type"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "extension_name": self.extension_name,
            "extension_type": self.extension_type,
            "shopify_app_id": self.shopify_app_id,
            "api_version": self.api_version,
            "target_placement": self.target_placement,
            "custom_fields_schema": self.custom_fields_schema,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
