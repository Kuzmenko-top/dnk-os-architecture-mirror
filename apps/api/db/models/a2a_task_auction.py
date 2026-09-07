# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-MODEL-AUCTION"
# purpose: "A2A Task Auction ORM Model for Decentralized Task Bidding"
# canonical_source: true
# alters_files: ["apps/api/db/models/a2a_task_auction.py"]
# triggers_tasks: ["DNK-A2A-003-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Integer, Float
from apps.api.db.models.workspace import Base


class A2ATaskAuction(Base):
    """Represents a decentralized task auction where worker agents submit resource bids."""
    __tablename__ = "a2a_task_auctions"

    id = Column(String(64), primary_key=True, default=lambda: f"auc_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    task_id = Column(String(64), nullable=False, index=True)
    task_name = Column(String(256), nullable=False)
    initiator_agent_id = Column(String(64), nullable=False, index=True)
    winning_agent_id = Column(String(64), nullable=True)
    required_capabilities = Column(JSON, nullable=False, default=list)  # list of required capability strings
    max_budget_units = Column(Float, nullable=False, default=100.0)
    final_settled_price = Column(Float, nullable=True)
    bids_count = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="open", index=True)  # open, closed, awarded, expired, cancelled
    task_payload = Column(JSON, nullable=False, default=dict)
    expires_at = Column(DateTime, nullable=False)
    awarded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "task_id": self.task_id,
            "task_name": self.task_name,
            "initiator_agent_id": self.initiator_agent_id,
            "winning_agent_id": self.winning_agent_id,
            "required_capabilities": self.required_capabilities or [],
            "max_budget_units": self.max_budget_units if self.max_budget_units is not None else 100.0,
            "final_settled_price": self.final_settled_price,
            "bids_count": self.bids_count if self.bids_count is not None else 0,
            "status": self.status or "open",
            "task_payload": self.task_payload or {},
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "awarded_at": self.awarded_at.isoformat() if self.awarded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
