# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_swarm_cognitive_topologies.py"
# purpose: "Verify Cognitive Swarm Topologies: Mixture-of-Agents (MoA) & Majority Voting / Borda Count."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Maksym Kuzmenko"
# --- END DNK-MRH-HEADER ---

import pytest
from core.orchestrator.cognitive_topologies import (
    CognitiveTopologiesEngine,
    AgentProposal,
    VoteBallot,
)
from core.orchestrator.swarm_coordinator import swarm_coordinator


def test_mixture_of_agents_synthesis(tmp_path):
    engine = CognitiveTopologiesEngine()
    proposals = [
        AgentProposal(
            agent="dnk_dev_fullstack",
            content="Implement async connection pooling with SQLAlchemy 2.0 and asyncpg.",
            confidence_score=0.95,
            rationale="High throughput and native asyncio support.",
        ),
        AgentProposal(
            agent="gerych_builder",
            content="Use React Query with optimistic UI updates and skeleton fallbacks.",
            confidence_score=0.90,
            rationale="Eliminates visual layout shifts on canvas reloads.",
        ),
        AgentProposal(
            agent="gerych_auditor",
            content="Enforce strict rate-limiting and JWT token refresh sliding windows.",
            confidence_score=0.98,
            rationale="Prevents replay attacks and unauthorized socket abuse.",
        ),
    ]

    result = engine.run_mixture_of_agents(
        task_id="task_moa_test_001",
        topic="DNK Studio Core Performance & Security Architecture",
        proposals=proposals,
        aggregator_agent="gerych_prime",
    )

    assert result.task_id == "task_moa_test_001"
    assert result.aggregator_agent == "gerych_prime"
    assert len(result.proposals) == 3
    assert "DNK Studio Core Performance & Security Architecture" in result.synthesized_solution
    assert "dnk_dev_fullstack" in result.synthesized_solution
    assert "gerych_auditor" in result.synthesized_solution
    assert result.ledger_artifact_id is not None


def test_majority_voting_plurality_and_borda():
    engine = CognitiveTopologiesEngine()
    candidates = ["PostgreSQL", "SQLite", "DuckDB"]

    # 4 voters
    ballots = [
        VoteBallot(voter_agent="dnk_dev_fullstack", ranked_candidates=["PostgreSQL", "DuckDB", "SQLite"]),
        VoteBallot(voter_agent="gerych_builder", ranked_candidates=["PostgreSQL", "SQLite", "DuckDB"]),
        VoteBallot(voter_agent="dnk_analytics", ranked_candidates=["DuckDB", "PostgreSQL", "SQLite"]),
        VoteBallot(voter_agent="gerych_auditor", ranked_candidates=["PostgreSQL", "SQLite", "DuckDB"]),
    ]

    outcome = engine.run_majority_voting(
        decision_topic="Primary Database for DNK Studio Analytics",
        candidates=candidates,
        ballots=ballots,
        task_id="task_vote_test_001",
    )

    assert outcome.winner == "PostgreSQL"
    assert outcome.consensus_reached is True
    assert outcome.vote_tallies["PostgreSQL"] == 3
    assert outcome.vote_tallies["DuckDB"] == 1
    assert outcome.borda_scores["PostgreSQL"] > outcome.borda_scores["DuckDB"]


def test_swarm_coordinator_topologies_integration():
    proposals = [
        AgentProposal(
            agent="dnk_shopify",
            content="Use Shopify Admin GraphQL 2026-04 with Bulk Operation API.",
            confidence_score=0.92,
        ),
        AgentProposal(
            agent="gerych_builder",
            content="Use Virtualized Table with virtual scrolling for 10,000 products.",
            confidence_score=0.88,
        ),
    ]

    moa = swarm_coordinator.execute_mixture_of_agents(
        task_id="task_coord_moa_001",
        topic="Shopify High-Volume Catalog Sync",
        proposals=proposals,
    )
    assert moa.aggregator_agent == "gerych_prime"
    assert "Shopify High-Volume Catalog Sync" in moa.synthesized_solution

    ballots = [
        VoteBallot(voter_agent="agent_a", ranked_candidates=["Remotion", "FrameCN"]),
        VoteBallot(voter_agent="agent_b", ranked_candidates=["Remotion", "FrameCN"]),
    ]
    voting = swarm_coordinator.execute_majority_voting(
        decision_topic="Video Rendering Framework",
        candidates=["Remotion", "FrameCN"],
        ballots=ballots,
    )
    assert voting.winner == "Remotion"
    assert voting.consensus_reached is True
