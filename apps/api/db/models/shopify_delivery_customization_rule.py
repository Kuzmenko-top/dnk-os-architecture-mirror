# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_delivery_customization_rule"
# purpose: "SQLAlchemy ORM model for Shopify Delivery Customization Rules (DNK-ECOM-005)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Index
from apps.api.db.models.workspace import Base


class ShopifyDeliveryCustomizationRuleModel(Base):
    __tablename__ = "shopify_delivery_customization_rules"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), nullable=False, index=True)
    function_id = Column(String(128), nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    action = Column(String(32), nullable=False)  # hide, rename, reorder, surcharge
    match_conditions = Column(JSON, nullable=False, default=dict)  # country_codes, state_codes, weight_max_kg, order_type
    target_delivery_methods = Column(JSON, nullable=False, default=list)  # list of delivery method names
    parameters = Column(JSON, nullable=False, default=dict)  # rename_to, surcharge_cents, new_position
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_shopify_deliv_rule_ws", "workspace_id"),
        Index("ix_shopify_deliv_rule_fn", "workspace_id", "function_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "function_id": self.function_id,
            "rule_name": self.rule_name,
            "action": self.action,
            "match_conditions": self.match_conditions,
            "target_delivery_methods": self.target_delivery_methods,
            "parameters": self.parameters,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
