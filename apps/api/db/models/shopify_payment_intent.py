# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_payment_intent"
# purpose: "SQLAlchemy ORM model for Tracking Payment Intents and 3DS States (DNK-ECOM-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Integer, DateTime, JSON, Index, Boolean
from apps.api.db.models.workspace import Base


class ShopifyPaymentIntentModel(Base):
    __tablename__ = "shopify_payment_intents"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), nullable=False, index=True)
    order_id = Column(String(255), nullable=False, index=True)
    gateway_type = Column(String(30), nullable=False)  # 'stripe', 'shopify_payments', 'coinbase'
    payment_intent_id = Column(String(255), nullable=False, unique=True, index=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(30), nullable=False, default="pending")  # 'pending', 'requires_action', 'succeeded', 'failed', 'refunded'
    customer_email = Column(String(255), nullable=True)
    requires_3ds = Column(Boolean, nullable=False, default=False)
    three_ds_action_url = Column(String(1024), nullable=True)
    client_secret = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_shopify_pi_ws_order", "workspace_id", "order_id"),
        Index("ix_shopify_pi_status", "workspace_id", "status"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "order_id": self.order_id,
            "gateway_type": self.gateway_type,
            "payment_intent_id": self.payment_intent_id,
            "amount_cents": self.amount_cents,
            "currency": self.currency,
            "status": self.status,
            "customer_email": self.customer_email,
            "requires_3ds": self.requires_3ds,
            "three_ds_action_url": self.three_ds_action_url,
            "client_secret": self.client_secret,
            "metadata": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
