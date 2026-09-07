# --- DNK-MRH-HEADER ---
# mrh_id: "tests_a2a_test_a2a_router_ws_phase4"
# purpose: "Integration & E2E Tests for A2A Mesh Router, WebSockets, Live Telemetry & Quorum Dashboard (DNK-A2A-003 Phase 4)"
# author: "DNK-e.com Maksym & Gerych Builder"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_agent_registration_and_proposal_evaluation():
    """Test registering an agent and evaluating a negotiation proposal via REST."""
    reg_res = client.post(
        "/a2a/mesh/agents/register",
        json={
            "agent_id": "agent_test_01",
            "agent_name": "Test Agent 01",
            "capabilities": ["code_generation", "security_audit"],
            "reputation_score": 95.0,
            "cost_per_token": 0.002,
        },
    )
    assert reg_res.status_code in [200, 201]
    reg_data = reg_res.json()
    assert reg_data["status"] == "success"

    eval_res = client.post(
        "/a2a/mesh/proposals/evaluate",
        json={
            "proposed_price_units": 10.0,
            "proposed_duration_ms": 3000.0,
            "required_capabilities": ["code_generation"],
            "initiator_reputation": 90.0,
        },
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert "accepted" in eval_data or "status" in eval_data or "evaluation" in eval_data


def test_contract_negotiation_flow():
    """Test creating, agreeing to, and fulfilling a negotiation contract."""
    for aid in ["initiator_node", "target_node"]:
        client.post(
            "/a2a/mesh/agents/register",
            json={
                "agent_id": aid,
                "agent_name": f"Node {aid}",
                "capabilities": ["distributed_task"],
                "reputation_score": 90.0,
            },
        )

    init_res = client.post(
        "/a2a/mesh/contracts/negotiate",
        json={
            "task_id": "task_dist_01",
            "initiator_agent_id": "initiator_node",
            "target_agent_id": "target_node",
            "task_description": "Run distributed verification",
            "agreed_price_units": 15.0,
            "max_duration_ms": 5000.0,
            "required_capabilities": ["distributed_task"],
        },
    )
    assert init_res.status_code in [200, 201]
    contract = init_res.json().get("contract", {})
    contract_id = contract.get("id") or contract.get("contract_id", "contract_test_01")
    assert contract.get("status") in ["proposed", "active"]

    fulfill_res = client.post(f"/a2a/mesh/contracts/{contract_id}/fulfill")
    assert fulfill_res.status_code == 200
    assert fulfill_res.json()["status"] == "success"


def test_task_auction_creation_and_bidding():
    """Test creating an auction, submitting bids, and resolving winner."""
    auc_res = client.post(
        "/a2a/mesh/auctions",
        json={
            "task_id": "auction_task_99",
            "task_name": "Deep AST Scanning",
            "initiator_agent_id": "master_node",
            "max_budget_units": 50.0,
            "auction_duration_seconds": 60.0,
            "required_capabilities": ["ast_scan"],
        },
    )
    assert auc_res.status_code == 201
    auction = auc_res.json()["auction"]
    auction_id = auction.get("auction_id") or auction.get("id")

    bid_res1 = client.post(
        f"/a2a/mesh/auctions/{auction_id}/bids",
        json={
            "bidder_node_id": "worker_01",
            "bidder_agent_name": "Worker Node 1",
            "price_units": 40.0,
            "estimated_completion_ms": 2000.0,
            "reputation_score": 92.0,
        },
    )
    assert bid_res1.status_code in [200, 201]

    bid_res2 = client.post(
        f"/a2a/mesh/auctions/{auction_id}/bids",
        json={
            "bidder_node_id": "worker_02",
            "bidder_agent_name": "Worker Node 2",
            "price_units": 30.0,
            "estimated_completion_ms": 1500.0,
            "reputation_score": 96.0,
        },
    )
    assert bid_res2.status_code in [200, 201]

    resolve_res = client.post(f"/a2a/mesh/auctions/{auction_id}/resolve")
    assert resolve_res.status_code == 200
    res_data = resolve_res.json()
    assert res_data["status"] == "success"
    assert res_data["winner_bid"] is not None
    assert res_data["winner_bid"]["price_units"] == 30.0


def test_swarm_consensus_voting_round():
    """Test consensus voting round creation, multi-agent voting, and quorum determination."""
    round_res = client.post(
        "/a2a/mesh/consensus/rounds",
        json={
            "cluster_id": "cluster_alpha",
            "proposal_type": "deploy_upgrade",
            "proposal_payload": {"version": "v5.1.0"},
            "initiator_agent_id": "gerych_prime",
            "quorum_threshold_percentage": 66.7,
            "timeout_seconds": 30.0,
            "eligible_voter_ids": ["node_1", "node_2", "node_3"],
        },
    )
    assert round_res.status_code == 201
    round_id = round_res.json()["round"]["round_id"]

    v1 = client.post(
        f"/a2a/mesh/consensus/rounds/{round_id}/vote",
        json={"voter_agent_id": "node_1", "decision": "approve", "voting_power": 1.0},
    )
    assert v1.status_code == 200

    v2 = client.post(
        f"/a2a/mesh/consensus/rounds/{round_id}/vote",
        json={"voter_agent_id": "node_2", "decision": "approve", "voting_power": 1.0},
    )
    assert v2.status_code == 200

    v3 = client.post(
        f"/a2a/mesh/consensus/rounds/{round_id}/vote",
        json={"voter_agent_id": "node_3", "decision": "reject", "voting_power": 1.0},
    )
    assert v3.status_code == 200

    resolve_res = client.post(f"/a2a/mesh/consensus/rounds/{round_id}/resolve")
    assert resolve_res.status_code == 200
    round_result = resolve_res.json()["round"]
    assert round_result["status"] in ["approved", "active"]
    assert round_result["final_outcome"] is not None


def test_load_rebalancer_telemetry_and_rebalance():
    """Test node telemetry heartbeats, health status checks, and emergency rebalance trigger."""
    hb1 = client.post(
        "/a2a/mesh/heartbeat",
        json={
            "node_id": "heavy_node_1",
            "agent_id": "heavy_node_1",
            "cpu_utilization": 88.5,
            "memory_utilization": 75.0,
            "active_tasks_count": 12,
            "capabilities": ["compute_heavy"],
        },
    )
    assert hb1.status_code == 200

    hb2 = client.post(
        "/a2a/mesh/heartbeat",
        json={
            "node_id": "light_node_2",
            "agent_id": "light_node_2",
            "cpu_utilization": 15.0,
            "memory_utilization": 20.0,
            "active_tasks_count": 2,
            "capabilities": ["compute_heavy"],
        },
    )
    assert hb2.status_code == 200

    health_res = client.get("/a2a/mesh/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "success"

    rebal_res = client.post("/a2a/mesh/rebalance", json={})
    assert rebal_res.status_code == 200
    assert rebal_res.json()["status"] == "success"


def test_websocket_telemetry_streaming_and_ping():
    """Test real-time WebSocket connection, event receiving, and ping-pong."""
    with client.websocket_connect("/a2a/mesh/ws/events") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "connection_established"

        websocket.send_json({"type": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"
