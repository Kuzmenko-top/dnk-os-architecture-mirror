# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-A2A-004-SERVICES-PHASE2"
# purpose: "Unit tests for Federation Registry, Message Codec and Streaming Engine (DNK-A2A-004 Phase 2)"
# canonical_source: true
# alters_files: ["tests/a2a/test_a2a_federation_services.py"]
# triggers_tasks: ["DNK-A2A-004-PHASE2"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import pytest
from apps.api.services.a2a_federation_registry_service import A2AFederationRegistryService
from apps.api.services.a2a_message_codec_service import A2AMessageCodecService
from apps.api.services.a2a_streaming_engine import A2AStreamingEngine


# ============================================================================
# A2AFederationRegistryService Tests
# ============================================================================

def test_federation_registry_agent_lifecycle():
    service = A2AFederationRegistryService()

    # 1. Register agent with auth token
    agent = service.register_agent(
        workspace_id="ws-alpha",
        agent_name="crewai_research_lead",
        platform="crewai",
        api_endpoint="https://crewai-mesh.local/rpc",
        capabilities=["market_analysis", "report_synthesis"],
        trust_tier="tier-1",
        auth_token="super-secret-a2a-token-123",
        max_concurrency=8.0,
    )
    agent_id = agent["id"]
    assert agent_id.startswith("fed_agent_")
    assert agent["status"] == "active"
    assert agent["trust_tier"] == "tier-1"

    # 2. Authenticate agent
    assert service.authenticate_agent(agent_id, "super-secret-a2a-token-123") is True
    assert service.authenticate_agent(agent_id, "wrong-token") is False
    assert service.authenticate_agent("non_existent", "token") is False

    # 3. Heartbeat & reputation updates
    updated = service.update_agent_heartbeat(agent_id, current_load=3.5, status="active")
    assert updated is not None
    assert updated["current_load"] == 3.5

    rep = service.update_reputation(agent_id, -0.05)
    assert rep == 0.95


def test_federation_registry_capability_validation_and_discovery():
    service = A2AFederationRegistryService()

    # Register Capability Schema
    service.register_capability_schema(
        workspace_id="ws-alpha",
        capability_key="code_synthesis",
        display_name="Code Synthesis Engine",
        input_schema={"required": ["prompt", "target_language"]},
        output_schema={"required": ["code", "ast_valid"]},
        required_trust_tier="tier-2",
    )

    # Register 2 agents
    agent1 = service.register_agent(
        workspace_id="ws-alpha",
        agent_name="opencode_bot",
        platform="opencode",
        api_endpoint="https://opencode.local/rpc",
        capabilities=["code_synthesis"],
        trust_tier="tier-1",
    )
    agent2 = service.register_agent(
        workspace_id="ws-alpha",
        agent_name="untrusted_bot",
        platform="custom",
        api_endpoint="https://untrusted.local/rpc",
        capabilities=["code_synthesis"],
        trust_tier="tier-3",  # lower trust
    )

    # Capability validation: Valid payload
    val_ok = service.validate_capability_invocation(
        "code_synthesis",
        {"prompt": "Write a binary search", "target_language": "python"},
        caller_trust_tier="tier-1",
    )
    assert val_ok["valid"] is True

    # Capability validation: Missing field
    val_missing = service.validate_capability_invocation(
        "code_synthesis",
        {"prompt": "Write a binary search"},  # missing target_language
        caller_trust_tier="tier-1",
    )
    assert val_missing["valid"] is False
    assert "target_language" in val_missing["error"]

    # Capability validation: Trust tier violation
    val_trust = service.validate_capability_invocation(
        "code_synthesis",
        {"prompt": "x", "target_language": "py"},
        caller_trust_tier="tier-3",  # tier-3 cannot call tier-2 required capability
    )
    assert val_trust["valid"] is False
    assert "Insufficient trust tier" in val_trust["error"]

    # Discovery
    found = service.discover_agents_by_capability("code_synthesis", min_trust_tier="tier-2")
    assert len(found) == 1
    assert found[0]["id"] == agent1["id"]


