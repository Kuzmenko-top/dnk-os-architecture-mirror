# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-MODEL-CONTRACT"
# purpose: "A2A Negotiation Contract ORM Model for Service Level Agreements between Agents"
# canonical_source: true
# alters_files: ["apps/api/db/models/a2a_negotiation_contract.py"]
# triggers_tasks: ["DNK-A2A-003-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer
from apps.api.db.models.workspace import Base


class A2ANegotiationContract(Base):
    """Represents a finalized bilateral SLA contract between delegator and worker agents."""
    __tablename__ = "a2a_negotiation_contracts"

    id = Column(String(64), primary_key=True, default=lambda: f"sla_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    delegator_agent_id = Column(String(64), nullable=False, index=True)
    executor_agent_id = Column(String(64), nullable=False, index=True)
    task_id = Column(String(64), nullable=False, index=True)
    agreed_budget_units = Column(Float, nullable=False, default=0.0)
    max_latency_ms = Column(Float, nullable=False, default=1000.0)
    retry_limit = Column(Integer, nullable=False, default=3)
    status = Column(String(32), nullable=False, default="active", index=True)  # active, fulfilled, breached, terminated
    contract_terms = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    fulfilled_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "delegator_agent_id": self.delegator_agent_id,
            "executor_agent_id": self.executor_agent_id,
            "task_id": self.task_id,
            "agreed_budget_units": self.agreed_budget_units if self.agreed_budget_units is not None else 0.0,
            "max_latency_ms": self.max_latency_ms if self.max_latency_ms is not None else 1000.0,
            "retry_limit": self.retry_limit if self.retry_limit is not None else 3,
            "status": self.status or "active",
            "contract_terms": self.contract_terms or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "fulfilled_at": self.fulfilled_at.isoformat() if self.fulfilled_at else None,
        }
