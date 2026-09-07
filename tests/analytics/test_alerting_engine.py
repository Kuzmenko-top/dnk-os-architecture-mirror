# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_alerting_engine"
# purpose: "Unit and integration tests for Alerting Engine, Threshold Rules, Composite Logic, and Webhook Dispatcher"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import pytest
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.services.analytics_alerting_service import analytics_alerting_service
from apps.api.services.auth_service import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_alerting_state():
    analytics_alerting_service.clear()
    yield
    analytics_alerting_service.clear()


@pytest.mark.asyncio
async def test_threshold_alert_rule_evaluation():
    rule = await analytics_alerting_service.create_rule(
        workspace_id="ws_test",
        name="High Error Rate",
        metric_type="error_rate",
        operator="gt",
        threshold_value=0.05,
        severity="critical",
    )
    rule_id = rule["id"]

    # Below threshold -> no trigger
    ev_normal = await analytics_alerting_service.evaluate_and_trigger(
        rule_id=rule_id,
        current_value=0.02,
    )
    assert ev_normal is None

    # Above threshold -> triggers alert
    ev_alert = await analytics_alerting_service.evaluate_and_trigger(
        rule_id=rule_id,
        current_value=0.08,
    )
    assert ev_alert is not None
    assert ev_alert["rule_id"] == rule_id
    assert ev_alert["metric_value"] == 0.08
    assert ev_alert["severity"] == "critical"
    assert ev_alert["resolved_at"] is None


@pytest.mark.asyncio
async def test_composite_alert_logic_and_or():
    # Composite rule: (error_rate > 0.05 AND latency_p95 > 250)
    composite_and = await analytics_alerting_service.create_rule(
        workspace_id="ws_comp",
        name="Degraded System Perf",
        metric_type="error_rate",
        operator="gt",
        threshold_value=0.0,
        severity="warning",
        composite_logic={
            "and": [
                {"metric": "error_rate", "op": "gt", "val": 0.05},
                {"metric": "latency_p95", "op": "gt", "val": 250.0},
            ]
        },
    )
    rule_id = composite_and["id"]

    # Partial match (only latency high) -> False
    triggered_partial = await analytics_alerting_service.evaluate_and_trigger(
        rule_id=rule_id,
        current_value=0.02,
        metric_context={"error_rate": 0.02, "latency_p95": 300.0},
    )
    assert triggered_partial is None

    # Full match (both high) -> Triggered
    triggered_full = await analytics_alerting_service.evaluate_and_trigger(
        rule_id=rule_id,
        current_value=0.07,
        metric_context={"error_rate": 0.07, "latency_p95": 320.0},
    )
    assert triggered_full is not None
    assert triggered_full["rule_name"] == "Degraded System Perf"


@pytest.mark.asyncio
async def test_full_alerting_pipeline_and_audit_log():
    # Setup listener to simulate WebSocket stream
    received_stream = []

    async def listener(event):
        received_stream.append(event)

    analytics_alerting_service.add_listener(listener)

    rule = await analytics_alerting_service.create_rule(
        workspace_id="ws_stream_test",
        name="High Latency Alert",
        metric_type="latency_p95",
        operator="gte",
        threshold_value=200.0,
        severity="warning",
    )
    rule_id = rule["id"]

    # Trigger alert
    event = await analytics_alerting_service.evaluate_and_trigger(
        rule_id=rule_id,
        current_value=220.0,
    )
    assert event is not None
    assert len(received_stream) == 1
    assert received_stream[0]["rule_id"] == rule_id

    # Verify audit log retrieval
    logged_events = await analytics_alerting_service.list_events(workspace_id="ws_stream_test")
    assert len(logged_events) == 1
    assert logged_events[0]["id"] == event["id"]

    # Resolve event
    resolved = await analytics_alerting_service.resolve_event(
        event_id=event["id"],
        resolution_note="Autoscaled pods to mitigate latency",
    )
    assert resolved is not None
    assert resolved["resolved_at"] is not None
    assert resolved["resolution_note"] == "Autoscaled pods to mitigate latency"


@pytest.mark.asyncio
async def test_alert_webhook_dispatcher():
    rule = await analytics_alerting_service.create_rule(
        workspace_id="ws_webhook",
        name="Webhook Notification Rule",
        metric_type="resource_usage",
        operator="gt",
        threshold_value=90.0,
        webhook_url="https://mock.webhook.internal/alerts",
    )
    rule_id = rule["id"]

    event = await analytics_alerting_service.evaluate_and_trigger(
        rule_id=rule_id,
        current_value=95.0,
    )
    assert event is not None


def test_api_alert_rules_and_events_crud():
    token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_api_test",
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Create Rule via POST
    create_payload = {
        "workspace_id": "ws_api_test",
        "name": "API Inactivity Rule",
        "metric_type": "inactivity",
        "operator": "gt",
        "threshold_value": 3600.0,
        "window_seconds": 300,
        "severity": "info",
    }
    res = client.post("/api/v1/analytics/alerts/rules", json=create_payload, headers=headers)
    assert res.status_code == 201
    rule_data = res.json()
    rule_id = rule_data["id"]
    assert rule_data["name"] == "API Inactivity Rule"

    # List Rules via GET
    res_list = client.get("/api/v1/analytics/alerts/rules?workspace_id=ws_api_test", headers=headers)
    assert res_list.status_code == 200
    rules = res_list.json()["rules"]
    assert len(rules) >= 1

    # Update Rule via PUT
    update_payload = {"threshold_value": 7200.0, "severity": "warning"}
    res_update = client.put(f"/api/v1/analytics/alerts/rules/{rule_id}", json=update_payload, headers=headers)
    assert res_update.status_code == 200
    assert res_update.json()["threshold_value"] == 7200.0
    assert res_update.json()["severity"] == "warning"

    # Trigger metric evaluation to produce an event
    asyncio.run(
        analytics_alerting_service.evaluate_and_trigger(
            rule_id=rule_id,
            current_value=8000.0,
            force=True,
        )
    )

    # Get Events
    res_events = client.get("/api/v1/analytics/alerts/events?workspace_id=ws_api_test", headers=headers)
    assert res_events.status_code == 200
    events = res_events.json()["events"]
    assert len(events) == 1
    event_id = events[0]["id"]

    # Resolve Event via POST
    res_resolve = client.post(
        f"/api/v1/analytics/alerts/events/{event_id}/resolve",
        json={"resolution_note": "User restarted worker session"},
        headers=headers,
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["resolution_note"] == "User restarted worker session"

    # Delete Rule via DELETE
    res_delete = client.delete(f"/api/v1/analytics/alerts/rules/{rule_id}", headers=headers)
    assert res_delete.status_code == 200
    assert res_delete.json()["status"] == "deleted"
