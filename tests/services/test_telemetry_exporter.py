# --- DNK-MRH-HEADER ---
# mrh_id: "tests_services_test_telemetry_exporter"
# purpose: "Comprehensive unit and integration test suite for Gemini telemetry exporter, Prometheus exposition, and Visual Shell dashboard JSON."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from services.dnk_analytics.drift_monitor import (
    GeminiDriftMonitor,
    DriftMetricKind,
    AlarmSeverity,
    DriftAlarm,
    DriftReport,
    WindowSummary,
)
from services.dnk_analytics.telemetry_exporter import (
    GeminiTelemetryExporter,
    gemini_telemetry_exporter,
)
from core.orchestrator.gemini_self_heal import (
    GeminiSelfHealer,
    HealExecutionResult,
)
from apps.api.monitoring.metrics import metrics_registry
from apps.api.main import app


def test_prometheus_exposition_format():
    """Verifies that export_prometheus_text produces valid Prometheus exposition format with all metrics."""
    monitor = GeminiDriftMonitor()
    for _ in range(5):
        monitor.update_baseline_online('{"status": "ok", "message": "Standard Baseline Response Payload"}')
        monitor.record_response('{"status": "ok", "message": "Standard Baseline Response Payload"}')

    exporter = GeminiTelemetryExporter(monitor=monitor, model_name="gemini-2.5-pro")
    prom_text = exporter.export_prometheus_text()

    assert isinstance(prom_text, str)
    assert "# HELP dnk_gemini_entropy_mean" in prom_text
    assert "# TYPE dnk_gemini_entropy_mean gauge" in prom_text
    assert 'dnk_gemini_entropy_mean{model="gemini-2.5-pro"}' in prom_text

    assert "# HELP dnk_gemini_char_length_mean" in prom_text
    assert "# TYPE dnk_gemini_char_length_mean gauge" in prom_text

    assert "# HELP dnk_gemini_json_valid_ratio" in prom_text
    assert 'dnk_gemini_json_valid_ratio{model="gemini-2.5-pro"} 1.0000' in prom_text

    assert "# HELP dnk_gemini_is_healthy" in prom_text
    assert 'dnk_gemini_is_healthy{model="gemini-2.5-pro"} 1.0' in prom_text

    assert "# HELP dnk_gemini_samples_total" in prom_text
    assert "# TYPE dnk_gemini_samples_total counter" in prom_text
    assert 'dnk_gemini_samples_total{model="gemini-2.5-pro"} 5' in prom_text


def test_visual_shell_telemetry_json():
    """Verifies that export_visual_shell_telemetry returns valid JSON-serializable dashboard payload."""
    monitor = GeminiDriftMonitor()
    for i in range(5):
        monitor.record_response(f'{{"index": {i}, "data": "visual shell test data"}}')

    exporter = GeminiTelemetryExporter(monitor=monitor, model_name="gemini-flash")
    data = exporter.export_visual_shell_telemetry()

    assert isinstance(data, dict)
    assert data["status"] in ("HEALTHY", "WARNING", "CRITICAL")
    assert data["model_name"] == "gemini-flash"
    assert "timestamp" in data
    assert "summary" in data
    assert data["summary"]["total_samples"] == 5

    assert "metrics" in data
    assert "entropy" in data["metrics"]
    assert "char_len" in data["metrics"]
    assert "ttr" in data["metrics"]
    assert "json_valid_ratio" in data["metrics"]

    assert "welford_online" in data
    assert "active_alarms" in data
    assert "healing" in data

    # Verify JSON serializability
    json_str = json.dumps(data)
    assert len(json_str) > 0


