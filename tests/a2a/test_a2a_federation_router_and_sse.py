# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-A2A-004-ROUTER-PHASE4"
# purpose: "Integration tests for A2A Federation REST Router & SSE Streaming (DNK-A2A-004 Phase 4)"
# canonical_source: true
# alters_files: ["tests/a2a/test_a2a_federation_router_and_sse.py"]
# triggers_tasks: ["DNK-A2A-004-PHASE4"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_federation_router_agent_and_capability_crud():
    # 1. Register Capability
    cap_resp = client.post(
        "/api/v1/a2a/mesh/capabilities",
        json={
            "workspace_id": "ws-alpha",
            "capability_key": "distributed_analysis",
            "display_name": "Distributed Analysis",
            "input_schema": {"required": ["query"]},
            "output_schema": {"required": ["insights"]},
            "target_sla_latency_ms": 1200.0,
            "required_trust_tier": "tier-2",
        },
    )
    assert cap_resp.status_code == 201
    cap_data = cap_resp.json()
    assert cap_data["capability"]["capability_key"] == "distributed_analysis"

    # 2. Register Agent
    agent_resp = client.post(
        "/api/v1/a2a/mesh/agents",
        json={
            "workspace_id": "ws-alpha",
            "agent_name": "autogpt_market_scout",
            "platform": "autogpt",
            "api_endpoint": "https://autogpt.mesh.local/rpc",
            "capabilities": ["distributed_analysis"],
            "trust_tier": "tier-2",
            "auth_token": "secret-mesh-token",
        },
    )
    assert agent_resp.status_code == 201
    agent_data = agent_resp.json()
    agent_id = agent_data["agent"]["id"]
    assert agent_id.startswith("fed_agent_")

    # 3. List agents
    list_resp = client.get("/api/v1/a2a/mesh/agents", params={"capability": "distributed_analysis"})
    assert list_resp.status_code == 200
    assert list_resp.json()["count"] >= 1

    # 4. Get Agent
    get_resp = client.get(f"/api/v1/a2a/mesh/agents/{agent_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["agent"]["agent_name"] == "autogpt_market_scout"


def test_federation_router_dispatch_and_routing():
    # Register 2 agents: primary & fallback
    ag1 = client.post(
        "/api/v1/a2a/mesh/agents",
        json={
            "workspace_id": "ws-alpha",
            "agent_name": "claude_code_primary",
            "platform": "claude_code",
            "api_endpoint": "https://claude.mesh.local/rpc",
            "capabilities": ["refactoring"],
            "trust_tier": "tier-1",
        },
    ).json()["agent"]

    ag2 = client.post(
        "/api/v1/a2a/mesh/agents",
        json={
            "workspace_id": "ws-alpha",
            "agent_name": "opencode_fallback",
            "platform": "opencode",
            "api_endpoint": "https://opencode.mesh.local/rpc",
            "capabilities": ["refactoring"],
            "trust_tier": "tier-1",
        },
    ).json()["agent"]

    # Register Route
    route_resp = client.post(
        "/api/v1/a2a/mesh/routes",
        json={
            "workspace_id": "ws-alpha",
            "capability_key": "refactoring",
            "primary_agent_id": ag1["id"],
            "fallback_agent_ids": [ag2["id"]],
            "routing_strategy": "least_loaded",
        },
    )
    assert route_resp.status_code == 201

    # Dispatch task
    dispatch_resp = client.post(
        "/api/v1/a2a/mesh/dispatch",
        json={
            "workspace_id": "ws-alpha",
            "capability_key": "refactoring",
            "sender_agent_id": "gerych_builder",
            "method": "refactor.ast",
            "payload": {"file": "core.py", "action": "optimize"},
            "secret_key": "shared-a2a-key",
        },
    )
    assert dispatch_resp.status_code == 200
    dispatch_data = dispatch_resp.json()
    assert dispatch_data["dispatched_to"] == ag1["id"]
    assert dispatch_data["envelope"]["signature_hash"] is not None


def test_federation_router_probes_and_health():
    # Record probe
    probe_resp = client.post(
        "/api/v1/a2a/mesh/probes",
        json={
            "workspace_id": "ws-alpha",
            "agent_id": "agent_test_node",
            "probe_type": "http_ping",
            "is_healthy": True,
            "latency_ms": 45.0,
            "cpu_usage_pct": 12.5,
            "memory_usage_pct": 34.0,
        },
    )
    assert probe_resp.status_code == 200
    assert probe_resp.json()["result"]["node_status"] == "healthy"

    # Query health
    health_resp = client.get("/api/v1/a2a/mesh/health/agent_test_node")
    assert health_resp.status_code == 200
    health_data = health_resp.json()["health"]
    assert health_data["uptime_pct"] == 100.0
    assert health_data["avg_latency_ms"] == 45.0


def test_mesh_sse_streaming_lifecycle():
    # 1. Create Stream Session
    sess_resp = client.post(
        "/api/v1/a2a/mesh/stream/sessions",
        json={
            "workspace_id": "ws-alpha",
            "sender_agent_id": "gerych_builder",
            "receiver_agent_id": "langgraph_orchestrator",
            "stream_type": "cot_stream",
            "backpressure_window_size": 20,
        },
    )
    assert sess_resp.status_code == 201
    session_tok = sess_resp.json()["session"]["session_token"]

    # 2. Push Stream Events
    push1 = client.post(
        f"/api/v1/a2a/mesh/stream/{session_tok}/events",
        json={"event_type": "cot_thought", "data": {"step": "Analyzing AST", "confidence": 0.98}},
    )
    assert push1.status_code == 200
    assert push1.json()["seq"] == 1

    push2 = client.post(
        f"/api/v1/a2a/mesh/stream/{session_tok}/events",
        json={"event_type": "token_chunk", "data": {"delta": "def optimize():"}},
    )
    assert push2.status_code == 200
    assert push2.json()["seq"] == 2

    # 3. Close Stream Session
    close_resp = client.post(
        f"/api/v1/a2a/mesh/stream/{session_tok}/close",
        json={"reason": "completed"},
    )
    assert close_resp.status_code == 200
    assert close_resp.json()["session"]["status"] == "closed"
