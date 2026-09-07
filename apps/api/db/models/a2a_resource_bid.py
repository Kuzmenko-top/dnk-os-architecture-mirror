# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-MODEL-BID"
# purpose: "A2A Resource Bid ORM Model for Task Auction Responses"
# canonical_source: true
# alters_files: ["apps/api/db/models/a2a_resource_bid.py"]
# triggers_tasks: ["DNK-A2A-003-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Float, Boolean
from apps.api.db.models.workspace import Base


class A2AResourceBid(Base):
    """Represents a competitive resource bid submitted by an agent for a task auction."""
    __tablename__ = "a2a_resource_bids"

    id = Column(String(64), primary_key=True, default=lambda: f"bid_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    auction_id = Column(String(64), nullable=False, index=True)
    bidder_agent_id = Column(String(64), nullable=False, index=True)
    bid_price_units = Column(Float, nullable=False, default=1.0)
    estimated_duration_ms = Column(Float, nullable=False, default=100.0)
    current_load_percentage = Column(Float, nullable=False, default=0.0)
    composite_score = Column(Float, nullable=False, default=0.0)
    is_winning_bid = Column(Boolean, nullable=False, default=False)
    bid_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "auction_id": self.auction_id,
            "bidder_agent_id": self.bidder_agent_id,
            "bid_price_units": self.bid_price_units if self.bid_price_units is not None else 1.0,
            "estimated_duration_ms": self.estimated_duration_ms if self.estimated_duration_ms is not None else 100.0,
            "current_load_percentage": self.current_load_percentage if self.current_load_percentage is not None else 0.0,
            "composite_score": self.composite_score if self.composite_score is not None else 0.0,
            "is_winning_bid": bool(self.is_winning_bid),
            "bid_metadata": self.bid_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
