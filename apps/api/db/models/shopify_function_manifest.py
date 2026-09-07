# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_function_manifest"
# purpose: "SQLAlchemy ORM model for Shopify Function Manifest & Wasm Metadata (DNK-ECOM-005)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Index, Text
from apps.api.db.models.workspace import Base


class ShopifyFunctionManifestModel(Base):
    __tablename__ = "shopify_function_manifests"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), nullable=False, index=True)
    function_id = Column(String(128), nullable=False, unique=True, index=True)
    function_title = Column(String(255), nullable=False)
    api_type = Column(String(64), nullable=False)  # cart_transform, order_routing, product_discounts, order_discounts, delivery_customization, payment_customization
    api_version = Column(String(32), nullable=False, default="2024-07")
    wasm_binary_hash = Column(String(128), nullable=True)
    wasm_source_type = Column(String(32), nullable=False, default="rust")  # rust, assemblyscript, javascript, native_python_sandbox
    status = Column(String(32), nullable=False, default="draft")  # draft, compiled, deployed, active, disabled
    input_query = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_shopify_fn_manifest_ws", "workspace_id"),
        Index("ix_shopify_fn_manifest_type", "workspace_id", "api_type"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "function_id": self.function_id,
            "function_title": self.function_title,
            "api_type": self.api_type,
            "api_version": self.api_version,
            "wasm_binary_hash": self.wasm_binary_hash,
            "wasm_source_type": self.wasm_source_type,
            "status": self.status,
            "input_query": self.input_query,
            "metadata_json": self.metadata_json,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
