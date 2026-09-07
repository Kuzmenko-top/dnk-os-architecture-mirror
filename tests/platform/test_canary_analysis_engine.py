# --- DNK-MRH-HEADER ---
# mrh_id: "tests_platform_test_canary_analysis_engine"
# purpose: "Unit & Statistical Verification Tests for Canary Analysis Engine & Auto-Rollback (DNK-PLATFORM-SCALE-004)"
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
from apps.api.services.canary_analysis_engine import (
    CanaryAnalysisEngine,
    CanaryAnalysisInput,
)
from apps.api.services.auto_rollback_engine import AutoRollbackEngine
from apps.api.services.blue_green_deployment_manager import BlueGreenDeploymentManager
from apps.api.services.health_probe_evaluator import (
    HealthProbeEvaluator,
    SLOMetricSnapshot,
)


def test_mann_whitney_u_identical_distributions():
    engine = CanaryAnalysisEngine()
    sample_a = [10.0, 12.0, 11.0, 13.0, 10.5, 12.5, 11.5, 12.0, 10.8, 11.2]
    sample_b = [10.2, 11.8, 11.1, 12.9, 10.6, 12.4, 11.6, 12.1, 10.9, 11.3]

    stat, p_val = engine.mann_whitney_u_test(sample_a, sample_b)
    # p-value should be high (no significant difference)
    assert p_val > 0.5


def test_mann_whitney_u_significant_degradation():
    engine = CanaryAnalysisEngine()
    baseline_blue = [10.0, 12.0, 11.0, 13.0, 10.5, 12.5, 11.5, 12.0, 10.8, 11.2]
    candidate_green = [50.0, 55.0, 48.0, 60.0, 52.0, 58.0, 51.0, 62.0, 49.0, 53.0]

    stat, p_val = engine.mann_whitney_u_test(baseline_blue, candidate_green)
    # Clear significant difference (p < 0.01)
    assert p_val < 0.01


def test_canary_analysis_recommend_promote():
    engine = CanaryAnalysisEngine()
    analysis_input = CanaryAnalysisInput(
        deployment_id="dep-123",
        blue_metrics={
            "latency_samples": [20.0, 22.0, 21.0, 23.0, 20.5, 22.5, 21.5, 22.0, 20.8, 21.2],
            "p95_ms": 23.0,
            "error_rate": 0.001,
            "request_count": 2000,
        },
        green_metrics={
            "latency_samples": [20.1, 21.9, 21.2, 22.8, 20.6, 22.4, 21.4, 22.1, 20.9, 21.1],
            "p95_ms": 22.8,
            "error_rate": 0.001,
            "request_count": 500,
        },
        statistical_test="mann_whitney_u",
    )

    result = engine.analyze_canary(analysis_input)
    assert result.is_degraded is False
    assert result.recommendation == "promote"


def test_canary_analysis_recommend_rollback_on_error_spike():
    engine = CanaryAnalysisEngine()
    analysis_input = CanaryAnalysisInput(
        deployment_id="dep-123",
        blue_metrics={
            "latency_samples": [20.0] * 15,
            "p95_ms": 20.0,
            "error_rate": 0.001,
            "request_count": 2000,
        },
        green_metrics={
            "latency_samples": [22.0] * 15,
            "p95_ms": 22.0,
            "error_rate": 0.035,  # 3.5% error rate spike
            "request_count": 500,
        },
        statistical_test="mann_whitney_u",
        allowed_error_rate_delta=0.005,
    )

    result = engine.analyze_canary(analysis_input)
    assert result.is_degraded is True
    assert result.recommendation == "rollback"
    assert "error rate delta" in result.analysis_notes


def test_auto_rollback_engine_triggers_instant_rollback():
    manager = BlueGreenDeploymentManager(
        config_id="cfg-test-01",
        deployment_name="dnk-api",
        blue_service_name="dnk-api-blue",
        green_service_name="dnk-api-green",
        initial_image_tag="v1.0.0",
    )

    # 1. Deploy & Start Canary
    manager.trigger_deploy(image_tag="v1.1.0-bad")
    manager.start_canary()
    assert manager.environments["green"].traffic_percentage == 1

    # 2. Setup Watchdog
    evaluator = HealthProbeEvaluator(slo_error_rate_threshold=0.01)
    engine = CanaryAnalysisEngine()
    auto_rollback = AutoRollbackEngine(
        probe_evaluator=evaluator,
        canary_engine=engine,
        auto_rollback_enabled=True,
    )

    # 3. Candidate telemetry has severe error rate breach (5.0%)
    bad_snapshot = SLOMetricSnapshot(
        environment="green",
        latency_p50_ms=40.0,
        latency_p95_ms=180.0,
        latency_p99_ms=300.0,
        error_rate=0.05,  # 5%
        request_count=200,
        saturation_percentage=50.0,
    )

    decision = auto_rollback.evaluate_and_enforce(
        manager=manager,
        candidate_slo_snapshot=bad_snapshot,
    )

    assert decision.triggered is True
    assert decision.target_environment == "green"
    assert decision.rollback_status == "rollback_completed"
    # Verify manager rolled back to blue 100%
    assert manager.environments["blue"].traffic_percentage == 100
    assert manager.environments["green"].traffic_percentage == 0
    assert manager.canary_enabled is False