def test_drift_alarm_recording_in_telemetry():
    """Verifies that drift alarms are properly tracked in counters and active gauges."""
    monitor = GeminiDriftMonitor()
    exporter = GeminiTelemetryExporter(monitor=monitor)

    dummy_alarm = DriftAlarm(
        metric=DriftMetricKind.ENTROPY_COLLAPSE,
        severity=AlarmSeverity.CRITICAL,
        current_value=1.5,
        baseline_value=4.0,
        delta_or_z=-3.5,
        message="Simulated entropy collapse detected",
    )
    dummy_summary = WindowSummary(
        sample_count=3,
        mean_char_len=50.0,
        stdev_char_len=2.0,
        mean_word_count=10.0,
        mean_entropy=1.5,
        stdev_entropy=0.1,
        mean_ttr=0.3,
        json_valid_rate=1.0,
    )
    report = DriftReport(
        is_healthy=False,
        alarms=[dummy_alarm],
        baseline=dummy_summary,
        current_window=dummy_summary,
    )

    exporter.record_drift_report(report)
    prom_text = exporter.export_prometheus_text()

    assert 'dnk_gemini_is_healthy{model="gemini-2.5-pro"} 0.0' in prom_text
    assert 'dnk_gemini_drift_alarm_active{model="gemini-2.5-pro",alarm_type="entropy_collapse"} 1.0' in prom_text
    assert 'dnk_gemini_drift_alarms_total{model="gemini-2.5-pro",alarm_type="entropy_collapse",severity="CRITICAL"} 1' in prom_text

    telemetry = exporter.export_visual_shell_telemetry()
    assert telemetry["status"] == "CRITICAL"
    assert telemetry["is_healthy"] is False
    assert len(telemetry["active_alarms"]) == 1
    assert telemetry["active_alarms"][0]["metric"] == "entropy_collapse"


def test_healing_recording_in_telemetry():
    """Verifies that self-healing outcomes and retries are recorded in exporter."""
    exporter = GeminiTelemetryExporter()
    heal_result = HealExecutionResult(
        success=True,
        final_output='{"recovered": true}',
        parsed_json={"recovered": True},
        total_attempts=2,
        healed=True,
        healing_actions=["temperature_dampening_0.3", "system_prompt_reinforcement"],
    )

    exporter.record_healing_result(heal_result)
    prom_text = exporter.export_prometheus_text()

    assert 'dnk_gemini_retries_total{model="gemini-2.5-pro"} 1' in prom_text
    assert 'dnk_gemini_self_healings_total{model="gemini-2.5-pro",strategy="temperature_dampening_0.3",status="success"} 1' in prom_text
    assert 'dnk_gemini_self_healings_total{model="gemini-2.5-pro",strategy="system_prompt_reinforcement",status="success"} 1' in prom_text

    telemetry = exporter.export_visual_shell_telemetry()
    assert telemetry["healing"]["total_healed"] == 1
    assert telemetry["healing"]["last_healed"] is True
    assert telemetry["healing"]["strategies_used"]["temperature_dampening_0.3"] == 1


def test_self_healer_auto_records_to_telemetry():
    """Verifies that GeminiSelfHealer automatically updates an attached GeminiTelemetryExporter."""
    monitor = GeminiDriftMonitor()
    exporter = GeminiTelemetryExporter(monitor=monitor)
    healer = GeminiSelfHealer(
        monitor=monitor,
        telemetry_exporter=exporter,
        max_retries=1,
    )

    # Calling execute_with_healing with valid output
    mock_llm = MagicMock(return_value='{"status": "ok", "payload": "healer auto telemetry test"}')
    result = healer.execute_with_healing(
        call_fn=mock_llm,
        initial_params={"prompt": "test prompt"},
        expect_json=True,
    )

    assert result.success is True
    assert exporter.last_healing_result is not None
    assert exporter.last_report is not None


def test_metrics_registry_includes_drift_exporter():
    """Verifies that MetricsRegistry exports drift metrics from registered exporters."""
    exporter = GeminiTelemetryExporter()
    metrics_registry.register_drift_exporter(exporter)

    raw_bytes = metrics_registry.export_metrics()
    text = raw_bytes.decode("utf-8")

    assert "dnk_gemini_entropy_mean" in text
    assert "dnk_gemini_is_healthy" in text


def test_api_workspace_analytics_drift_endpoints():
    """Verifies GET /api/v1/analytics/drift/telemetry and GET /api/v1/analytics/drift/metrics."""
    client = TestClient(app)

    # 1. Test telemetry JSON endpoint
    headers = {
        "x-tenant-id": "tenant-test",
        "x-workspace-id": "ws-alpha-001",
    }
    resp_telemetry = client.get("/api/v1/analytics/drift/telemetry", headers=headers)
    assert resp_telemetry.status_code == 200
    telemetry_json = resp_telemetry.json()
    assert "status" in telemetry_json
    assert "metrics" in telemetry_json

    # 2. Test Prometheus text metrics endpoint
    resp_metrics = client.get("/api/v1/analytics/drift/metrics")
    assert resp_metrics.status_code == 200
    assert "dnk_gemini_" in resp_metrics.text

    # 3. Test global /metrics endpoint
    resp_global = client.get("/metrics")
    assert resp_global.status_code == 200
    assert "dnk_gemini_is_healthy" in resp_global.text
