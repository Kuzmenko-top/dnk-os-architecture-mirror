# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-ANALYTICS-005-FORECASTING-ENGINE"
# purpose: "Unit tests for CapacityForecastingEngine in DNK-ANALYTICS-005 Phase 2"
# canonical_source: true
# alters_files: ["tests/analytics/test_capacity_forecasting_engine.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-PHASE2"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone, timedelta
from apps.api.services.capacity_forecasting_engine import CapacityForecastingEngine


@pytest.fixture
def engine():
    return CapacityForecastingEngine()


def test_ingest_metric_and_historical_series(engine):
    now = datetime.now(timezone.utc)
    for i in range(10):
        engine.ingest_metric("cluster-1", "cpu", 50.0 + i * 2.0, now + timedelta(minutes=i))

    history = engine.get_historical_series("cluster-1", "cpu", limit=5)
    assert len(history) == 5
    assert history[-1]["value"] == 68.0


def test_ingest_snapshot(engine):
    snap = {
        "cluster_id": "cluster-prod",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cpu_utilization_pct": 75.0,
        "memory_utilization_pct": 82.0,
        "gpu_utilization_pct": 45.0,
        "network_iops_mbps": 150.0,
        "active_agents_count": 12,
        "queue_depth": 25,
        "token_throughput_tps": 400.0,
    }
    engine.ingest_snapshot(snap)

    cpu_hist = engine.get_historical_series("cluster-prod", "cpu")
    assert len(cpu_hist) == 1
    assert cpu_hist[0]["value"] == 75.0

    mem_hist = engine.get_historical_series("cluster-prod", "memory")
    assert len(mem_hist) == 1
    assert mem_hist[0]["value"] == 82.0

    token_hist = engine.get_historical_series("cluster-prod", "token_throughput")
    assert len(token_hist) == 1
    assert token_hist[0]["value"] == 400.0


def test_generate_forecast_holt_winters(engine):
    base_time = datetime.now(timezone.utc)
    # Simulate upward trend with minor noise
    values = [30.0, 32.5, 35.0, 37.0, 40.0, 43.0, 45.0, 48.0, 50.0]
    for idx, v in enumerate(values):
        engine.ingest_metric("cluster-1", "cpu", v, base_time + timedelta(minutes=idx * 5))

    fc = engine.generate_forecast(
        workspace_id="ws-alpha",
        cluster_id="cluster-1",
        metric_name="cpu",
        forecast_horizon="1h",
        model_algorithm="holt_winters",
    )

    assert fc["workspace_id"] == "ws-alpha"
    assert fc["cluster_id"] == "cluster-1"
    assert fc["metric_name"] == "cpu"
    assert fc["forecast_horizon"] == "1h"
    assert fc["predicted_value_p50"] >= 45.0
    assert fc["predicted_value_p90"] >= fc["predicted_value_p50"]
    assert fc["predicted_value_p99"] >= fc["predicted_value_p90"]
    assert fc["confidence_score"] > 0.60
    assert len(fc["forecast_series"]) == 12

    # Check cached retrieval
    cached = engine.get_forecast_by_id(fc["id"])
    assert cached is not None
    assert cached["id"] == fc["id"]


def test_generate_forecast_linear_regression(engine):
    base_time = datetime.now(timezone.utc)
    # Perfect linear slope: y = 10 + 2*x
    for i in range(10):
        engine.ingest_metric("cluster-1", "memory", 10.0 + 2.0 * i, base_time + timedelta(hours=i))

    fc = engine.generate_forecast(
        workspace_id="ws-alpha",
        cluster_id="cluster-1",
        metric_name="memory",
        forecast_horizon="24h",
        model_algorithm="linear_regression",
    )

    assert fc["model_algorithm"] == "linear_regression"
    assert len(fc["forecast_series"]) == 24
    assert fc["confidence_score"] >= 0.85
    # First step should extrapolate next linear value (around 30.0)
    assert fc["forecast_series"][0]["p50"] >= 28.0


def test_quantiles_ordering_and_monotonicity(engine):
    base_time = datetime.now(timezone.utc)
    for i in range(20):
        val = 50.0 + (i % 3) * 5.0
        engine.ingest_metric("cluster-quantiles", "tokens", val, base_time + timedelta(minutes=i))

    fc = engine.generate_forecast(
        workspace_id="ws-alpha",
        cluster_id="cluster-quantiles",
        metric_name="tokens",
        forecast_horizon="15m",
    )

    assert len(fc["forecast_series"]) == 15
    for pt in fc["forecast_series"]:
        assert pt["p50"] <= pt["p90"] + 1e-6
        assert pt["p90"] <= pt["p99"] + 1e-6


def test_generate_multi_horizon_forecast(engine):
    base_time = datetime.now(timezone.utc)
    for i in range(15):
        engine.ingest_metric("cluster-multi", "cpu", 40.0 + i, base_time + timedelta(minutes=i * 10))

    multi_fc = engine.generate_multi_horizon_forecast(
        workspace_id="ws-alpha",
        cluster_id="cluster-multi",
        metric_name="cpu",
    )

    assert set(multi_fc.keys()) == {"15m", "1h", "24h", "7d"}
    assert len(multi_fc["15m"]["forecast_series"]) == 15
    assert len(multi_fc["1h"]["forecast_series"]) == 12
    assert len(multi_fc["24h"]["forecast_series"]) == 24
    assert len(multi_fc["7d"]["forecast_series"]) == 14


def test_evaluate_model_accuracy(engine):
    actuals = [10.0, 20.0, 30.0, 40.0, 50.0]
    perfect_preds = [10.0, 20.0, 30.0, 40.0, 50.0]

    perf_metrics = engine.evaluate_model_accuracy(actuals, perfect_preds)
    assert perf_metrics["mae"] == 0.0
    assert perf_metrics["mse"] == 0.0
    assert perf_metrics["mape"] == 0.0
    assert perf_metrics["r2"] == 1.0

    imperfect_preds = [12.0, 18.0, 33.0, 39.0, 52.0]
    imp_metrics = engine.evaluate_model_accuracy(actuals, imperfect_preds)
    assert imp_metrics["mae"] == 2.0
    assert imp_metrics["mse"] > 0
    assert imp_metrics["mape"] > 0
    assert 0.0 <= imp_metrics["r2"] <= 1.0


def test_edge_cases_empty_and_single_point(engine):
    # Empty time-series fallback
    fc_empty = engine.generate_forecast(
        workspace_id="ws-alpha",
        cluster_id="empty-cluster",
        metric_name="cpu",
        forecast_horizon="15m",
    )
    assert fc_empty is not None
    assert len(fc_empty["forecast_series"]) == 15

    # Single point
    engine.ingest_metric("single-point-cluster", "memory", 60.0)
    fc_single = engine.generate_forecast(
        workspace_id="ws-alpha",
        cluster_id="single-point-cluster",
        metric_name="memory",
        forecast_horizon="1h",
    )
    assert fc_single["predicted_value_p50"] == 60.0
