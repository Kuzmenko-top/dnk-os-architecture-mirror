# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_advanced_alerting"
# purpose: "Unit & API Integration Tests for Advanced Composite Alerting Engine (DNK-ANALYTICS-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import time
import pytest
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.services.advanced_alerting_engine import (
    CompositeRuleEvaluator,
    AlertDeduplicator,
    AdvancedAlertingEngine,
)

client = TestClient(app)


def test_composite_rule_evaluator_single_and_nested():
    metrics = {
        "error_rate": 0.08,
        "latency_p95": 600.0,
        "queue_depth": 50,
    }

    # Single condition GT
    cond_gt = {"metric": "error_rate", "operator": "gt", "value": 0.05}
    assert CompositeRuleEvaluator.evaluate_condition(cond_gt, metrics) is True

    # Composite AND
    rule_and = {
        "and": [
            {"metric": "error_rate", "operator": "gt", "value": 0.05},
            {"metric": "latency_p95", "operator": "gt", "value": 500},
        ]
    }
    assert CompositeRuleEvaluator.evaluate_composite_logic(rule_and, metrics) is True

    # Composite OR (one true, one false)
    rule_or = {
        "or": [
            {"metric": "error_rate", "operator": "gt", "value": 0.50},  # False
            {"metric": "latency_p95", "operator": "gt", "value": 500},  # True
        ]
    }
    assert CompositeRuleEvaluator.evaluate_composite_logic(rule_or, metrics) is True


def test_alert_deduplication_cooldown():
    dedup = AlertDeduplicator()
    rule_id = "rule-dedup-001"

    assert dedup.is_in_cooldown(rule_id, cooldown_seconds=60) is False
    dedup.record_trigger(rule_id)
    assert dedup.is_in_cooldown(rule_id, cooldown_seconds=60) is True

    dedup.reset_rule(rule_id)
    assert dedup.is_in_cooldown(rule_id, cooldown_seconds=60) is False


def test_advanced_alerting_engine_evaluation():
    engine = AdvancedAlertingEngine()
    rule_id = "rule-engine-001"
    logic = {
        "and": [
            {"metric": "error_rate", "operator": "gte", "value": 0.05},
        ]
    }
    metrics = {"error_rate": 0.10}

    # First trigger: triggered=True, suppressed=False
    trig1, supp1 = engine.evaluate_rule(rule_id, logic, metrics, cooldown_seconds=300)
    assert trig1 is True
    assert supp1 is False

    # Immediate second trigger: triggered=True, suppressed=True (in cooldown)
    trig2, supp2 = engine.evaluate_rule(rule_id, logic, metrics, cooldown_seconds=300)
    assert trig2 is True
    assert supp2 is True


def test_grouping_alerts():
    alerts = [
        {"id": "a1", "workspace_id": "ws-1", "severity": "critical"},
        {"id": "a2", "workspace_id": "ws-1", "severity": "warning"},
        {"id": "a3", "workspace_id": "ws-2", "severity": "info"},
    ]

    by_ws = AdvancedAlertingEngine.group_alerts_by_workspace(alerts)
    assert len(by_ws["ws-1"]) == 2
    assert len(by_ws["ws-2"]) == 1

    by_sev = AdvancedAlertingEngine.group_alerts_by_severity(alerts)
    assert len(by_sev["critical"]) == 1
    assert len(by_sev["warning"]) == 1
    assert len(by_sev["info"]) == 1


def test_advanced_alert_rules_crud_api():
    workspace_id = "ws-alerting-004"

    rule_payload = {
        "workspace_id": workspace_id,
        "rule_name": "High Error Rate & Latency Alert",
        "composite_logic": {
            "and": [
                {"metric": "error_rate", "operator": "gt", "value": 0.05},
                {"metric": "latency_p95", "operator": "gt", "value": 500},
            ]
        },
        "severity": "critical",
        "cooldown_seconds": 300,
        "enabled": True,
    }

    # Create rule
    create_res = client.post("/api/v1/alerts/rules/advanced", json=rule_payload)
    assert create_res.status_code == 200
    rule_data = create_res.json()
    assert rule_data["rule_name"] == "High Error Rate & Latency Alert"
    rule_id = rule_data["id"]

    # List rules
    list_res = client.get(f"/api/v1/alerts/rules/advanced?workspace_id={workspace_id}")
    assert list_res.status_code == 200
    rules = list_res.json()
    assert len(rules) >= 1

    # Update rule
    up_res = client.put(f"/api/v1/alerts/rules/advanced/{rule_id}", json={"severity": "warning"})
    assert up_res.status_code == 200
    assert up_res.json()["severity"] == "warning"

    # Delete rule
    del_res = client.delete(f"/api/v1/alerts/rules/advanced/{rule_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"
