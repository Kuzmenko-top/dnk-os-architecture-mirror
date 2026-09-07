# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_a2a_capability_schema"
# purpose: "ORM Model for Capability Schemas, Contracts and SLA Constraints in A2A Mesh (DNK-A2A-004 Phase 1)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Float, Boolean, Integer
from apps.api.db.models.workspace import Base


class A2ACapabilitySchema(Base):
    """Defines formal schemas, input/output validation contracts and SLA parameters for agent capabilities."""
    __tablename__ = "a2a_capability_schemas"

    id = Column(String(64), primary_key=True, default=lambda: f"cap_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    capability_key = Column(String(128), nullable=False, unique=True, index=True)  # e.g. "code_synthesis", "vector_search"
    display_name = Column(String(128), nullable=False)
    description = Column(String(512), nullable=True)
    version = Column(String(32), nullable=False, default="1.0.0")
    input_schema = Column(JSON, nullable=False, default=dict)   # JSONSchema specification
    output_schema = Column(JSON, nullable=False, default=dict)  # JSONSchema specification
    target_sla_latency_ms = Column(Float, nullable=False, default=1500.0)
    cost_per_invocation_units = Column(Float, nullable=False, default=0.01)
    rate_limit_rpm = Column(Integer, nullable=False, default=120)
    required_trust_tier = Column(String(32), nullable=False, default="tier-2")
    is_deprecated = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id or "ws-default",
            "capability_key": self.capability_key,
            "display_name": self.display_name,
            "description": self.description,
            "version": self.version or "1.0.0",
            "input_schema": self.input_schema or {},
            "output_schema": self.output_schema or {},
            "target_sla_latency_ms": self.target_sla_latency_ms if self.target_sla_latency_ms is not None else 1500.0,
            "cost_per_invocation_units": self.cost_per_invocation_units if self.cost_per_invocation_units is not None else 0.01,
            "rate_limit_rpm": self.rate_limit_rpm if self.rate_limit_rpm is not None else 120,
            "required_trust_tier": self.required_trust_tier or "tier-2",
            "is_deprecated": bool(self.is_deprecated),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
