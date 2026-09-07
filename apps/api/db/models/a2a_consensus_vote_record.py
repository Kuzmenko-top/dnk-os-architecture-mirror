# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-MODEL-VOTE"
# purpose: "A2A Consensus Vote Record ORM Model for Auditable Swarm Decisions"
# canonical_source: true
# alters_files: ["apps/api/db/models/a2a_consensus_vote_record.py"]
# triggers_tasks: ["DNK-A2A-003-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Float, Boolean, Text
from apps.api.db.models.workspace import Base


class A2AConsensusVoteRecord(Base):
    """Represents an individual agent vote cast during swarm consensus rounds."""
    __tablename__ = "a2a_consensus_vote_records"

    id = Column(String(64), primary_key=True, default=lambda: f"vote_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    consensus_round_id = Column(String(64), nullable=False, index=True)
    proposal_id = Column(String(64), nullable=False, index=True)
    voter_agent_id = Column(String(64), nullable=False, index=True)
    vote_decision = Column(String(32), nullable=False)  # approve, reject, abstain
    reputation_weight = Column(Float, nullable=False, default=1.0)
    vote_reasoning = Column(Text, nullable=True)
    is_valid = Column(Boolean, nullable=False, default=True)
    signature_hash = Column(String(128), nullable=True)
    vote_metadata = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "consensus_round_id": self.consensus_round_id,
            "proposal_id": self.proposal_id,
            "voter_agent_id": self.voter_agent_id,
            "vote_decision": self.vote_decision,
            "reputation_weight": self.reputation_weight if self.reputation_weight is not None else 1.0,
            "vote_reasoning": self.vote_reasoning,
            "is_valid": bool(self.is_valid),
            "signature_hash": self.signature_hash,
            "vote_metadata": self.vote_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
