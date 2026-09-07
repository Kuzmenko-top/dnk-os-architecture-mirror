# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-A2A-004-SERVICES-PHASE3"
# purpose: "Unit tests for Mesh Router, Circuit Breaker and Health Probe Service (DNK-A2A-004 Phase 3)"
# canonical_source: true
# alters_files: ["tests/a2a/test_a2a_mesh_router_and_health.py"]
# triggers_tasks: ["DNK-A2A-004-PHASE3"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import time
import pytest
from apps.api.services.a2a_mesh_router_service import A2AMeshRouterService, CircuitBreakerState
from apps.api.services.a2a_health_probe_service import A2AHealthProbeService


# ============================================================================
# A2AMeshRouterService Tests
# ============================================================================

def test_mesh_router_registration_and_primary_selection():
    router = A2AMeshRouterService()
    router.register_route(
        workspace_id="ws-alpha",
        capability_key="video_generation",
        primary_agent_id="agent_primary",
        fallback_agent_ids=["agent_fb1", "agent_fb2"],
        routing_strategy="least_loaded",
    )

    agents_map = {
        "agent_primary": {"id": "agent_primary", "status": "active", "capabilities": ["video_generation"]},
        "agent_fb1": {"id": "agent_fb1", "status": "active", "capabilities": ["video_generation"]},
        "agent_fb2": {"id": "agent_fb2", "status": "active", "capabilities": ["video_generation"]},
    }

    # Selection with healthy primary
    res = router.select_target_agent("video_generation", agents_map)
    assert res["success"] is True
    assert res["agent_id"] == "agent_primary"
    assert res["is_fallback"] is False


def test_mesh_router_failover_and_circuit_breaker():
    # Router with 2 failure threshold, 0.2s recovery timeout
    router = A2AMeshRouterService(failure_threshold=2, recovery_timeout_s=0.2, half_open_success_threshold=1)
    router.register_route(
        workspace_id="ws-alpha",
        capability_key="code_review",
        primary_agent_id="agent_primary",
        fallback_agent_ids=["agent_fb1"],
    )

    agents_map = {
        "agent_primary": {"id": "agent_primary", "status": "active", "capabilities": ["code_review"]},
        "agent_fb1": {"id": "agent_fb1", "status": "active", "capabilities": ["code_review"]},
    }

    # 1. First failure on primary (circuit remains CLOSED)
    router.record_failure("agent_primary")
    assert router.is_agent_available("agent_primary") is True

    # 2. Second failure on primary (trips circuit to OPEN)
    router.record_failure("agent_primary")
    assert router.is_agent_available("agent_primary") is False

    # 3. Router should automatically select fallback
    res_failover = router.select_target_agent("code_review", agents_map)
    assert res_failover["success"] is True
    assert res_failover["agent_id"] == "agent_fb1"
    assert res_failover["is_fallback"] is True

    # 4. Wait for recovery timeout -> enters HALF_OPEN
    time.sleep(0.25)
    assert router.is_agent_available("agent_primary") is True

    # 5. Record success during probing -> transitions to CLOSED
    router.record_success("agent_primary")
    res_recovered = router.select_target_agent("code_review", agents_map)
    assert res_recovered["agent_id"] == "agent_primary"
    assert res_recovered["is_fallback"] is False


# ============================================================================
# A2AHealthProbeService Tests
# ============================================================================

def test_health_probe_lifecycle_and_quarantine():
    health = A2AHealthProbeService(
        quarantine_failure_threshold=2,
        recovery_success_threshold=2,
        max_acceptable_latency_ms=1000.0,
    )

    # 1. Record healthy probe
    r1 = health.record_probe_result("ws-alpha", "node_1", is_healthy=True, latency_ms=80.0)
    assert r1["node_status"] == "healthy"
    assert r1["is_quarantined"] is False

    # 2. High latency probe (> 1000ms SLA) -> treated as failure
    r2 = health.record_probe_result("ws-alpha", "node_1", is_healthy=True, latency_ms=1500.0)
    assert r2["node_status"] == "degraded"
    assert r2["is_quarantined"] is False

    # 3. Second failure -> enters quarantine
    r3 = health.record_probe_result("ws-alpha", "node_1", is_healthy=False, latency_ms=200.0)
    assert r3["node_status"] == "quarantined"
    assert r3["is_quarantined"] is True
    assert "node_1" in health.list_quarantined_agents()

    # 4. Recovery probing: 1st success (still quarantined)
    r4 = health.record_probe_result("ws-alpha", "node_1", is_healthy=True, latency_ms=75.0)
    assert r4["is_quarantined"] is True

    # 5. 2nd success -> leaves quarantine
    r5 = health.record_probe_result("ws-alpha", "node_1", is_healthy=True, latency_ms=85.0)
    assert r5["is_quarantined"] is False
    assert r5["node_status"] == "healthy"

    # Summary metrics
    summary = health.get_agent_health_summary("node_1")
    assert summary["total_probes"] == 5
    assert summary["failed_probes"] == 2
    assert summary["uptime_pct"] == 60.0
