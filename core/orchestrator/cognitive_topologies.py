# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/cognitive_topologies.py"
# purpose: "Cognitive Swarm Topologies: Mixture-of-Agents (MoA), Majority Voting & Borda Count Consensus."
# canonical_source: true
# alters_files: ["data/swarm_artifacts/audit_trail.ndjson"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Maksym Kuzmenko"
# --- END DNK-MRH-HEADER ---

import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Callable
from pydantic import BaseModel, Field

from core.orchestrator.swarm_worktree import SwarmWorktreeManager
from core.orchestrator.swarm_ledger import SwarmLedger, ArtifactCategory


class AgentProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: f"prop_{uuid.uuid4().hex[:8]}")
    agent: str
    content: str
    confidence_score: float = 1.0
    rationale: Optional[str] = None
    created_at: float = Field(default_factory=time.time)


class MoAResult(BaseModel):
    task_id: str
    proposals: List[AgentProposal]
    synthesized_solution: str
    aggregator_agent: str
    duration_s: float
    ledger_artifact_id: Optional[str] = None


class VoteBallot(BaseModel):
    voter_agent: str
    ranked_candidates: List[str]  # In order of preference, index 0 is top choice
    justification: Optional[str] = None


class VotingOutcome(BaseModel):
    decision_topic: str
    winner: str
    vote_tallies: Dict[str, int]
    borda_scores: Dict[str, int]
    total_voters: int
    ballots: List[VoteBallot]
    consensus_reached: bool


class CognitiveTopologiesEngine:
    """
    Implements SOTA Multi-Agent Cognitive Topologies:
    1. Mixture-of-Agents (MoA): Layered multi-proposer generation + aggregator synthesis.
    2. Majority Voting & Borda Count: High-assurance multi-agent consensus decisions.
    """

    def __init__(self, worktree_manager: Optional[SwarmWorktreeManager] = None, ledger: Optional[SwarmLedger] = None):
        self.worktree_manager = worktree_manager or SwarmWorktreeManager()
        self.ledger = ledger or SwarmLedger.get_instance()

    def run_mixture_of_agents(
        self,
        task_id: str,
        topic: str,
        proposals: List[AgentProposal],
        aggregator_agent: str = "gerych_prime",
        custom_synthesizer: Optional[Callable[[List[AgentProposal]], str]] = None,
    ) -> MoAResult:
        """
        Executes Mixture-of-Agents layered aggregation over independent agent proposals.
        """
        start_time = time.time()

        if not proposals:
            raise ValueError("MoA requires at least one proposal to synthesize.")

        if custom_synthesizer:
            synthesized = custom_synthesizer(proposals)
        else:
            # Deterministic multi-perspective synthesis
            sections = []
            sections.append(f"# Multi-Agent Synthesis: {topic}")
            sections.append(f"**Aggregated by**: `{aggregator_agent}` | **Proposers count**: {len(proposals)}\n")
            sections.append("## Core Consensus Elements")
            for prop in sorted(proposals, key=lambda p: p.confidence_score, reverse=True):
                sections.append(f"- **[{prop.agent}]** (Conf: {prop.confidence_score:.2f}): {prop.content}")
                if prop.rationale:
                    sections.append(f"  *Rationale*: {prop.rationale}")

            synthesized = "\n".join(sections)

        duration = time.time() - start_time

        # Store into Swarm Ledger
        artifact = self.ledger.register_artifact(
            key=f"moa_synthesis:{task_id}",
            category=ArtifactCategory.SYNTHESIS_SUMMARY,
            producer_agent=aggregator_agent,
            content={
                "topic": topic,
                "synthesized": synthesized,
                "proposals_count": len(proposals),
            },
            task_id=task_id,
        )

        # Record to audit trail
        self.worktree_manager.record_audit_event(
            event="SWARM_MOA_SYNTHESIZED",
            agent=aggregator_agent,
            task_id=task_id,
            details={
                "topic": topic,
                "proposals_count": len(proposals),
                "duration_s": duration,
                "artifact_id": artifact.artifact_id,
            },
        )

        return MoAResult(
            task_id=task_id,
            proposals=proposals,
            synthesized_solution=synthesized,
            aggregator_agent=aggregator_agent,
            duration_s=duration,
            ledger_artifact_id=artifact.artifact_id,
        )

    def run_majority_voting(
        self,
        decision_topic: str,
        candidates: List[str],
        ballots: List[VoteBallot],
        task_id: Optional[str] = None,
    ) -> VotingOutcome:
        """
        Executes Plurality Voting and Borda Count ranking across voter agents.
        """
        if not candidates:
            raise ValueError("Candidates list cannot be empty.")
        if not ballots:
            raise ValueError("Ballots list cannot be empty.")

        plurality_tallies: Dict[str, int] = {c: 0 for c in candidates}
        borda_scores: Dict[str, int] = {c: 0 for c in candidates}

        n_candidates = len(candidates)

        for ballot in ballots:
            # Plurality tally (top choice only)
            if ballot.ranked_candidates:
                top_choice = ballot.ranked_candidates[0]
                if top_choice in plurality_tallies:
                    plurality_tallies[top_choice] += 1

            # Borda count tally (ranked weighting)
            for rank_idx, candidate in enumerate(ballot.ranked_candidates):
                if candidate in borda_scores:
                    points = max(0, n_candidates - rank_idx)
                    borda_scores[candidate] += points

        # Determine winner by highest Borda score, fallback to plurality
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (borda_scores.get(c, 0), plurality_tallies.get(c, 0)),
            reverse=True,
        )
        winner = sorted_candidates[0]
        consensus_reached = plurality_tallies[winner] > (len(ballots) / 2)

        outcome = VotingOutcome(
            decision_topic=decision_topic,
            winner=winner,
            vote_tallies=plurality_tallies,
            borda_scores=borda_scores,
            total_voters=len(ballots),
            ballots=ballots,
            consensus_reached=consensus_reached,
        )

        # Audit recording
        self.worktree_manager.record_audit_event(
            event="SWARM_VOTING_RESOLVED",
            agent="cognitive_topologies",
            task_id=task_id or f"vote_{uuid.uuid4().hex[:8]}",
            details={
                "decision_topic": decision_topic,
                "winner": winner,
                "consensus_reached": consensus_reached,
                "total_voters": len(ballots),
                "borda_scores": borda_scores,
            },
        )

        return outcome
