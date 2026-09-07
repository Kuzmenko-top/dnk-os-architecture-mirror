# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_alert_channel_dispatcher"
# purpose: "Unit & API Integration Tests for Multi-Channel Alert Dispatcher (DNK-ANALYTICS-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.services.alert_channel_dispatcher import (
    TelegramChannelAdapter,
    SlackChannelAdapter,
    PagerDutyChannelAdapter,
    EmailChannelAdapter,
    AlertChannelDispatcher,
)

client = TestClient(app)


def test_telegram_channel_adapter():
    alert = {
        "rule_name": "Database High Latency",
        "severity": "critical",
        "workspace_id": "ws-tg-001",
        "triggered_at": "2026-08-28T12:00:00Z",
        "details": "p95 latency reached 850ms",
    }

    # Missing config failure
    res_failed = TelegramChannelAdapter.dispatch({}, alert)
    assert res_failed["status"] == "failed"

    # Valid config
    config = {"webhook_url": "https://api.telegram.org/bot123/sendMessage", "chat_id": "999888"}
    res_sent = TelegramChannelAdapter.dispatch(config, alert)
    assert res_sent["status"] == "sent"
    assert res_sent["channel"] == "telegram"


def test_slack_channel_adapter():
    alert = {
        "rule_name": "API Error Spike",
        "severity": "warning",
        "workspace_id": "ws-slack-001",
    }

    res_failed = SlackChannelAdapter.dispatch({}, alert)
    assert res_failed["status"] == "failed"

    config = {"webhook_url": "https://hooks.slack.com.example/services/REDACTED_MOCK_WEBHOOK"}
    res_sent = SlackChannelAdapter.dispatch(config, alert)
    assert res_sent["status"] == "sent"
    assert res_sent["channel"] == "slack"


def test_pagerduty_channel_adapter():
    alert = {
        "rule_name": "Service Outage",
        "severity": "critical",
    }

    config = {"routing_key": "pd-integration-key-123"}
    res_sent = PagerDutyChannelAdapter.dispatch(config, alert)
    assert res_sent["status"] == "sent"
    assert res_sent["channel"] == "pagerduty"


def test_email_channel_adapter():
    alert = {
        "rule_name": "Daily Summary Anomaly",
        "severity": "info",
    }

    config = {"recipients": ["ops@dnk-e.com", "devs@dnk-e.com"]}
    res_sent = EmailChannelAdapter.dispatch(config, alert)
    assert res_sent["status"] == "sent"
    assert res_sent["recipients"] == 2


def test_alert_channel_dispatcher_multi_channel():
    dispatcher = AlertChannelDispatcher()
    alert = {
        "rule_name": "Multi Channel Test Alert",
        "severity": "warning",
        "workspace_id": "ws-multi-001",
    }

    channels_config = [
        {
            "channel_type": "telegram",
            "enabled": True,
            "channel_config": {"webhook_url": "https://telegram.org/hook", "chat_id": "1234"},
        },
        {
            "channel_type": "slack",
            "enabled": True,
            "channel_config": {"webhook_url": "https://slack.com/hook"},
        },
        {
            "channel_type": "email",
            "enabled": False,  # Disabled channel should be skipped
            "channel_config": {"recipients": ["test@dnk-e.com"]},
        },
    ]

    res = dispatcher.dispatch_alert(alert, channels_config)
    assert "telegram" in res["delivered_channels"]
    assert "slack" in res["delivered_channels"]
    assert res["delivery_status"]["email"] == "skipped_disabled"


def test_alert_channels_api():
    workspace_id = "ws-channel-api-004"

    channel_payload = {
        "workspace_id": workspace_id,
        "channel_type": "telegram",
        "channel_config": {"webhook_url": "https://telegram.org/hook", "chat_id": "112233"},
        "enabled": True,
    }

    # Create channel
    create_res = client.post("/api/v1/alerts/channels", json=channel_payload)
    assert create_res.status_code == 200
    ch_data = create_res.json()
    assert ch_data["channel_type"] == "telegram"
    channel_id = ch_data["id"]

    # List channels
    list_res = client.get(f"/api/v1/alerts/channels?workspace_id={workspace_id}")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Test channel delivery
    test_res = client.post(f"/api/v1/alerts/channels/{channel_id}/test")
    assert test_res.status_code == 200
    assert test_res.json()["status"] == "test_completed"

    # Delete channel
    del_res = client.delete(f"/api/v1/alerts/channels/{channel_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"
