# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_checkout_extension"
# purpose: "SQLAlchemy ORM model for Checkout Extension entity (DNK-ECOM-006 Phase 1)"
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
    DateTime,
    JSON,
    ForeignKey,
    Index,
    CheckConstraint
)

from apps.api.db.models.workspace import Base


class CheckoutExtensionModel(Base):
    __tablename__ = "checkout_extensions"

    id = Column(String(128), primary_key=True, nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_domain = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    extension_point = Column(String(128), nullable=False)  # e.g., 'purchase.checkout.block.render'
    extension_type = Column(String(64), nullable=False, default="cross_sell")  # cross_sell, banner, custom_field, trust_badge
    status = Column(String(32), nullable=False, default="active")  # active, paused, archived
    priority = Column(Integer, nullable=False, default=10)
    config_schema = Column(JSON, nullable=True, default=dict)
    rules_payload = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("status IN ('active', 'paused', 'archived')", name="check_checkout_extension_status"),
        Index("idx_checkout_ext_shop_status", "shop_domain", "status"),
        Index("idx_checkout_ext_point", "extension_point"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "shop_domain": self.shop_domain,
            "title": self.title,
            "extension_point": self.extension_point,
            "extension_type": self.extension_type,
            "status": self.status,
            "priority": self.priority,
            "config_schema": self.config_schema or {},
            "rules_payload": self.rules_payload or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
