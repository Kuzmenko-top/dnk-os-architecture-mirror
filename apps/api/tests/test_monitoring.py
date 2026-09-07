# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_tests_test_monitoring"
# purpose: "Comprehensive Pytest Suite for Health Checks, Prometheus Metrics & Alerting"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

import asyncio
import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.api.monitoring.alerts import (
    BaseAlertChannel as AlertChannel,
    AlertDispatchResult,
    AlertManager,
    AlertNotification,
    AlertSeverity,
    EmailAlertChannel,
    SlackAlertChannel,
)
from apps.api.monitoring.health_check import (
    ComponentHealth,
    HealthCheckRegistry as HealthRegistry,
    HealthStatus,
    SystemHealthReport,
)
from apps.api.monitoring.metrics import (
    CONTENT_TYPE_LATEST,
    MetricsRegistry,
)
from apps.api.routers.health import router as health_router


# ===========================================================================
# 1. HealthRegistry Unit Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_health_registry_liveness():
    registry = HealthRegistry(service_version="1.0.0")
    liveness = await registry.check_liveness()
    assert liveness["status"] == "healthy"
    assert liveness["version"] == "1.0.0"
    assert "uptime_seconds" in liveness


@pytest.mark.asyncio
async def test_health_registry_readiness_healthy():
    registry = HealthRegistry()
    report = await registry.check_readiness()
    assert isinstance(report, SystemHealthReport)
    assert report.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
    assert report.uptime_seconds >= 0


@pytest.mark.asyncio
async def test_health_registry_custom_probes():
    registry = HealthRegistry()

    async def healthy_probe() -> ComponentHealth:
        return ComponentHealth(
            name="custom_service",
            status=HealthStatus.HEALTHY,
            response_time_ms=5.0,
            details={"ping": "pong"},
        )

    async def failing_probe() -> ComponentHealth:
        return ComponentHealth(
            name="faulty_service",
            status=HealthStatus.UNHEALTHY,
            response_time_ms=10.0,
            error="Connection refused",
        )

    registry.register("custom_service", healthy_probe)
    registry.register("faulty_service", failing_probe)

    report = await registry.check_all()
    assert "custom_service" in report.components
    assert report.components["custom_service"].status == HealthStatus.HEALTHY
    assert "faulty_service" in report.components
    assert report.components["faulty_service"].status == HealthStatus.UNHEALTHY
    assert report.status == HealthStatus.UNHEALTHY


# ===========================================================================
# 2. MetricsRegistry Unit Tests
# ===========================================================================

def test_metrics_registry_initialization():
    registry = MetricsRegistry()
    assert registry is not None


def test_metrics_registry_record_request():
    registry = MetricsRegistry()
    registry.record_request(
        method="GET",
        endpoint="/health/live",
        status_code=200,
        duration_seconds=0.015,
    )
    # Check that export produces valid prometheus exposition bytes
    output = registry.export_metrics()
    assert isinstance(output, bytes)
    text = output.decode("utf-8")
    assert "dnk_http_requests_total" in text


def test_metrics_registry_record_task_and_alert():
    registry = MetricsRegistry()
    registry.record_swarm_task(agent="gerych_builder", status="completed")
    registry.record_alert_dispatched(severity="warning", channel="slack", success=True)
    output = registry.export_metrics()
    text = output.decode("utf-8")
    assert "dnk_swarm_completed_tasks_total" in text or "dnk_alerts_dispatched_total" in text


# ===========================================================================
# 3. AlertManager & Channels Unit Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_slack_channel_mock_send(monkeypatch):
    channel = SlackAlertChannel(webhook_url="https://hooks.slack.com.example/services/REDACTED_MOCK_WEBHOOK")
    
    # Mock httpx.AsyncClient.post to avoid real network calls
    class MockResponse:
        status_code = 200
        text = "ok"

    async def mock_post(self, url, json=None):
        return MockResponse()

    monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

    alert = AlertNotification(
        title="High Memory Usage",
        message="RAM utilization exceeded 90%",
        severity=AlertSeverity.WARNING,
        service="dnk_api",
        component="memory",
    )

    result = await channel.send(alert)
    assert result.success is True
    assert result.channel == "slack"
    assert result.error is None


@pytest.mark.asyncio
async def test_email_channel_mock_send(monkeypatch):
    channel = EmailAlertChannel(
        smtp_host="smtp.example.com",
        smtp_port=587,
        from_email="alerts@dnk.test",
        to_email="admin@dnk.test",
    )

    # Mock _sync_send_mail to avoid real SMTP
    def mock_send(alert):
        return AlertDispatchResult(channel="email", success=True, status_code=250)

    monkeypatch.setattr(channel, "_sync_send_mail", mock_send)

    alert = AlertNotification(
        title="Database Down",
        message="PostgreSQL replica is unreachable",
        severity=AlertSeverity.CRITICAL,
        service="dnk_db",
    )

    result = await channel.send(alert)
    assert result.success is True
    assert result.channel == "email"


@pytest.mark.asyncio
async def test_alert_manager_throttling():
    manager = AlertManager(throttle_cooldown_seconds=60)
    
    # Register mock channel
    class MockChannel(AlertChannel):
        name = "mock"
        call_count = 0
        async def send(self, alert: AlertNotification) -> AlertDispatchResult:
            self.call_count += 1
            return AlertDispatchResult(channel="mock", success=True)

    mock_chan = MockChannel()
    manager.register_channel("mock", mock_chan)

    alert = AlertNotification(
        title="Disk Warning",
        message="Disk space low",
        severity=AlertSeverity.WARNING,
        service="dnk_node",
    )

    # First dispatch - should succeed
    res1 = await manager.dispatch(alert, channels=["mock"])
    assert res1[0].success is True
    assert mock_chan.call_count == 1

    # Second immediate dispatch with identical alert - should be throttled
    res2 = await manager.dispatch(alert, channels=["mock"])
    assert res2[0].success is True
    assert "throttled" in (res2[0].error or "").lower()
    assert mock_chan.call_count == 1  # Not sent again

    # Critical alert with same title - should bypass throttling
    critical_alert = AlertNotification(
        title="Disk Warning",
        message="Disk full emergency",
        severity=AlertSeverity.CRITICAL,
        service="dnk_node",
    )
    res3 = await manager.dispatch(critical_alert, channels=["mock"])
    assert res3[0].success is True
    assert mock_chan.call_count == 2


# ===========================================================================
# 4. FastAPI Router End-to-End Tests
# ===========================================================================

def get_test_client() -> TestClient:
    app = FastAPI(title="DNK Monitoring Test")
    app.include_router(health_router)
    return TestClient(app)


def test_router_liveness_endpoint():
    client = get_test_client()
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_router_readiness_endpoint():
    client = get_test_client()
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "uptime_seconds" in data


def test_router_detailed_health_endpoint():
    client = get_test_client()
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "components" in data
    assert "system_metrics" in data


def test_router_metrics_endpoint():
    client = get_test_client()
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    assert len(response.text) > 0


def test_router_alert_channels_status():
    client = get_test_client()
    response = client.get("/api/v1/alerts/channels")
    assert response.status_code == 200
    data = response.json()
    assert "channels" in data
    assert "cooldown_seconds" in data
