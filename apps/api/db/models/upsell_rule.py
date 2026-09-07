# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_upsell_rule"
# purpose: "SQLAlchemy ORM model for Upsell and Cross-sell Logic Rules (DNK-ECOM-006 Phase 1)"
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


class UpsellRuleModel(Base):
    __tablename__ = "upsell_rules"

    id = Column(String(128), primary_key=True, nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    shop_domain = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    rule_type = Column(String(64), nullable=False, default="cart_value")  # cart_value, product_match, customer_tag, inventory_level
    min_cart_value = Column(Float, nullable=False, default=0.0)
    max_cart_value = Column(Float, nullable=True)
    matching_product_ids = Column(JSON, nullable=True, default=list)
    matching_collection_ids = Column(JSON, nullable=True, default=list)
    customer_tags = Column(JSON, nullable=True, default=list)
    action_type = Column(String(64), nullable=False, default="recommend_upsell")  # recommend_upsell, apply_discount, trigger_funnel
    target_offer_id = Column(String(128), nullable=True)
    priority = Column(Integer, nullable=False, default=10)
    is_active = Column(Integer, nullable=False, default=1)  # 1 = True, 0 = False
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_upsell_rule_shop", "shop_domain"),
        Index("idx_upsell_rule_type", "rule_type"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "shop_domain": self.shop_domain,
            "name": self.name,
            "rule_type": self.rule_type,
            "min_cart_value": self.min_cart_value,
            "max_cart_value": self.max_cart_value,
            "matching_product_ids": self.matching_product_ids or [],
            "matching_collection_ids": self.matching_collection_ids or [],
            "customer_tags": self.customer_tags or [],
            "action_type": self.action_type,
            "target_offer_id": self.target_offer_id,
            "priority": self.priority,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
