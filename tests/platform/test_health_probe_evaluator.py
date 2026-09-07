# --- DNK-MRH-HEADER ---
# mrh_id: "tests_platform_test_health_probe_evaluator"
# purpose: "Unit Tests for Health Probes & SLO Watchdog Evaluator (DNK-PLATFORM-SCALE-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.health_probe_evaluator import (
    HealthProbeEvaluator,
    SLOMetricSnapshot,
)


def test_probe_evaluation_healthy():
    evaluator = HealthProbeEvaluator(failure_threshold=3)
    res = evaluator.evaluate_probe_response(
        probe_type="liveness",
        target_environment="green",
        endpoint_path="/health/live",
        status_code=200,
        response_time_ms=45.0,
    )
    assert res.is_healthy is True
    assert res.status_code == 200
    assert evaluator.is_probe_failing_threshold("green", "liveness", "/health/live") is False


def test_probe_evaluation_failure_streak_threshold():
    evaluator = HealthProbeEvaluator(failure_threshold=3)

    # 1st failure (500)
    res1 = evaluator.evaluate_probe_response(
        probe_type="readiness",
        target_environment="green",
        endpoint_path="/health/ready",
        status_code=503,
        response_time_ms=10.0,
    )
    assert res1.is_healthy is False
    assert evaluator.is_probe_failing_threshold("green", "readiness", "/health/ready") is False

    # 2nd failure
    evaluator.evaluate_probe_response(
        probe_type="readiness",
        target_environment="green",
        endpoint_path="/health/ready",
        status_code=500,
        response_time_ms=15.0,
    )
    assert evaluator.is_probe_failing_threshold("green", "readiness", "/health/ready") is False

    # 3rd failure (exceeds threshold)
    evaluator.evaluate_probe_response(
        probe_type="readiness",
        target_environment="green",
        endpoint_path="/health/ready",
        status_code=500,
        response_time_ms=12.0,
    )
    assert evaluator.is_probe_failing_threshold("green", "readiness", "/health/ready") is True

    # Recovery resets failure streak
    evaluator.evaluate_probe_response(
        probe_type="readiness",
        target_environment="green",
        endpoint_path="/health/ready",
        status_code=200,
        response_time_ms=8.0,
    )
    assert evaluator.is_probe_failing_threshold("green", "readiness", "/health/ready") is False


def test_probe_evaluation_timeout():
    evaluator = HealthProbeEvaluator()
    res = evaluator.evaluate_probe_response(
        probe_type="slo",
        target_environment="green",
        endpoint_path="/api/v1/ping",
        status_code=200,
        response_time_ms=6000.0,
        timeout_seconds=5.0,
    )
    assert res.is_healthy is False
    assert res.error_message is not None and "timed out" in res.error_message


def test_slo_compliance_evaluation_healthy():
    evaluator = HealthProbeEvaluator(
        slo_latency_p95_max_ms=200.0,
        slo_latency_p99_max_ms=500.0,
        slo_error_rate_threshold=0.01,
        slo_saturation_max=80.0,
    )

    snapshot = SLOMetricSnapshot(
        environment="green",
        latency_p50_ms=25.0,
        latency_p95_ms=120.0,
        latency_p99_ms=250.0,
        error_rate=0.002,  # 0.2%
        request_count=5000,
        saturation_percentage=45.0,
    )

    slo_res = evaluator.evaluate_slo_compliance(snapshot)
    assert slo_res.is_compliant is True
    assert len(slo_res.violations) == 0
    assert slo_res.score == 1.0


def test_slo_compliance_evaluation_violations():
    evaluator = HealthProbeEvaluator(
        slo_latency_p95_max_ms=200.0,
        slo_latency_p99_max_ms=500.0,
        slo_error_rate_threshold=0.01,
        slo_saturation_max=80.0,
    )

    snapshot = SLOMetricSnapshot(
        environment="green",
        latency_p50_ms=150.0,
        latency_p95_ms=350.0,  # breach
        latency_p99_ms=650.0,  # breach
        error_rate=0.025,      # 2.5% breach
        request_count=1000,
        saturation_percentage=92.0,  # breach
    )

    slo_res = evaluator.evaluate_slo_compliance(snapshot)
    assert slo_res.is_compliant is False
    assert len(slo_res.violations) == 4
    assert slo_res.latency_p95_ok is False
    assert slo_res.latency_p99_ok is False
    assert slo_res.error_rate_ok is False
    assert slo_res.saturation_ok is False
    assert slo_res.score == 0.0
