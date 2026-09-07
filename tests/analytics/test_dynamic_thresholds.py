# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_dynamic_thresholds"
# purpose: "Unit & API Integration Tests for Dynamic Threshold Auto-Tuning Engine (DNK-ANALYTICS-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.services.dynamic_threshold_calculator import DynamicThresholdCalculator

client = TestClient(app)


def test_percentile_calculation():
    data = [10.0, 20.0, 30.0, 40.0, 50.0]
    p10 = DynamicThresholdCalculator.calculate_percentile(data, 0.10)
    p50 = DynamicThresholdCalculator.calculate_percentile(data, 0.50)
    p90 = DynamicThresholdCalculator.calculate_percentile(data, 0.90)

    assert p10 == 14.0
    assert p50 == 30.0
    assert p90 == 46.0


def test_compute_thresholds():
    history = [10.0, 12.0, 11.0, 9.5, 10.5, 11.5, 10.0]
    res = DynamicThresholdCalculator.compute_thresholds(
        history_values=history,
        sensitivity=0.80,
        rolling_window_hours=24,
    )

    assert res["rolling_window_hours"] == 24
    assert res["mean_value"] > 0.0
    assert res["lower_bound"] <= res["mean_value"] <= res["upper_bound"]
    assert res["sample_size"] == len(history)


def test_auto_tune_sensitivity():
    # Stable data -> high sensitivity
    stable_history = [10.0, 10.1, 10.05, 9.95, 10.02, 10.08, 9.98, 10.01, 10.04, 9.99]
    high_sens = DynamicThresholdCalculator.auto_tune_sensitivity(stable_history)
    assert high_sens >= 0.85

    # High variability data -> lower sensitivity
    noisy_history = [10.0, 50.0, 2.0, 100.0, 5.0, 80.0, 1.0, 120.0, 15.0, 90.0]
    low_sens = DynamicThresholdCalculator.auto_tune_sensitivity(noisy_history)
    assert low_sens <= 0.70


def test_dynamic_thresholds_recalculate_api():
    workspace_id = "ws-thresholds-004"
    metric_type = "error_rate"
    history = [0.01, 0.02, 0.015, 0.012, 0.018, 0.022, 0.011]

    # Recalculate endpoint: query parameters for workspace_id and metric_type, JSON body array for historical_values
    res = client.post(
        f"/api/v1/anomaly-detection/thresholds/recalculate?workspace_id={workspace_id}&metric_type={metric_type}",
        json=history,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["metric_type"] == "error_rate"
    assert "mean_value" in data
    assert "upper_bound" in data

    # Get current thresholds
    get_res = client.get(f"/api/v1/anomaly-detection/thresholds?workspace_id={workspace_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert len(get_data) >= 1
    assert get_data[0]["metric_type"] == "error_rate"
