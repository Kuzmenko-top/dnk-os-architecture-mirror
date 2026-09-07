# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_webhook_event"
# purpose: "SQLAlchemy ORM model for Shopify Webhook Event Ingestion & Idempotency (DNK-ECOM-006 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    JSON,
    ForeignKey,
    Index,
    CheckConstraint
)

from apps.api.db.models.workspace import Base


class ShopifyWebhookEventModel(Base):
    __tablename__ = "shopify_webhook_events"

    id = Column(String(128), primary_key=True, nullable=False, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_domain = Column(String(255), nullable=False, default="default.myshopify.com", index=True)
    webhook_id = Column(String(128), nullable=False, default=lambda: f"wh_{uuid.uuid4().hex[:12]}", index=True)
    topic = Column(String(128), nullable=True, index=True)  # e.g., 'orders/create', 'checkouts/update'
    event_type = Column(String(128), nullable=True, index=True)  # alias for topic compatibility
    api_version = Column(String(32), nullable=False, default="2026-04")
    hmac_verified = Column(Integer, nullable=False, default=1)  # 1 = True, 0 = False
    status = Column(String(32), nullable=False, default="processed")  # pending, processed, failed, skipped
    processing_status = Column(String(32), nullable=True, default="pending")  # legacy compatibility field
    error_message = Column(String(1024), nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_webhook_shop_topic", "shop_domain", "topic"),
    )

    def __init__(self, **kwargs):
        if "event_type" in kwargs and "topic" not in kwargs:
            kwargs["topic"] = kwargs["event_type"]
        elif "topic" in kwargs and "event_type" not in kwargs:
            kwargs["event_type"] = kwargs["topic"]
        if "processing_status" in kwargs and "status" not in kwargs:
            kwargs["status"] = kwargs["processing_status"]
        if "id" not in kwargs:
            kwargs["id"] = str(uuid.uuid4())
        if "workspace_id" in kwargs:
            kwargs["workspace_id"] = str(kwargs["workspace_id"])
        super().__init__(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "workspace_id": str(self.workspace_id),
            "shop_domain": self.shop_domain,
            "webhook_id": self.webhook_id,
            "topic": self.topic or self.event_type,
            "event_type": self.event_type or self.topic,
            "api_version": self.api_version,
            "hmac_verified": bool(self.hmac_verified),
            "status": self.status or self.processing_status,
            "processing_status": self.processing_status or self.status,
            "error_message": self.error_message,
            "payload": self.payload,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
