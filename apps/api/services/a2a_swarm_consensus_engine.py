# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-SERVICE-CONSENSUS"
# purpose: "Lightweight Raft/PBFT Swarm Consensus Engine with Weighted Quorum and Leader Fallback"
# canonical_source: true
# alters_files: ["apps/api/services/a2a_swarm_consensus_engine.py"]
# triggers_tasks: ["DNK-A2A-003-PHASE3"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import hashlib
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple
from apps.api.db.models.a2a_consensus_vote_record import A2AConsensusVoteRecord


class A2ASwarmConsensusEngine:
    """Lightweight consensus engine using Byzantine fault tolerance & weighted quorum voting."""

    def __init__(self):
        self._voting_rounds: Dict[str, Dict[str, Any]] = {}
        self._votes: Dict[str, List[A2AConsensusVoteRecord]] = {}
        self._leaders: Dict[str, str] = {}  # cluster_id -> leader_agent_id

    def set_cluster_leader(self, cluster_id: str, leader_agent_id: str) -> None:
        self._leaders[cluster_id] = leader_agent_id

    def get_cluster_leader(self, cluster_id: str) -> Optional[str]:
        return self._leaders.get(cluster_id)

    def create_voting_round(
        self,
        cluster_id: str,
        proposal_type: str,
        proposal_payload: Dict[str, Any],
        initiator_agent_id: str,
        quorum_threshold_percentage: float = 66.7,
        voting_timeout_seconds: float = 10.0,
        eligible_voter_ids: Optional[List[str]] = None,
        workspace_id: str = "ws-default",
        timeout_seconds: Optional[float] = None,
    ) -> Dict[str, Any]:
        round_id = f"rnd_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        effective_timeout = timeout_seconds if timeout_seconds is not None else voting_timeout_seconds
        expires_at = now + timedelta(seconds=effective_timeout)

        round_data = {
            "round_id": round_id,
            "workspace_id": workspace_id,
            "cluster_id": cluster_id,
            "proposal_type": proposal_type,
            "proposal_payload": proposal_payload,
            "initiator_agent_id": initiator_agent_id,
            "quorum_threshold_percentage": quorum_threshold_percentage,
            "status": "active",  # active, approved, rejected, expired, leader_override
            "eligible_voter_ids": eligible_voter_ids or [],
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "final_outcome": None,
        }
        self._voting_rounds[round_id] = round_data
        self._votes[round_id] = []
        return round_data

    def _generate_vote_signature(self, round_id: str, voter_id: str, decision: str, reason: str) -> str:
        payload = f"{round_id}:{voter_id}:{decision}:{reason}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def cast_vote(
        self,
        round_id: str,
        voter_agent_id: str,
        decision: str,  # approve, reject, abstain
        voting_power: float = 1.0,
        reason: str = "",
        workspace_id: str = "ws-default",
    ) -> Tuple[bool, Optional[A2AConsensusVoteRecord], str]:
        round_data = self._voting_rounds.get(round_id)
        if not round_data:
            return False, None, f"Voting round {round_id} not found"

        if round_data["status"] != "active":
            return False, None, f"Voting round {round_id} is already {round_data['status']}"

        eligible = round_data.get("eligible_voter_ids", [])
        if eligible and voter_agent_id not in eligible:
            return False, None, f"Agent {voter_agent_id} is not eligible to vote in round {round_id}"

        # Check for duplicate vote
        existing_votes = self._votes.get(round_id, [])
        if any(v.voter_agent_id == voter_agent_id for v in existing_votes):
            return False, None, f"Agent {voter_agent_id} has already cast a vote in round {round_id}"

        valid_decisions = ("approve", "reject", "abstain")
        if decision not in valid_decisions:
            return False, None, f"Invalid decision '{decision}'. Must be one of {valid_decisions}"

        sig = self._generate_vote_signature(round_id, voter_agent_id, decision, reason)
        vote_id = f"vote_{uuid.uuid4().hex[:12]}"
        vote_record = A2AConsensusVoteRecord(
            id=vote_id,
            workspace_id=workspace_id,
            consensus_round_id=round_id,
            proposal_id=round_data.get("proposal_type", "prop_generic"),
            voter_agent_id=voter_agent_id,
            vote_decision=decision,
            reputation_weight=voting_power,
            signature_hash=sig,
            vote_reasoning=reason,
            created_at=datetime.now(timezone.utc),
        )
        self._votes[round_id].append(vote_record)
        return True, vote_record, "Vote cast successfully"

    def resolve_voting_round(self, round_id: str) -> Dict[str, Any]:
        round_data = self._voting_rounds.get(round_id)
        if not round_data:
            return {"status": "error", "message": f"Round {round_id} not found"}

        votes = self._votes.get(round_id, [])
        if not votes:
            round_data["status"] = "expired"
            round_data["final_outcome"] = "no_votes_cast"
            return round_data

        total_power = sum(v.reputation_weight or 1.0 for v in votes)
        approve_power = sum(v.reputation_weight or 1.0 for v in votes if v.vote_decision == "approve")
        reject_power = sum(v.reputation_weight or 1.0 for v in votes if v.vote_decision == "reject")

        non_abstain_power = approve_power + reject_power
        threshold = round_data.get("quorum_threshold_percentage", 66.7)

        if non_abstain_power > 0:
            approval_pct = (approve_power / non_abstain_power) * 100.0
        else:
            approval_pct = 0.0

        if round(approval_pct, 1) >= round(threshold, 1):
            round_data["status"] = "approved"
            round_data["final_outcome"] = "consensus_reached"
        else:
            round_data["status"] = "rejected"
            round_data["final_outcome"] = "consensus_failed"

        round_data["stats"] = {
            "total_votes": len(votes),
            "total_power": round(total_power, 2),
            "approve_power": round(approve_power, 2),
            "reject_power": round(reject_power, 2),
            "approval_percentage": round(approval_pct, 2),
            "threshold_percentage": threshold,
        }
        return round_data

    def elect_fallback_leader(
        self,
        cluster_id: str,
        candidates: List[Dict[str, Any]],  # list of {'agent_id': str, 'reputation': float, 'load': float}
    ) -> Optional[str]:
        """Leader election fallback selecting node with highest reputation and lowest load."""
        if not candidates:
            return None

        # Sort candidates: highest reputation first, then lowest load
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (
                c.get("reputation", c.get("reputation_score", 1.0)),
                -c.get("load", c.get("cpu_utilization", 50.0)),
            ),
            reverse=True,
        )
        new_leader_id = sorted_candidates[0]["agent_id"]
        self._leaders[cluster_id] = new_leader_id
        return new_leader_id

    def leader_override(self, round_id: str, leader_agent_id: str, override_decision: str, reason: str) -> Dict[str, Any]:
        round_data = self._voting_rounds.get(round_id)
        if not round_data:
            return {"status": "error", "message": f"Round {round_id} not found"}

        cluster_id = round_data.get("cluster_id", "")
        current_leader = self._leaders.get(cluster_id)
        if current_leader != leader_agent_id:
            return {"status": "error", "message": f"Agent {leader_agent_id} is not the cluster leader for {cluster_id}"}

        round_data["status"] = "leader_override"
        round_data["final_outcome"] = f"override_{override_decision}"
        round_data["override_metadata"] = {
            "leader_id": leader_agent_id,
            "decision": override_decision,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        return round_data

    def get_round(self, round_id: str) -> Optional[Dict[str, Any]]:
        return self._voting_rounds.get(round_id)

    def get_round_votes(self, round_id: str) -> List[A2AConsensusVoteRecord]:
        return self._votes.get(round_id, [])
