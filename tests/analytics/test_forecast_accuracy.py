# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_forecast_accuracy"
# purpose: "Unit & Integration Tests for Forecast Accuracy Evaluation (MAE, RMSE, MAPE, R2 Score)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.forecast_accuracy_tracker import ForecastAccuracyTracker


def test_forecast_accuracy_perfect_match():
    tracker = ForecastAccuracyTracker()
    actuals = [10.0, 20.0, 30.0, 40.0]
    preds = [10.0, 20.0, 30.0, 40.0]

    metrics = tracker.calculate_metrics(actuals=actuals, predictions=preds)
    assert metrics["mae"] == 0.0
    assert metrics["rmse"] == 0.0
    assert metrics["mape"] == 0.0
    assert metrics["r2_score"] == 1.0


def test_forecast_accuracy_known_error():
    tracker = ForecastAccuracyTracker()
    actuals = [10.0, 20.0, 30.0, 40.0]
    preds = [12.0, 18.0, 32.0, 38.0]  # errors: +2, -2, +2, -2 -> abs: 2, sq: 4

    metrics = tracker.calculate_metrics(actuals=actuals, predictions=preds)
    assert metrics["mae"] == 2.0
    assert metrics["rmse"] == 2.0
    assert metrics["mape"] > 0.0
    assert metrics["r2_score"] > 0.90


def test_accuracy_tracking_and_history():
    tracker = ForecastAccuracyTracker()
    actuals = [15.0, 25.0, 35.0, 45.0, 55.0]
    preds = [14.0, 26.0, 33.0, 47.0, 54.0]

    res = tracker.record_and_evaluate(
        model_id="mod-linear-001",
        model_name="linear",
        actuals=actuals,
        predictions=preds,
        evaluation_window_hours=24,
    )

    assert res["model_id"] == "mod-linear-001"
    assert res["mae"] > 0.0
    assert res["rmse"] > 0.0
    assert "evaluation_time" in res
    assert res["evaluation_window_hours"] == 24

    history = tracker.get_accuracy_history(model_id="mod-linear-001")
    assert len(history) == 1
    assert history[0]["model_id"] == "mod-linear-001"
