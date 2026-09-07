# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-TEST-ROUTER-PHASE4"
# purpose: "E2E Integration Tests for A2A Mesh FastAPI REST and WebSocket Endpoints"
# canonical_source: true
# alters_files: ["tests/a2a/test_a2a_router_phase4.py"]
# triggers_tasks: ["DNK-A2A-003-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_agent_registration_and_discovery():
    # 1. Register agent
    resp = client.post("/a2a/mesh/agents/register", json={
        "agent_id": "mesh_agent_007",
        "agent_name": "James Bond AI",
        "role": "special_ops",
        "capabilities": ["stealth", "analysis", "fastapi"],
        "cpu_utilization": 25.0,
        "memory_utilization": 30.0,
        "reputation_score": 1.5,
        "workspace_id": "ws-phase4",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert data["agent"]["agent_name"] == "James Bond AI"

    # 2. List agents
    resp = client.get("/a2a/mesh/agents?workspace_id=ws-phase4")
    assert resp.status_code == 200
    agents_data = resp.json()
    assert agents_data["status"] == "success"
    assert any(a["agent_name"] == "James Bond AI" for a in agents_data["agents"])


def test_proposal_evaluation_and_contracts():
    # Register agents
    client.post("/a2a/mesh/agents/register", json={
        "agent_id": "agent_del_1",
        "agent_name": "Delegator One",
        "capabilities": ["orchestration"],
        "workspace_id": "ws-contract",
    })
    client.post("/a2a/mesh/agents/register", json={
        "agent_id": "agent_exec_1",
        "agent_name": "Executor One",
        "capabilities": ["code_gen", "wasm"],
        "cpu_utilization": 40.0,
        "memory_utilization": 50.0,
        "workspace_id": "ws-contract",
    })

    # Evaluate proposal
    eval_resp = client.post("/a2a/mesh/proposals/evaluate", json={
        "executor_id": "agent_exec_1",
        "required_capabilities": ["code_gen"],
        "offered_budget_units": 60.0,
    })
    assert eval_resp.status_code == 200
    assert eval_resp.json()["evaluation"]["accepted"] is True

    # Negotiate & create SLA contract
    neg_resp = client.post("/a2a/mesh/contracts/negotiate", json={
        "delegator_id": "agent_del_1",
        "executor_id": "agent_exec_1",
        "task_id": "task_wasm_compiler_01",
        "agreed_budget_units": 60.0,
        "max_latency_ms": 500.0,
        "retry_limit": 2,
        "workspace_id": "ws-contract",
    })
    assert neg_resp.status_code == 201
    contract = neg_resp.json()["contract"]
    contract_id = contract["id"]
    assert contract["status"] == "active"

    # Fulfill contract
    fulfill_resp = client.post(f"/a2a/mesh/contracts/{contract_id}/fulfill")
    assert fulfill_resp.status_code == 200
    assert fulfill_resp.json()["contract"]["status"] == "fulfilled"


def test_auction_lifecycle_and_bidding():
    # 1. Create Auction
    auc_resp = client.post("/a2a/mesh/auctions", json={
        "task_id": "task_distributed_render_99",
        "task_name": "4K Video Rendering Task",
        "initiator_agent_id": "supervisor_media",
        "required_capabilities": ["gpu_render", "ffmpeg"],
        "max_budget_units": 150.0,
        "auction_duration_seconds": 30.0,
        "workspace_id": "ws-auction",
    })
    assert auc_resp.status_code == 201
    auction_id = auc_resp.json()["auction"]["id"]

    # 2. Submit Bids
    bid1 = client.post(f"/a2a/mesh/auctions/{auction_id}/bids", json={
        "bidder_agent_id": "worker_gpu_alpha",
        "bid_price_units": 120.0,
        "estimated_duration_ms": 300.0,
        "current_load_percentage": 20.0,
        "agent_reputation": 1.8,
    })
    assert bid1.status_code == 201

    bid2 = client.post(f"/a2a/mesh/auctions/{auction_id}/bids", json={
        "bidder_agent_id": "worker_gpu_beta",
        "bid_price_units": 80.0,
        "estimated_duration_ms": 150.0,
        "current_load_percentage": 10.0,
        "agent_reputation": 1.9,
    })
    assert bid2.status_code == 201

    # 3. Resolve Auction
    res_resp = client.post(f"/a2a/mesh/auctions/{auction_id}/resolve")
    assert res_resp.status_code == 200
    res_data = res_resp.json()
    assert res_data["status"] == "success"
    assert res_data["winner_bid"]["bidder_agent_id"] == "worker_gpu_beta"
    assert res_data["contract"] is not None


def test_consensus_voting_and_quorum_resolution():
    # 1. Create consensus voting round
    round_resp = client.post("/a2a/mesh/consensus/rounds", json={
        "proposal_type": "protocol_upgrade_v2",
        "proposal_payload": {"feature_flag": "enabled_a2a_wasm"},
        "initiator_agent_id": "prime_leader_node",
        "cluster_id": "cluster-gamma-01",
        "quorum_threshold_percentage": 60.0,
        "timeout_seconds": 60.0,
        "workspace_id": "ws-consensus",
    })
    assert round_resp.status_code == 201
    round_id = round_resp.json()["round"]["round_id"]

    # 2. Cast Votes
    v1 = client.post(f"/a2a/mesh/consensus/rounds/{round_id}/vote", json={
        "voter_agent_id": "node_voter_1",
        "decision": "approve",
        "voting_power": 2.0,
        "reason": "All benchmarks verified",
        "workspace_id": "ws-consensus",
    })
    assert v1.status_code == 200

    v2 = client.post(f"/a2a/mesh/consensus/rounds/{round_id}/vote", json={
        "voter_agent_id": "node_voter_2",
        "decision": "approve",
        "voting_power": 1.5,
        "reason": "Approved",
        "workspace_id": "ws-consensus",
    })
    assert v2.status_code == 200

    # 3. Resolve Consensus Round
    res_resp = client.post(f"/a2a/mesh/consensus/rounds/{round_id}/resolve")
    assert res_resp.status_code == 200
    res_data = res_resp.json()["round"]
    assert res_data["status"] == "approved"
    assert res_data["final_outcome"] in ["approved", "consensus_reached"]


def test_fallback_leader_election():
    resp = client.post("/a2a/mesh/consensus/leader-elect", json={
        "cluster_id": "cluster-lead-001",
        "candidates": [
            {"agent_id": "node_candidate_a", "reputation_score": 1.2, "cpu_utilization": 50.0, "memory_utilization": 40.0},
            {"agent_id": "node_candidate_b", "reputation_score": 1.9, "cpu_utilization": 20.0, "memory_utilization": 20.0},
            {"agent_id": "node_candidate_c", "reputation_score": 1.5, "cpu_utilization": 10.0, "memory_utilization": 15.0},
        ],
    })
    assert resp.status_code == 200
    assert resp.json()["leader_id"] == "node_candidate_b"


def test_heartbeat_health_and_load_rebalancing():
    # Register nodes and record heartbeats
    client.post("/a2a/mesh/heartbeat", json={
        "agent_id": "overloaded_node_x",
        "cpu_utilization": 95.0,
        "memory_utilization": 90.0,
        "active_tasks": [{"task_id": "heavy_task_1", "required_capabilities": ["calc"]}],
    })

    client.post("/a2a/mesh/heartbeat", json={
        "agent_id": "idle_node_y",
        "cpu_utilization": 15.0,
        "memory_utilization": 20.0,
        "active_tasks": [],
    })

    # Health summary
    health_resp = client.get("/a2a/mesh/health")
    assert health_resp.status_code == 200
    health_data = health_resp.json()["health"]
    assert health_data["total_nodes"] >= 2
    assert any(n["agent_id"] == "overloaded_node_x" for n in health_data["overloaded_nodes"])

    # Rebalance
    reb_resp = client.post("/a2a/mesh/rebalance", json={
        "cpu_threshold": 80.0,
        "ram_threshold": 80.0,
        "heartbeat_timeout_sec": 15.0,
    })
    assert reb_resp.status_code == 200
    result = reb_resp.json()["result"]
    assert result["rebalanced"] is True
    assert result["reassigned_tasks_count"] >= 1


def test_websocket_telemetry_stream():
    with client.websocket_connect("/a2a/mesh/ws/telemetry") as ws:
        data = ws.receive_json()
        assert data["type"] == "mesh_telemetry"
        assert "mesh_health" in data
        assert "agents_count" in data
        assert "nodes" in data


def test_websocket_events_stream():
    with client.websocket_connect("/a2a/mesh/ws/events") as ws:
        init_data = ws.receive_json()
        assert init_data["type"] == "connection_established"
        assert "A2A Mesh Event Bus" in init_data["message"]

        # Send ping
        ws.send_text(json.dumps({"type": "ping"}))
        pong_data = ws.receive_json()
        assert pong_data["type"] == "pong"
