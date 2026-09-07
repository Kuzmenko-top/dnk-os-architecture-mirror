# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-HEALTH-001-ROUTER-PHASE4"
# purpose: "Integration tests for Health Monitoring & Auto-Healing REST Router (DNK-HEALTH-001 Phase 4)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_health_metric_ingest_and_summary():
    # Ingest metrics
    response = client.post(
        "/api/v1/health/metrics/ingest",
        json={
            "workspace_id": "ws-health-001",
            "service_name": "api-gateway",
            "metric_name": "cpu_usage_pct",
            "value": 45.5,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "ingested"
    assert data["service_name"] == "api-gateway"
    assert data["value"] == 45.5

    # Get summary
    res_summary = client.get(
        "/api/v1/health/metrics/summary",
        params={
            "workspace_id": "ws-health-001",
            "service_name": "api-gateway",
            "metric_name": "cpu_usage_pct",
            "window_s": 300,
        },
    )
    assert res_summary.status_code == 200
    sum_data = res_summary.json()
    assert sum_data["workspace_id"] == "ws-health-001"
    assert sum_data["summary"]["count"] >= 1


def test_health_rule_and_incident_lifecycle():
    # 1. Create rule
    res_rule = client.post(
        "/api/v1/health/rules",
        json={
            "workspace_id": "ws-health-002",
            "service_name": "auth-service",
            "metric_name": "error_rate_pct",
            "comparator": ">",
            "threshold": 10.0,
            "severity": "CRITICAL",
            "duration_seconds": 0,
            "description": "Auth error rate spike",
        },
    )
    assert res_rule.status_code == 201
    rule_data = res_rule.json()
    assert rule_data["status"] == "registered"

    # List rules
    res_rules_list = client.get("/api/v1/health/rules", params={"workspace_id": "ws-health-002"})
    assert res_rules_list.status_code == 200
    assert len(res_rules_list.json()["rules"]) >= 1

    # Ingest metric breaching threshold (15 > 10) 3 times to trigger incident
    for _ in range(3):
        res_ingest = client.post(
            "/api/v1/health/metrics/ingest",
            json={
                "workspace_id": "ws-health-002",
                "service_name": "auth-service",
                "metric_name": "error_rate_pct",
                "value": 15.0,
            },
        )
        assert res_ingest.status_code == 201

    # List incidents
    res_incidents = client.get("/api/v1/health/incidents", params={"workspace_id": "ws-health-002"})
    assert res_incidents.status_code == 200
    inc_list = res_incidents.json()["incidents"]
    assert len(inc_list) >= 1
    incident_id = inc_list[0]["id"]

    # Resolve incident
    res_resolve = client.post(
        f"/api/v1/health/incidents/{incident_id}/resolve",
        json={"resolution_note": "Issue resolved by ops"},
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] == "resolved"


def test_auto_healing_policy_and_remediation():
    # 1. Create policy
    res_policy = client.post(
        "/api/v1/health/policies",
        json={
            "workspace_id": "ws-health-003",
            "service_name": "order-service",
            "incident_type": "HIGH",
            "remediation_playbook": "RESTART_SERVICE",
            "max_retries": 3,
            "cooldown_seconds": 60,
            "flap_detection_window_s": 300,
        },
    )
    assert res_policy.status_code == 201
    assert res_policy.json()["status"] == "created"

    # List policies
    res_pol_list = client.get("/api/v1/health/policies", params={"workspace_id": "ws-health-003"})
    assert res_pol_list.status_code == 200
    assert len(res_pol_list.json()["policies"]) >= 1

    # Create rule and trigger incident for order-service
    client.post(
        "/api/v1/health/rules",
        json={
            "workspace_id": "ws-health-003",
            "service_name": "order-service",
            "metric_name": "latency_ms",
            "comparator": ">",
            "threshold": 500.0,
            "severity": "HIGH",
            "duration_seconds": 0,
        },
    )
    for _ in range(3):
        client.post(
            "/api/v1/health/metrics/ingest",
            json={
                "workspace_id": "ws-health-003",
                "service_name": "order-service",
                "metric_name": "latency_ms",
                "value": 850.0,
            },
        )

    res_inc = client.get("/api/v1/health/incidents", params={"workspace_id": "ws-health-003"})
    incidents = res_inc.json()["incidents"]
    assert len(incidents) >= 1
    inc_id = incidents[0]["id"]

    # Remediate incident
    res_rem = client.post(f"/api/v1/health/remediate/{inc_id}")
    assert res_rem.status_code == 200
    assert res_rem.json()["status"] == "SUCCEEDED"

    # List remediations
    res_hist = client.get("/api/v1/health/remediations", params={"workspace_id": "ws-health-003"})
    assert res_hist.status_code == 200
    assert len(res_hist.json()["actions"]) >= 1


def test_alert_dispatch_and_audit_logs():
    # Create rule and trigger incident
    client.post(
        "/api/v1/health/rules",
        json={
            "workspace_id": "ws-health-004",
            "service_name": "payment-service",
            "metric_name": "failure_rate_pct",
            "comparator": ">",
            "threshold": 5.0,
            "severity": "CRITICAL",
            "duration_seconds": 0,
        },
    )
    for _ in range(3):
        client.post(
            "/api/v1/health/metrics/ingest",
            json={
                "workspace_id": "ws-health-004",
                "service_name": "payment-service",
                "metric_name": "failure_rate_pct",
                "value": 12.0,
            },
        )

    res_inc = client.get("/api/v1/health/incidents", params={"workspace_id": "ws-health-004"})
    incidents = res_inc.json()["incidents"]
    assert len(incidents) >= 1
    inc_id = incidents[0]["id"]

    # Dispatch alert
    res_alert = client.post(
        "/api/v1/health/alerts/dispatch",
        json={
            "incident_id": inc_id,
            "channel": "TELEGRAM",
            "target": "@dnk_security_ops",
            "force": True,
        },
    )
    assert res_alert.status_code == 201
    assert res_alert.json()["status"] in ["SENT", "DELIVERED"]

    # Check alert audit logs
    res_logs = client.get("/api/v1/health/alerts/logs", params={"workspace_id": "ws-health-004"})
    assert res_logs.status_code == 200
    assert len(res_logs.json()["logs"]) >= 1
