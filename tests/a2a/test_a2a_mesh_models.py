# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-A2A-004-MODELS"
# purpose: "Unit tests for DNK-A2A-004 Cross-Platform Agent Protocol & Mesh ORM models"
# canonical_source: true
# alters_files: ["tests/a2a/test_a2a_mesh_models.py"]
# triggers_tasks: ["DNK-A2A-004-PHASE1"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone
from apps.api.db.models import (
    A2AFederatedAgent,
    A2ACapabilitySchema,
    A2AMessageEnvelope,
    A2AStreamSession,
    A2ARoutingTable,
    A2AHealthProbe,
)


def test_a2a_federated_agent_model():
    agent = A2AFederatedAgent(
        workspace_id="ws-test",
        agent_name="autogpt-researcher-01",
        platform="autogpt",
        protocol_version="a2a/v2",
        api_endpoint="https://external-agent.ai/a2a/rpc",
        streaming_endpoint="https://external-agent.ai/a2a/stream",
        auth_token_hash="hash123456",
        trust_tier="tier-1",
        capabilities=["deep_research", "web_scraping"],
        status="active",
        max_concurrency=10.0,
        current_load=2.0,
        reputation_score=0.98,
        metadata_json={"framework_version": "0.5.2"},
    )
    d = agent.to_dict()
    assert d["agent_name"] == "autogpt-researcher-01"
    assert d["platform"] == "autogpt"
    assert d["trust_tier"] == "tier-1"
    assert "deep_research" in d["capabilities"]
    assert d["max_concurrency"] == 10.0
    assert d["metadata"]["framework_version"] == "0.5.2"


def test_a2a_capability_schema_model():
    cap = A2ACapabilitySchema(
        workspace_id="ws-test",
        capability_key="deep_research",
        display_name="Deep Web Research",
        description="Autonomous iterative multi-source web research",
        version="1.1.0",
        input_schema={"type": "object", "properties": {"query": {"type": "string"}}},
        output_schema={"type": "object", "properties": {"summary": {"type": "string"}}},
        target_sla_latency_ms=2500.0,
        cost_per_invocation_units=0.05,
        rate_limit_rpm=60,
        required_trust_tier="tier-2",
        is_deprecated=False,
    )
    d = cap.to_dict()
    assert d["capability_key"] == "deep_research"
    assert d["display_name"] == "Deep Web Research"
    assert d["target_sla_latency_ms"] == 2500.0
    assert d["is_deprecated"] is False


def test_a2a_message_envelope_model():
    env = A2AMessageEnvelope(
        workspace_id="ws-test",
        trace_id="trc-9876",
        span_id="spn-1234",
        parent_span_id="spn-0000",
        sender_agent_id="fed_agent_01",
        recipient_agent_id="fed_agent_02",
        protocol_pattern="supervisor-worker",
        method="task.delegate",
        payload={"goal": "Analyze competitive landscape"},
        headers={"x-dnk-priority": "high"},
        signature_hash="sig-sha256-abc",
        status="delivered",
        delivery_attempts=1,
        latency_ms=120.5,
    )
    d = env.to_dict()
    assert d["trace_id"] == "trc-9876"
    assert d["sender_agent_id"] == "fed_agent_01"
    assert d["method"] == "task.delegate"
    assert d["payload"]["goal"] == "Analyze competitive landscape"
    assert d["status"] == "delivered"


def test_a2a_stream_session_model():
    session = A2AStreamSession(
        workspace_id="ws-test",
        session_token="stream-tok-abc-123",
        sender_agent_id="agent_sender",
        receiver_agent_id="agent_receiver",
        stream_type="cot_stream",
        status="active",
        backpressure_window_size=100,
        messages_streamed=42,
        bytes_streamed=10240.0,
    )
    d = session.to_dict()
    assert d["session_token"] == "stream-tok-abc-123"
    assert d["stream_type"] == "cot_stream"
    assert d["status"] == "active"
    assert d["messages_streamed"] == 42
    assert d["bytes_streamed"] == 10240.0


def test_a2a_routing_table_model():
    route = A2ARoutingTable(
        workspace_id="ws-test",
        capability_key="deep_research",
        primary_agent_id="fed_agent_01",
        fallback_agent_ids=["fed_agent_02", "fed_agent_03"],
        circuit_breaker_status="CLOSED",
        failure_count=0,
        consecutive_success_count=15,
        health_weight=1.0,
        is_active=True,
    )
    d = route.to_dict()
    assert d["capability_key"] == "deep_research"
    assert d["primary_agent_id"] == "fed_agent_01"
    assert len(d["fallback_agent_ids"]) == 2
    assert d["circuit_breaker_status"] == "CLOSED"
    assert d["is_active"] is True


def test_a2a_health_probe_model():
    probe = A2AHealthProbe(
        workspace_id="ws-test",
        agent_id="fed_agent_01",
        probe_type="synthetic_rpc",
        is_healthy=True,
        latency_ms=45.2,
        cpu_percent=12.4,
        memory_mb=256.0,
        status_code=200,
        probe_details={"rpc_method": "ping", "response_bytes": 64},
    )
    d = probe.to_dict()
    assert d["agent_id"] == "fed_agent_01"
    assert d["probe_type"] == "synthetic_rpc"
    assert d["is_healthy"] is True
    assert d["latency_ms"] == 45.2
    assert d["status_code"] == 200
    assert d["probe_details"]["rpc_method"] == "ping"
