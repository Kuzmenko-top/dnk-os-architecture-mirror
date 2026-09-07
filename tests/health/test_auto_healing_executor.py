# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-HEALTH-001-AUTO-HEALING-PHASE3"
# purpose: "Unit tests for AutoHealingExecutor & AlertDispatcherService (DNK-HEALTH-001 Phase 3)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.db.models.auto_healing_policy import AutoHealingPolicy
from apps.api.db.models.system_incident import SystemIncident
from apps.api.services.alert_dispatcher_service import AlertDispatcherService
from apps.api.services.auto_healing_executor import AutoHealingExecutor


def test_auto_healing_policy_execution():
    executor = AutoHealingExecutor()
    ws = "ws-prod"
    svc = "dnk_search_engine"

    policy = AutoHealingPolicy(
        workspace_id=ws,
        service_name=svc,
        incident_type="CRITICAL",
        remediation_playbook="restart_service",
        cooldown_seconds=30,
        max_retries=2,
    )
    pol_id = executor.register_policy(policy)
    assert pol_id is not None
    assert len(executor.list_policies(workspace_id=ws)) == 1

    incident = SystemIncident(
        id="inc_001",
        workspace_id=ws,
        service_name=svc,
        severity="CRITICAL",
        status="OPEN",
        title="High error rate breach",
        metric_name="error_rate_pct",
        observed_value=12.5,
    )

    action = executor.evaluate_and_execute(incident)
    assert action.status == "SUCCEEDED"
    assert action.action_type == "restart_service"
    assert action.execution_time_ms is not None
    assert action.execution_result["handler_result"]["restarted"] is True


def test_auto_healing_cooldown_and_flap_safety():
    executor = AutoHealingExecutor()
    ws = "ws-prod"
    svc = "dnk_worker"

    policy = AutoHealingPolicy(
        workspace_id=ws,
        service_name=svc,
        incident_type="CRITICAL",
        remediation_playbook="clear_cache",
        cooldown_seconds=60,
        max_retries=3,
    )
    executor.register_policy(policy)

    incident = SystemIncident(
        id="inc_002",
        workspace_id=ws,
        service_name=svc,
        severity="CRITICAL",
        status="OPEN",
        title="OOM threshold breach",
        metric_name="memory_usage_mb",
        observed_value=2048.0,
    )

    # 1st run -> Succeeded
    act1 = executor.evaluate_and_execute(incident)
    assert act1.status == "SUCCEEDED"

    # 2nd run immediately -> Suppressed due to cooldown
    act2 = executor.evaluate_and_execute(incident)
    assert act2.status == "SKIPPED"
    assert "in cooldown" in act2.execution_result.get("reason", "")

    # Flapping safety test
    flapping_incident = SystemIncident(
        id="inc_003",
        workspace_id=ws,
        service_name=svc,
        severity="CRITICAL",
        status="FLAPPING",
        title="Flapping service",
        metric_name="cpu_usage_pct",
        observed_value=99.0,
    )
    act3 = executor.evaluate_and_execute(flapping_incident)
    assert act3.status == "SKIPPED"
    assert "FLAPPING" in act3.execution_result.get("reason", "")


def test_alert_dispatcher_service():
    dispatcher = AlertDispatcherService(default_cooldown_seconds=60)
    ws = "ws-prod"
    svc = "dnk_database"

    incident = SystemIncident(
        id="inc_db_001",
        workspace_id=ws,
        service_name=svc,
        severity="CRITICAL",
        status="OPEN",
        title="DB replication lag breach",
        metric_name="replication_lag_s",
        observed_value=45.0,
    )

    # First dispatch -> SENT
    log1 = dispatcher.dispatch_alert(incident, channel="SLACK", target="#sre-room")
    assert log1.status == "SENT"
    assert log1.channel == "SLACK"

    # Immediate second dispatch -> SUPPRESSED by rate limiting
    log2 = dispatcher.dispatch_alert(incident, channel="SLACK", target="#sre-room")
    assert log2.status == "SUPPRESSED"

    # Forced dispatch -> SENT
    log3 = dispatcher.dispatch_alert(incident, channel="TELEGRAM", target="@dnk_ops", force=True)
    assert log3.status == "SENT"
    assert log3.channel == "TELEGRAM"

    # Query logs
    logs = dispatcher.get_logs(workspace_id=ws)
    assert len(logs) == 3
