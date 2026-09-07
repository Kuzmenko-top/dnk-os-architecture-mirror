# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-A2A-003-MODELS"
# purpose: "Unit tests for DNK-A2A-003 Agent Mesh & Swarm Consensus ORM models"
# canonical_source: true
# alters_files: ["tests/a2a/test_a2a_models.py"]
# triggers_tasks: ["DNK-A2A-003-PHASE1"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone, timedelta
from apps.api.db.models import (
    A2AMeshAgent,
    A2ASwarmMesh,
    A2ATaskAuction,
    A2AResourceBid,
    A2ANegotiationContract,
    A2AConsensusVoteRecord,
)


def test_a2a_mesh_agent_model_instantiation():
    agent = A2AMeshAgent(
        workspace_id="ws-alpha",
        agent_name="gerych_builder",
        role="builder",
        capabilities=["codegen", "refactor"],
        status="online",
        cpu_utilization=35.5,
        memory_utilization=42.0,
        active_tasks_count=2.0,
        reputation_score=1.0,
        endpoint_url="https://agent-mesh.dnk.ai/builder",
        is_leader=False,
    )
    d = agent.to_dict()
    assert d["workspace_id"] == "ws-alpha"
    assert d["agent_name"] == "gerych_builder"
    assert "codegen" in d["capabilities"]
    assert d["status"] == "online"
    assert d["cpu_utilization"] == 35.5
    assert d["is_leader"] is False


def test_a2a_swarm_mesh_model_instantiation():
    mesh = A2ASwarmMesh(
        workspace_id="ws-alpha",
        mesh_name="core_swarm_alpha",
        topology_type="mesh",
        quorum_percentage=66.6,
        consensus_strategy="raft_quorum",
        active_nodes_count=8,
        status="healthy",
    )
    d = mesh.to_dict()
    assert d["mesh_name"] == "core_swarm_alpha"
    assert d["topology_type"] == "mesh"
    assert d["quorum_percentage"] == 66.6
    assert d["status"] == "healthy"


def test_a2a_task_auction_model_instantiation():
    expires = datetime.now(timezone.utc) + timedelta(seconds=10)
    auction = A2ATaskAuction(
        workspace_id="ws-alpha",
        task_id="task_build_123",
        task_name="Compile Liquid AST",
        initiator_agent_id="agent_supervisor_01",
        required_capabilities=["liquid", "wasm"],
        max_budget_units=50.0,
        expires_at=expires,
        status="open",
    )
    d = auction.to_dict()
    assert d["task_id"] == "task_build_123"
    assert d["status"] == "open"
    assert d["max_budget_units"] == 50.0
    assert "liquid" in d["required_capabilities"]


def test_a2a_resource_bid_model_instantiation():
    bid = A2AResourceBid(
        workspace_id="ws-alpha",
        auction_id="auction_999",
        bidder_agent_id="agent_dnk_shopify",
        bid_price_units=15.0,
        estimated_duration_ms=450.0,
        current_load_percentage=25.0,
        composite_score=0.92,
        is_winning_bid=False,
    )
    d = bid.to_dict()
    assert d["auction_id"] == "auction_999"
    assert d["bidder_agent_id"] == "agent_dnk_shopify"
    assert d["bid_price_units"] == 15.0
    assert d["composite_score"] == 0.92
    assert d["is_winning_bid"] is False


def test_a2a_negotiation_contract_model_instantiation():
    contract = A2ANegotiationContract(
        workspace_id="ws-alpha",
        delegator_agent_id="agent_supervisor_01",
        executor_agent_id="agent_dnk_shopify",
        task_id="task_build_123",
        agreed_budget_units=15.0,
        max_latency_ms=500.0,
        retry_limit=3,
        status="active",
        contract_terms={"priority": "high", "guarantee": "strict"},
    )
    d = contract.to_dict()
    assert d["agreed_budget_units"] == 15.0
    assert d["status"] == "active"
    assert d["contract_terms"]["priority"] == "high"


def test_a2a_consensus_vote_record_model_instantiation():
    vote = A2AConsensusVoteRecord(
        workspace_id="ws-alpha",
        consensus_round_id="round_007",
        proposal_id="prop_scale_up",
        voter_agent_id="agent_gerych_auditor",
        vote_decision="approve",
        reputation_weight=1.5,
        vote_reasoning="Security and resource invariants verified green",
        is_valid=True,
        signature_hash="sha256:7f8e9d",
    )
    d = vote.to_dict()
    assert d["consensus_round_id"] == "round_007"
    assert d["vote_decision"] == "approve"
    assert d["reputation_weight"] == 1.5
    assert d["is_valid"] is True
