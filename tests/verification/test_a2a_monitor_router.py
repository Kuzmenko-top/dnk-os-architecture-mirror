# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-ROUTER-DNK-A2A-001"
# purpose: "FastAPI Test Suite for A2A Multi-Agent Protocol & Swarm Monitor Router"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Auditor"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_api_list_agents():
    res = client.get("/a2a/agents")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] == 14
    agents = {a["name"]: a for a in data["agents"]}
    assert "gerych_auditor" in agents
    assert "gerych_builder" in agents
    assert "antigravity_supervisor" in agents
    assert "dnk_dev_fullstack" in agents
    assert "dnk_shopify" in agents
    assert "dnk_security_guard" in agents


def test_api_list_topics():
    res = client.get("/a2a/topics")
    assert res.status_code == 200
    data = res.json()
    assert "topics" in data
    assert isinstance(data["topics"], list)


def test_api_send_a2a_message_p2p():
    payload = {
        "sender": "gerych_auditor",
        "recipients": ["gerych_builder"],
        "method": "ast.verify_patch",
        "params": {"file": "apps/api/main.py", "clean": True},
        "pattern": "peer-to-peer",
        "timeout_ms": 3000,
    }
    res = client.post("/a2a/messages/send", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "sent"
    assert data["message"]["sender"] == "gerych_auditor"
    assert data["message"]["recipients"] == ["gerych_builder"]
    assert data["message"]["pattern"] == "peer-to-peer"


def test_api_broadcast_alert():
    payload = {
        "sender": "dnk_security_guard",
        "alert": {"event": "RATE_LIMIT_EXCEEDED", "ip": "10.0.0.1"},
        "severity": "CRITICAL",
    }
    res = client.post("/a2a/broadcast", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "broadcasted"
    assert data["recipients_count"] == 13  # All other agents in swarm


def test_api_consensus_proposal_and_voting():
    propose_payload = {
        "proposer": "antigravity_supervisor",
        "topic": "system.deploy_release",
        "description": "Approve v5.0.0 deployment to production",
        "mechanism": "majority-vote",
        "threshold": 0.5,
        "participants": ["gerych_auditor", "gerych_builder", "dnk_ops_agent"],
    }
    p_res = client.post("/a2a/consensus/propose", json=propose_payload)
    assert p_res.status_code == 200
    proposal = p_res.json()["proposal"]
    prop_id = proposal["proposal_id"]
    assert proposal["status"] == "pending"

    # Vote 1: Builder approves
    v1_res = client.post(
        "/a2a/consensus/vote",
        json={"proposal_id": prop_id, "voter": "gerych_builder", "vote": "approve"},
    )
    assert v1_res.status_code == 200

    # Vote 2: Ops approves -> Majority achieved (2/3 > 0.5)
    v2_res = client.post(
        "/a2a/consensus/vote",
        json={"proposal_id": prop_id, "voter": "dnk_ops_agent", "vote": "approve"},
    )
    assert v2_res.status_code == 200
    assert v2_res.json()["proposal"]["status"] == "accepted"

    # Query Status by ID
    status_res = client.get(f"/a2a/consensus/{prop_id}")
    assert status_res.status_code == 200
    assert status_res.json()["proposal"]["status"] == "accepted"


def test_api_distributed_locking():
    resource = "ecom_payment_gateway_config"
    acquire_payload = {
        "resource": resource,
        "agent": "dnk_shopify",
        "ttl_seconds": 15.0,
    }

    # 1. Acquire
    acq_res = client.post("/a2a/locks/acquire", json=acquire_payload)
    assert acq_res.status_code == 200
    assert acq_res.json()["status"] == "acquired"

    # 2. Conflicting Acquire fails with 409
    acq_conflict = client.post(
        "/a2a/locks/acquire",
        json={"resource": resource, "agent": "gerych_builder", "ttl_seconds": 10.0},
    )
    assert acq_conflict.status_code == 409

    # 3. List locks
    locks_res = client.get("/a2a/locks")
    assert locks_res.status_code == 200
    assert any(l["resource"] == resource for l in locks_res.json()["locks"])

    # 4. Release
    rel_res = client.post("/a2a/locks/release", json={"resource": resource, "agent": "dnk_shopify"})
    assert rel_res.status_code == 200
    assert rel_res.json()["status"] == "released"


def test_api_telemetry_and_dlq():
    # Fetch telemetry
    tel_res = client.get("/a2a/telemetry")
    assert tel_res.status_code == 200
    assert "telemetry" in tel_res.json()

    # Fetch DLQ
    dlq_res = client.get("/a2a/dlq")
    assert dlq_res.status_code == 200
    assert "dead_letters" in dlq_res.json()
