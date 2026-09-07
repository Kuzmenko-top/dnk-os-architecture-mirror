# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-HEALTH-001-MODELS-PHASE1"
# purpose: "Unit tests for Health Monitoring & Auto-Healing ORM Models (DNK-HEALTH-001 Phase 1)"
# canonical_source: true
# alters_files: ["tests/health/test_health_models.py"]
# triggers_tasks: ["DNK-HEALTH-001-PHASE1"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.db.models import (
    HealthMetricRule,
    SystemIncident,
    RemediationAction,
    AutoHealingPolicy,
    ServiceHealthSnapshot,
    AlertNotificationLog,
)


def test_health_metric_rule_model():
    rule = HealthMetricRule(
        workspace_id="ws-alpha",
        service_name="dnk_api_gateway",
        metric_name="p99_latency_ms",
        comparator=">",
        warning_threshold=500.0,
        critical_threshold=1500.0,
        evaluation_window_seconds=120,
        consecutive_breaches_required=3,
    )
    d = rule.to_dict()
    assert d["id"].startswith("hmr_")
    assert d["service_name"] == "dnk_api_gateway"
    assert d["metric_name"] == "p99_latency_ms"
    assert d["warning_threshold"] == 500.0
    assert d["critical_threshold"] == 1500.0
    assert d["is_active"] is True
    assert d["evaluation_window_seconds"] == 120
    assert d["consecutive_breaches_required"] == 3


def test_system_incident_model():
    incident = SystemIncident(
        workspace_id="ws-alpha",
        service_name="dnk_vector_db",
        severity="CRITICAL",
        status="OPEN",
        title="High Memory Pressure",
        metric_name="memory_usage_pct",
        observed_value=94.2,
        threshold_value=90.0,
    )
    d = incident.to_dict()
    assert d["id"].startswith("inc_")
    assert d["severity"] == "CRITICAL"
    assert d["status"] == "OPEN"
    assert d["observed_value"] == 94.2
    assert d["threshold_value"] == 90.0
    assert d["service_name"] == "dnk_vector_db"


def test_remediation_action_model():
    action = RemediationAction(
        workspace_id="ws-alpha",
        incident_id="inc_12345",
        service_name="dnk_vector_db",
        action_type="clear_cache",
        status="PENDING",
        parameters={"cache_tier": "l2_redis", "force": True},
    )
    d = action.to_dict()
    assert d["id"].startswith("act_")
    assert d["action_type"] == "clear_cache"
    assert d["status"] == "PENDING"
    assert d["parameters"]["force"] is True
    assert d["service_name"] == "dnk_vector_db"


def test_auto_healing_policy_model():
    policy = AutoHealingPolicy(
        workspace_id="ws-alpha",
        service_name="dnk_a2a_mesh",
        incident_type="consecutive_probe_failures",
        remediation_playbook="restart_service",
        max_retries=2,
        cooldown_seconds=180,
    )
    d = policy.to_dict()
    assert d["id"].startswith("ahp_")
    assert d["incident_type"] == "consecutive_probe_failures"
    assert d["remediation_playbook"] == "restart_service"
    assert d["max_retries"] == 2
    assert d["cooldown_seconds"] == 180
    assert d["is_enabled"] is True


def test_service_health_snapshot_model():
    snapshot = ServiceHealthSnapshot(
        workspace_id="ws-alpha",
        service_name="dnk_auth_service",
        status="HEALTHY",
        cpu_usage_pct=24.5,
        memory_usage_pct=42.1,
        p95_latency_ms=85.0,
        active_incidents_count=0.0,
    )
    d = snapshot.to_dict()
    assert d["id"].startswith("shs_")
    assert d["status"] == "HEALTHY"
    assert d["cpu_usage_pct"] == 24.5
    assert d["memory_usage_pct"] == 42.1
    assert d["p95_latency_ms"] == 85.0


def test_alert_notification_log_model():
    log = AlertNotificationLog(
        workspace_id="ws-alpha",
        incident_id="inc_12345",
        channel="telegram",
        recipient="devops-alerts",
        status="SENT",
        payload={"alert": "Memory spike on dnk_vector_db"},
    )
    d = log.to_dict()
    assert d["id"].startswith("anl_")
    assert d["channel"] == "telegram"
    assert d["status"] == "SENT"
    assert d["recipient"] == "devops-alerts"
    assert "alert" in d["payload"]
