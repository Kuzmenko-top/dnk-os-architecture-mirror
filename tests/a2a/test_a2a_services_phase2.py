# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-A2A-003-SERVICES-P2"
# purpose: "Unit tests for Phase 2: A2A Mesh Negotiator & Task Auction Engine"
# canonical_source: true
# alters_files: ["tests/a2a/test_a2a_services_phase2.py"]
# triggers_tasks: ["DNK-A2A-003-PHASE2"]
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
import pytest
from apps.api.db.models.a2a_task_auction import A2ATaskAuction
from apps.api.db.models.a2a_resource_bid import A2AResourceBid
from apps.api.db.models.a2a_negotiation_contract import A2ANegotiationContract
from apps.api.services.a2a_mesh_negotiator import A2AMeshNegotiator, TaskSpec, NegotiationSession
from apps.api.services.a2a_task_auction_engine import A2ATaskAuctionEngine


# ==========================================
# 1. Negotiation Engine Unit Tests
# ==========================================

def test_negotiation_session_initiation_and_counter_offer():
    """Verify initiation of bilateral negotiation session and counter-offer flow."""
    negotiator = A2AMeshNegotiator()
    task_spec = TaskSpec(
        task_id="task_video_segmentation",
        task_name="Segment Long Video",
        required_capabilities=["video_ai", "ffmpeg"],
        budget_units=50.0,
        max_latency_ms=1200.0,
    )

    session = negotiator.initiate_negotiation(
        delegator_id="agent_orchestrator",
        executor_id="agent_video_ai",
        task_spec=task_spec,
    )
    assert session.session_id.startswith("neg_")
    assert session.status == "initiated"
    assert session.delegator_id == "agent_orchestrator"
    assert session.executor_id == "agent_video_ai"

    # Executor makes a counter offer
    counter = session.counter_offer(price=45.0, latency_ms=1000.0, terms={"resolution": "1080p"})
    assert session.status == "counter_offered"
    assert counter["price"] == 45.0

    # Delegator accepts counter offer
    session.accept()
    assert session.status == "accepted"
    assert session.agreed_price == 45.0
    assert session.agreed_latency_ms == 1000.0


def test_sla_validation_and_contract_registration():
    """Verify SLA contract validation rules and formal registration."""
    negotiator = A2AMeshNegotiator()
    agent = negotiator.register_agent(
        agent_id="agent_builder_02",
        agent_name="gerych_builder",
        role="builder",
        capabilities=["codegen", "ast"],
        cpu_utilization=10.0,
        memory_utilization=20.0,
        reputation_score=1.5,
    )

    contract = A2ANegotiationContract(
        id=f"sla_{uuid.uuid4().hex[:12]}",
        workspace_id="ws-default",
        delegator_agent_id="agent_lead",
        executor_agent_id="agent_builder_02",
        task_id="task_ast_rewrite",
        agreed_budget_units=30.0,
        max_latency_ms=500.0,
        retry_limit=3,
        status="active",
    )

    # Validate SLA
    assert negotiator.validate_sla(contract) is True

    # Register Contract
    contract_id = negotiator.register_contract(contract)
    assert contract_id == contract.id
    assert negotiator.get_contract(contract_id) is not None
    assert agent.active_tasks_count == 1.0


def test_proposal_evaluation_and_rejection_overload():
    """Verify proposal evaluation rejection when agent is overloaded or missing capabilities."""
    negotiator = A2AMeshNegotiator()
    negotiator.register_agent(
        agent_id="agent_busy_node",
        agent_name="busy_worker",
        capabilities=["codegen"],
        cpu_utilization=90.0,
        memory_utilization=88.0,
    )

    # Rejection due to high load
    res_load = negotiator.evaluate_proposal(
        executor_id="agent_busy_node",
        required_capabilities=["codegen"],
        offered_budget_units=20.0,
    )
    assert res_load["accepted"] is False
    assert "overloaded" in res_load["reason"]

    # Rejection due to missing capabilities
    negotiator.register_agent(
        agent_id="agent_idle_node",
        agent_name="idle_worker",
        capabilities=["codegen"],
        cpu_utilization=10.0,
        memory_utilization=10.0,
    )
    res_caps = negotiator.evaluate_proposal(
        executor_id="agent_idle_node",
        required_capabilities=["wasm", "rust"],
        offered_budget_units=20.0,
    )
    assert res_caps["accepted"] is False
    assert "Missing required capabilities" in res_caps["reason"]


def test_contract_fulfillment_and_breach_lifecycle():
    """Verify lifecycle of fulfillment boosting reputation and breach penalizing reputation."""
    negotiator = A2AMeshNegotiator()
    agent = negotiator.register_agent(
        agent_id="agent_auditor_node",
        agent_name="gerych_auditor",
        reputation_score=1.0,
    )

    # Fulfillment flow
    contract1 = negotiator.negotiate_and_create_contract(
        delegator_id="lead",
        executor_id="agent_auditor_node",
        task_id="task_sec_audit",
        agreed_budget_units=15.0,
    )
    fulfilled = negotiator.fulfill_contract(contract1.id)
    assert fulfilled.status == "fulfilled"
    assert (agent.reputation_score or 1.0) > 1.0

    # Breach flow
    contract2 = negotiator.negotiate_and_create_contract(
        delegator_id="lead",
        executor_id="agent_auditor_node",
        task_id="task_sec_audit_2",
        agreed_budget_units=15.0,
    )
    breached = negotiator.breach_contract(contract2.id, reason="Timeout on test suite")
    assert breached.status == "breached"
    assert (agent.reputation_score or 1.0) < 1.05


