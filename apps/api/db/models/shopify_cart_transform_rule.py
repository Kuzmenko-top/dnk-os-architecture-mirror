# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_cart_transform_rule"
# purpose: "SQLAlchemy ORM model for Shopify Cart Transform & Bundle Rules (DNK-ECOM-005)"
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


class ShopifyCartTransformRuleModel(Base):
    __tablename__ = "shopify_cart_transform_rules"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), nullable=False, index=True)
    function_id = Column(String(128), nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    transform_type = Column(String(64), nullable=False)  # bundle_expand, bundle_merge, price_override, component_split
    trigger_criteria = Column(JSON, nullable=False, default=dict)  # parent_variant_id, min_quantity, target_tags
    operations = Column(JSON, nullable=False, default=list)  # list of expand, merge, or override ops
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_shopify_cart_tr_ws", "workspace_id"),
        Index("ix_shopify_cart_tr_fn", "workspace_id", "function_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "function_id": self.function_id,
            "rule_name": self.rule_name,
            "transform_type": self.transform_type,
            "trigger_criteria": self.trigger_criteria,
            "operations": self.operations,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