# ============================================================================
# A2AMessageCodecService Tests
# ============================================================================

def test_message_codec_signing_and_verification():
    codec = A2AMessageCodecService()
    secret = "mesh-hmac-shared-key-2026"

    envelope = codec.create_envelope(
        workspace_id="ws-alpha",
        sender_agent_id="fed_001",
        recipient_agent_id="fed_002",
        method="task.execute",
        payload={"action": "compile", "target": "main.py"},
        secret_key=secret,
    )
    assert envelope["signature_hash"] is not None
    assert envelope["trace_id"].startswith("trc_")

    # Encode to JSON
    wire_json = codec.encode_wire_format(envelope, format_type="json")
    decoded, is_valid = codec.decode_wire_format(wire_json, format_type="json", secret_key=secret)
    assert is_valid is True
    assert decoded["method"] == "task.execute"

    # Tampered payload detection
    tampered = dict(envelope)
    tampered["payload"] = {"action": "compile", "target": "malicious.py"}
    tampered_wire = codec.encode_wire_format(tampered, format_type="json")
    _, tampered_valid = codec.decode_wire_format(tampered_wire, format_type="json", secret_key=secret)
    assert tampered_valid is False

    # Base64 encoding roundtrip
    wire_b64 = codec.encode_wire_format(envelope, format_type="base64")
    decoded_b64, valid_b64 = codec.decode_wire_format(wire_b64, format_type="base64", secret_key=secret)
    assert valid_b64 is True
    assert decoded_b64["id"] == envelope["id"]


def test_message_codec_trace_context():
    codec = A2AMessageCodecService()
    headers = {"Authorization": "Bearer token"}
    injected = codec.inject_trace_context(headers, trace_id="trc-100", span_id="spn-200", parent_span_id="spn-050")
    assert injected["x-dnk-trace-id"] == "trc-100"
    assert injected["x-dnk-span-id"] == "spn-200"
    assert injected["x-dnk-parent-span-id"] == "spn-050"

    extracted = codec.extract_trace_context(injected)
    assert extracted["trace_id"] == "trc-100"
    assert extracted["span_id"] == "spn-200"
    assert extracted["parent_span_id"] == "spn-050"


# ============================================================================
# A2AStreamingEngine Tests
# ============================================================================

@pytest.mark.asyncio
async def test_streaming_engine_lifecycle_and_backpressure():
    engine = A2AStreamingEngine()

    session = engine.create_session(
        workspace_id="ws-alpha",
        sender_agent_id="fed_001",
        receiver_agent_id="fed_002",
        stream_type="cot_stream",
        backpressure_window_size=3,
    )
    token = session["session_token"]
    assert session["status"] == "open"

    # Push events
    res1 = await engine.push_event(token, "cot_thought", {"thought": "Step 1: Loading AST"})
    assert res1["success"] is True
    assert res1["seq"] == 1

    res2 = await engine.push_event(token, "cot_thought", {"thought": "Step 2: Traversing tree"})
    assert res2["success"] is True

    res3 = await engine.push_event(token, "cot_thought", {"thought": "Step 3: Checking imports"})
    assert res3["success"] is True

    # 4th push should trigger backpressure timeout because queue size is 3 and no consumer is draining
    res_overflow = await engine.push_event(token, "cot_thought", {"thought": "Step 4: Overflow"}, timeout_s=0.1)
    assert res_overflow["success"] is False
    assert "Backpressure" in res_overflow["error"]

    # SSE formatting
    sse_frame = engine.format_sse_frame("cot_thought", {"thought": "Hello"}, event_id="evt-1")
    assert sse_frame.startswith("id: evt-1\nevent: cot_thought\ndata: ")
    assert sse_frame.endswith("\n\n")

    # Close session
    close_res = engine.close_session(token, reason="completed")
    assert close_res["success"] is True
    sess = engine.get_session(token)
    assert sess is not None
    assert sess["status"] == "closed"
