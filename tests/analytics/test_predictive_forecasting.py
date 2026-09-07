# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_predictive_forecasting"
# purpose: "Unit and Integration Tests for Predictive Forecasting Engine (Linear, Poly, Holt-Winters, ARIMA, Ensemble, Feature Eng)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
from datetime import datetime, timezone, timedelta
import pytest

from apps.api.services.predictive_forecasting_engine import (
    TimeSeriesFeatureEngineer,
    LinearTrendModel,
    PolynomialTrendModel,
    HoltWintersModel,
    ARIMABaselineModel,
    EnsembleForecaster,
    ConfidenceIntervalCalculator,
    PredictiveForecastingEngine,
)


def test_time_series_feature_engineering():
    """Verify lag features, rolling statistics and cyclical seasonality encoding."""
    values = [10.0, 12.0, 15.0, 14.0, 18.0, 20.0, 22.0, 25.0]
    base_time = datetime(2026, 8, 28, 12, 0, 0, tzinfo=timezone.utc)

    # Cyclical seasonality features
    cyclical = TimeSeriesFeatureEngineer.extract_cyclical_features(base_time)
    assert "hour_sin" in cyclical
    assert "hour_cos" in cyclical
    assert "day_of_week_sin" in cyclical
    assert "day_of_week_cos" in cyclical
    assert -1.0 <= cyclical["hour_sin"] <= 1.0

    # Lag features
    lags = TimeSeriesFeatureEngineer.extract_lag_features(values, lags=[1, 2, 3])
    assert lags["lag_1"] == 25.0
    assert lags["lag_2"] == 22.0
    assert lags["lag_3"] == 20.0

    # Rolling statistics
    rolling = TimeSeriesFeatureEngineer.extract_rolling_stats(values, window=3)
    assert math.isclose(rolling["rolling_mean"], (25.0 + 22.0 + 20.0) / 3.0, rel_tol=1e-3)
    assert rolling["rolling_max"] == 25.0
    assert rolling["rolling_min"] == 20.0
    assert rolling["rolling_std"] > 0


def test_linear_regression_trend_fitting():
    """Verify linear trend fitting, slope, intercept, R2, and prediction."""
    model = LinearTrendModel()
    # y = 2 * t + 5 for t = 0..9
    y = [2.0 * ti + 5.0 for ti in range(10)]

    model.fit(y)
    assert math.isclose(model.slope, 2.0, rel_tol=1e-3)
    assert math.isclose(model.intercept, 5.0, rel_tol=1e-3)
    assert math.isclose(model.r2_score, 1.0, rel_tol=1e-3)

    preds = model.predict(steps_ahead=3)
    assert len(preds) == 3
    assert math.isclose(preds[0], 25.0, rel_tol=1e-3)
    assert math.isclose(preds[1], 27.0, rel_tol=1e-3)
    assert math.isclose(preds[2], 29.0, rel_tol=1e-3)


def test_polynomial_trend_degree_selection():
    """Verify polynomial fitting and degree selection."""
    # Quadratic curve y = t^2 - 3t + 2 for t = 0..11
    y = [ti**2 - 3.0 * ti + 2.0 for ti in range(12)]

    model = PolynomialTrendModel(degree=2, auto_degree=True, max_degree=3)
    model.fit(y)
    assert model.r2_score > 0.98

    preds = model.predict(steps_ahead=2)
    expected_12 = 12.0**2 - 3.0 * 12.0 + 2.0  # 144 - 36 + 2 = 110
    assert math.isclose(preds[0], expected_12, rel_tol=1e-2)


def test_holt_winters_seasonal_decomposition():
    """Verify Holt-Winters triple exponential smoothing with additive seasonality."""
    season_pattern = [10.0, 25.0, 50.0, 15.0]
    series = []
    for cycle in range(5):
        for s in season_pattern:
            series.append(s + cycle * 5.0)

    hw = HoltWintersModel(season_length=4, alpha=0.3, beta=0.1, gamma=0.3)
    hw.fit(series)

    forecast = hw.predict(steps_ahead=4)
    assert len(forecast) == 4
    # The peak of the cycle should be at index 2 (matching pattern 50.0 + trend)
    assert forecast[2] > forecast[0]
    assert forecast[2] > forecast[3]


def test_arima_parameter_estimation():
    """Verify ARIMA baseline autoregressive estimation and prediction."""
    series = [10.0]
    for _ in range(30):
        series.append(0.8 * series[-1] + 2.0)

    arima = ARIMABaselineModel(p=2, d=1, q=1)
    arima.fit(series)
    assert arima.residual_std >= 0

    preds = arima.predict(steps_ahead=3)
    assert len(preds) == 3
    assert all(p > 0 for p in preds)


def test_confidence_interval_calculation():
    """Verify p10, p50, p90 interval calculation and non-negativity constraint."""
    predicted_values = [100.0, 110.0, 120.0]
    residual_std = 10.0

    intervals = ConfidenceIntervalCalculator.calculate_intervals(
        predicted_values=predicted_values,
        residual_std=residual_std,
        metric_type="queue_depth",
    )

    assert len(intervals) == 3
    for item in intervals:
        p10, p50, p90 = item["p10"], item["p50"], item["p90"]
        assert p10 <= p50 <= p90
        assert p10 >= 0.0

    # Test uncertainty scaling with horizon
    spread_step1 = intervals[0]["p90"] - intervals[0]["p10"]
    spread_step3 = intervals[2]["p90"] - intervals[2]["p10"]
    assert spread_step3 > spread_step1


def test_ensemble_weighted_averaging():
    """Verify ensemble forecast combining multiple models."""
    y = [10.0 + 2.0 * ti + math.sin(ti) for ti in range(16)]

    linear_preds = LinearTrendModel().fit(y).predict(4)
    poly_preds = PolynomialTrendModel(degree=2).fit(y).predict(4)
    hw_preds = HoltWintersModel(season_length=4).fit(y).predict(4)
    arima_preds = ARIMABaselineModel(p=1, d=0).fit(y).predict(4)

    ensemble = EnsembleForecaster(
        weights={"linear": 0.4, "polynomial": 0.2, "holt_winters": 0.2, "arima": 0.2}
    )

    ensemble_preds = ensemble.forecast({
        "linear": linear_preds,
        "polynomial": poly_preds,
        "holt_winters": hw_preds,
        "arima": arima_preds,
    })

    assert len(ensemble_preds) == 4
    assert all(p > 0 for p in ensemble_preds)


def test_full_forecast_pipeline():
    """Verify end-to-end forecast engine snapshot generation."""
    from apps.api.services.predictive_forecasting_engine import TimeSeriesPoint

    engine = PredictiveForecastingEngine()
    history_values = [15.0 + 1.5 * i + (5.0 if i % 4 == 0 else 0.0) for i in range(30)]
    base_time = datetime(2026, 8, 28, 0, 0, 0, tzinfo=timezone.utc)
    points = [
        TimeSeriesPoint(timestamp=base_time + timedelta(hours=i), value=val)
        for i, val in enumerate(history_values)
    ]

    res = engine.fit_and_forecast(
        workspace_id="ws-alpha-001",
        metric_type="queue_depth",
        history=points,
        model_name="ensemble",
        forecast_horizon_minutes=60,
        step_minutes=15,
    )

    assert res["workspace_id"] == "ws-alpha-001"
    assert res["metric_type"] == "queue_depth"
    assert res["model_used"] == "ensemble"
    assert len(res["predictions"]) == 4
    for p in res["predictions"]:
        assert p["confidence_p10"] <= p["confidence_p50"] <= p["confidence_p90"]
        assert p["confidence_score"] >= 0.5