# ==========================================
# 2. Task Auction Engine Unit Tests
# ==========================================

def test_auction_creation_and_bid_ranking():
    """Verify task auction creation, multi-bid ranking, and winner determination."""
    engine = A2ATaskAuctionEngine()
    auction = engine.create_auction(
        task_id="task_shopify_extension",
        task_name="Compile Shopify Extension",
        initiator_agent_id="agent_shopify_lead",
        required_capabilities=["shopify_cli", "wasm"],
        max_budget_units=100.0,
    )
    assert isinstance(auction, A2ATaskAuction)
    assert auction.status == "open"

    # Bid 1: Fast and cheap
    bid1 = A2AResourceBid(
        id="bid_01",
        workspace_id="ws-default",
        auction_id=auction.id,
        bidder_agent_id="worker_alpha",
        bid_price_units=30.0,
        estimated_duration_ms=200.0,
        current_load_percentage=15.0,
    )
    assert engine.submit_bid(auction.id, bid1)

    # Bid 2: Slower and more expensive
    bid2 = A2AResourceBid(
        id="bid_02",
        workspace_id="ws-default",
        auction_id=auction.id,
        bidder_agent_id="worker_beta",
        bid_price_units=80.0,
        estimated_duration_ms=1200.0,
        current_load_percentage=60.0,
    )
    assert engine.submit_bid(auction.id, bid2)

    # Rank bids
    ranked = engine.rank_bids(auction.id)
    assert len(ranked) == 2
    assert ranked[0].bidder_agent_id == "worker_alpha"
    assert ranked[0].composite_score > ranked[1].composite_score


def test_auction_composite_scoring_weights():
    """Verify composite utility score calculation respects multi-attribute weights."""
    engine = A2ATaskAuctionEngine()

    # Optimal Bid: Low price (0.0), low duration (0ms), low load (0%), high reputation (2.0)
    score_perfect = engine.calculate_composite_score(
        bid_price=0.0,
        max_budget=100.0,
        estimated_duration_ms=0.0,
        current_load_percentage=0.0,
        agent_reputation=2.0,
    )
    assert score_perfect == 1.0

    # Worst Bid: High price (=budget), high duration (>=2000ms), 100% load, 0 reputation
    score_worst = engine.calculate_composite_score(
        bid_price=100.0,
        max_budget=100.0,
        estimated_duration_ms=2000.0,
        current_load_percentage=100.0,
        agent_reputation=0.0,
    )
    assert score_worst == 0.0


def test_auction_finalization_with_sla_contract():
    """Verify auction finalization automatically registers an active SLA contract with winning agent."""
    negotiator = A2AMeshNegotiator()
    negotiator.register_agent(
        agent_id="worker_winner",
        agent_name="winner_agent",
        capabilities=["fastapi", "postgres"],
        reputation_score=1.5,
    )
    engine = A2ATaskAuctionEngine(negotiator=negotiator)

    auction = engine.create_auction(
        task_id="task_db_migration",
        task_name="Migrate PG Schema",
        initiator_agent_id="agent_db_admin",
        required_capabilities=["postgres"],
        max_budget_units=60.0,
    )

    engine.submit_bid(
        auction_id=auction.id,
        bidder_agent_id="worker_winner",
        bid_price_units=25.0,
        estimated_duration_ms=300.0,
        current_load_percentage=10.0,
        agent_reputation=1.5,
    )

    contract = engine.finalize_auction(auction.id)
    assert contract is not None
    assert contract.status == "active"
    assert contract.executor_agent_id == "worker_winner"
    assert contract.delegator_agent_id == "agent_db_admin"
    assert contract.agreed_budget_units == 25.0
    assert contract.contract_terms["auction_id"] == auction.id


def test_auction_over_budget_and_expiration():
    """Verify bid rejection on budget overrun and auction expiration on zero bids."""
    engine = A2ATaskAuctionEngine()
    auction = engine.create_auction(
        task_id="task_budget_limit",
        task_name="Budget Bound Task",
        initiator_agent_id="lead",
        max_budget_units=40.0,
    )

    # Over budget bid
    res = engine.submit_bid(
        auction_id=auction.id,
        bidder_agent_id="greedy_bot",
        bid_price_units=50.0,
        estimated_duration_ms=100.0,
        current_load_percentage=10.0,
    )
    assert bool(res) is False

    # Expiration on no valid bids
    empty_auction = engine.create_auction(
        task_id="task_empty",
        task_name="Unattended Task",
        initiator_agent_id="lead",
    )
    auc, winner, msg = engine.resolve_auction(empty_auction.id)
    assert auc.status == "expired"
    assert winner is None
