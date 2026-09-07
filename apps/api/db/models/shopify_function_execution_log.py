# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_shopify_function_execution_log"
# purpose: "SQLAlchemy ORM model for Shopify Function Wasm Execution Logs (DNK-ECOM-005)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, Text, Index
from apps.api.db.models.workspace import Base


class ShopifyFunctionExecutionLogModel(Base):
    __tablename__ = "shopify_function_execution_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(128), nullable=False, index=True)
    function_id = Column(String(128), nullable=False, index=True)
    invocation_id = Column(String(128), nullable=False, unique=True, index=True)
    api_type = Column(String(64), nullable=False)
    input_payload = Column(JSON, nullable=False, default=dict)
    output_payload = Column(JSON, nullable=False, default=dict)
    execution_time_ms = Column(Float, nullable=False, default=0.0)
    memory_usage_bytes = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="success")  # success, error, timeout
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_shopify_fn_log_ws", "workspace_id"),
        Index("ix_shopify_fn_log_fn", "workspace_id", "function_id"),
        Index("ix_shopify_fn_log_status", "workspace_id", "status"),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "function_id": self.function_id,
            "invocation_id": self.invocation_id,
            "api_type": self.api_type,
            "input_payload": self.input_payload,
            "output_payload": self.output_payload,
            "execution_time_ms": self.execution_time_ms,
            "memory_usage_bytes": self.memory_usage_bytes,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
