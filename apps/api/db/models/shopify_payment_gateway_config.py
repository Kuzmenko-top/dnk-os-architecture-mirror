# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_payment_gateway_config"
# purpose: "SQLAlchemy ORM model for Payment Gateway Configurations (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Index, ForeignKey
from apps.api.db.models.workspace import Base


class ShopifyPaymentGatewayConfigModel(Base):
    __tablename__ = "shopify_payment_gateway_configs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), nullable=False, index=True)
    checkout_config_id = Column(String(64), nullable=True)
    gateway_type = Column(String(30), nullable=False)  # 'stripe', 'shopify_payments', 'coinbase'
    gateway_name = Column(String(100), nullable=False)
    gateway_config = Column(JSON, nullable=False, default=dict)  # encrypted/sanitized configs
    supported_methods = Column(JSON, nullable=False, default=list)  # ['card', 'apple_pay', 'crypto', 'native']
    is_test_mode = Column(Boolean, nullable=False, default=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_shopify_payment_gw_ws", "workspace_id"),
        Index("ix_shopify_payment_gw_type", "workspace_id", "gateway_type"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "checkout_config_id": self.checkout_config_id,
            "gateway_type": self.gateway_type,
            "gateway_name": self.gateway_name,
            "gateway_config": self.gateway_config,
            "supported_methods": self.supported_methods,
            "is_test_mode": self.is_test_mode,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
