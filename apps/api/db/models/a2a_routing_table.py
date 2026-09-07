# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_a2a_routing_table"
# purpose: "ORM Model for Dynamic Mesh Routing Entries, Fallbacks and Circuit Breakers (DNK-A2A-004 Phase 1)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Integer, Float, Boolean
from apps.api.db.models.workspace import Base


class A2ARoutingTable(Base):
    """Stores mesh routing paths for capabilities, primary/fallback targets, and circuit breaker status."""
    __tablename__ = "a2a_routing_tables"

    id = Column(String(64), primary_key=True, default=lambda: f"route_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    capability_key = Column(String(128), nullable=False, index=True)  # capability being routed
    primary_agent_id = Column(String(64), nullable=False, index=True)
    fallback_agent_ids = Column(JSON, nullable=False, default=list)  # list of str agent_ids
    circuit_breaker_status = Column(String(32), nullable=False, default="CLOSED")  # CLOSED (healthy), OPEN (tripped), HALF_OPEN (probing)
    failure_count = Column(Integer, nullable=False, default=0)
    consecutive_success_count = Column(Integer, nullable=False, default=0)
    circuit_tripped_at = Column(DateTime, nullable=True)
    health_weight = Column(Float, nullable=False, default=1.0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id or "ws-default",
            "capability_key": self.capability_key,
            "primary_agent_id": self.primary_agent_id,
            "fallback_agent_ids": self.fallback_agent_ids or [],
            "circuit_breaker_status": self.circuit_breaker_status or "CLOSED",
            "failure_count": self.failure_count if self.failure_count is not None else 0,
            "consecutive_success_count": self.consecutive_success_count if self.consecutive_success_count is not None else 0,
            "circuit_tripped_at": self.circuit_tripped_at.isoformat() if self.circuit_tripped_at else None,
            "health_weight": self.health_weight if self.health_weight is not None else 1.0,
            "is_active": bool(self.is_active),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
