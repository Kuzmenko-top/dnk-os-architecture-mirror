# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-A2A-003-SERVICES-P3"
# purpose: "Unit tests for Phase 3: A2A Swarm Consensus Engine & Dynamic Load Rebalancer"
# canonical_source: true
# alters_files: ["tests/a2a/test_a2a_services_phase3.py"]
# triggers_tasks: ["DNK-A2A-003-PHASE3"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import time
from datetime import datetime, timezone, timedelta
from apps.api.services.a2a_swarm_consensus_engine import A2ASwarmConsensusEngine
from apps.api.services.a2a_load_rebalancer import A2ALoadRebalancer


def test_consensus_voting_approval_supermajority():
    engine = A2ASwarmConsensusEngine()
    round_info = engine.create_voting_round(
        cluster_id="cluster_alpha",
        proposal_type="architecture_adr",
        proposal_payload={"adr_id": "ADR-0099", "title": "Adopt WASM Engine"},
        initiator_agent_id="agent_arch",
        quorum_threshold_percentage=66.7,
        eligible_voter_ids=["agent_1", "agent_2", "agent_3"],
    )
    round_id = round_info["round_id"]

    # Vote 1: Approve (weight 1.0)
    ok1, v1, _ = engine.cast_vote(round_id, "agent_1", "approve", voting_power=1.0)
    assert ok1 is True

    # Vote 2: Approve (weight 1.5)
    ok2, v2, _ = engine.cast_vote(round_id, "agent_2", "approve", voting_power=1.5)
    assert ok2 is True

    # Vote 3: Reject (weight 1.0)
    ok3, v3, _ = engine.cast_vote(round_id, "agent_3", "reject", voting_power=1.0)
    assert ok3 is True

    res = engine.resolve_voting_round(round_id)
    assert res["status"] == "approved"
    assert res["final_outcome"] == "consensus_reached"
    assert res["stats"]["approval_percentage"] > 66.7


def test_consensus_voting_rejection():
    engine = A2ASwarmConsensusEngine()
    round_info = engine.create_voting_round(
        cluster_id="cluster_alpha",
        proposal_type="security_policy",
        proposal_payload={"action": "bypass_firewall"},
        initiator_agent_id="rogue_worker",
        quorum_threshold_percentage=66.7,
        eligible_voter_ids=["sec_1", "sec_2"],
    )
    round_id = round_info["round_id"]

    engine.cast_vote(round_id, "sec_1", "reject", voting_power=1.0)
    engine.cast_vote(round_id, "sec_2", "reject", voting_power=1.0)

    res = engine.resolve_voting_round(round_id)
    assert res["status"] == "rejected"
    assert res["final_outcome"] == "consensus_failed"


def test_consensus_duplicate_and_ineligible_voting():
    engine = A2ASwarmConsensusEngine()
    round_info = engine.create_voting_round(
        cluster_id="cluster_alpha",
        proposal_type="deploy_gate",
        proposal_payload={},
        initiator_agent_id="lead",
        eligible_voter_ids=["valid_voter"],
    )
    round_id = round_info["round_id"]

    # Ineligible voter
    ok_bad, _, msg_bad = engine.cast_vote(round_id, "stranger", "approve")
    assert ok_bad is False
    assert "not eligible" in msg_bad

    # Valid voter
    ok_good, _, _ = engine.cast_vote(round_id, "valid_voter", "approve")
    assert ok_good is True

    # Duplicate vote
    ok_dup, _, msg_dup = engine.cast_vote(round_id, "valid_voter", "reject")
    assert ok_dup is False
    assert "already cast a vote" in msg_dup


def test_leader_election_fallback_and_override():
    engine = A2ASwarmConsensusEngine()
    candidates = [
        {"agent_id": "candidate_a", "reputation": 1.1, "load": 40.0},
        {"agent_id": "candidate_b", "reputation": 1.8, "load": 20.0},  # Winner: highest rep & lowest load
        {"agent_id": "candidate_c", "reputation": 1.4, "load": 10.0},
    ]
    elected_leader = engine.elect_fallback_leader("cluster_gamma", candidates)
    assert elected_leader == "candidate_b"
    assert engine.get_cluster_leader("cluster_gamma") == "candidate_b"

    # Test leader override
    round_info = engine.create_voting_round(
        cluster_id="cluster_gamma",
        proposal_type="emergency_shutdown",
        proposal_payload={},
        initiator_agent_id="candidate_c",
    )
    override_res = engine.leader_override(
        round_id=round_info["round_id"],
        leader_agent_id="candidate_b",
        override_decision="veto",
        reason="Leader emergency veto",
    )
    assert override_res["status"] == "leader_override"
    assert override_res["final_outcome"] == "override_veto"


def test_load_rebalancer_detection_and_redirection():
    rebalancer = A2ALoadRebalancer()

    # Register overloaded worker with tasks
    rebalancer.register_node(
        agent_id="node_overloaded",
        agent_name="heavy_worker",
        capabilities=["codegen"],
        cpu_utilization=90.0,
        memory_utilization=85.0,
    )
    rebalancer.assign_task("node_overloaded", {"task_id": "t1", "required_capabilities": ["codegen"]})
    rebalancer.assign_task("node_overloaded", {"task_id": "t2", "required_capabilities": ["codegen"]})

    # Register healthy idle worker
    rebalancer.register_node(
        agent_id="node_healthy",
        agent_name="idle_worker",
        capabilities=["codegen", "testing"],
        cpu_utilization=15.0,
        memory_utilization=20.0,
    )

    health = rebalancer.evaluate_mesh_health()
    assert len(health["overloaded_nodes"]) == 1
    assert len(health["healthy_nodes"]) == 1

    # Plan and execute rebalancing
    rebalance_res = rebalancer.plan_and_execute_rebalance()
    assert rebalance_res["rebalanced"] is True
    assert rebalance_res["reassigned_tasks_count"] >= 1
    assert len(rebalancer.get_node_tasks("node_healthy")) >= 1


def test_load_rebalancer_heartbeat_timeout_eviction():
    rebalancer = A2ALoadRebalancer()

    rebalancer.register_node(
        agent_id="node_dead",
        agent_name="dead_node",
        capabilities=["general"],
    )
    rebalancer.assign_task("node_dead", {"task_id": "urgent_task", "required_capabilities": ["general"]})

    # Register standby node
    rebalancer.register_node(
        agent_id="node_standby",
        agent_name="standby_worker",
        capabilities=["general"],
    )

    # Artificially age the dead node's heartbeat
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=30)).isoformat()
    rebalancer._nodes["node_dead"]["last_heartbeat"] = old_time

    health = rebalancer.evaluate_mesh_health(heartbeat_timeout_sec=10.0)
    assert len(health["unhealthy_nodes"]) == 1

    rebalance_res = rebalancer.plan_and_execute_rebalance(heartbeat_timeout_sec=10.0)
    assert rebalance_res["rebalanced"] is True
    assert len(rebalancer.get_node_tasks("node_dead")) == 0
    assert len(rebalancer.get_node_tasks("node_standby")) == 1
