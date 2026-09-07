# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_anomaly_detection"
# purpose: "Unit and integration tests for Anomaly Detection (Z-Score, EWMA, TimeSeriesPreprocessor, API endpoints)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.services.anomaly_detection_service import (
    EWMADetector,
    TimeSeriesPreprocessor,
    ZScoreDetector,
    anomaly_detection_service,
)
from apps.api.services.auth_service import auth_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_anomaly_state():
    anomaly_detection_service.clear()
    yield
    anomaly_detection_service.clear()


def test_time_series_preprocessor():
    # Test outlier filtering
    series = [10.0, 10.5, 11.0, 10.2, 9.8, 100.0, 10.1]
    filtered = TimeSeriesPreprocessor.remove_outliers_iqr(series)
    assert 100.0 not in filtered
    assert len(filtered) < len(series)

    # Test normalization
    norm = TimeSeriesPreprocessor.normalize_min_max([10.0, 20.0, 30.0])
    assert norm == [0.0, 0.5, 1.0]


def test_zscore_anomaly_detection():
    history = [10.0, 10.2, 9.8, 10.1, 10.0, 9.9, 10.1]
    # Normal value -> no anomaly
    score_norm, is_anom_norm = ZScoreDetector.compute_z_score(10.15, history, z_threshold=2.5)
    assert is_anom_norm is False
    assert score_norm < 0.5

    # Extreme spike -> anomaly flagged
    score_spike, is_anom_spike = ZScoreDetector.compute_z_score(25.0, history, z_threshold=2.5)
    assert is_anom_spike is True
    assert score_spike >= 0.8


def test_ewma_adaptive_smoothing():
    detector = EWMADetector(alpha=0.3, beta=0.3)
    history = [100.0, 102.0, 99.0, 101.0, 100.5, 100.0, 99.5]

    # Normal value
    score_norm, is_anom_norm = detector.compute_ewma_score(101.0, history, deviation_threshold=2.5)
    assert is_anom_norm is False

    # Large spike
    score_spike, is_anom_spike = detector.compute_ewma_score(250.0, history, deviation_threshold=2.5)
    assert is_anom_spike is True
    assert score_spike >= 0.8


def test_hybrid_anomaly_detection():
    history = [50.0] * 10
    # Normal
    res_norm = anomaly_detection_service.detect_anomaly(50.0, history, algorithm="hybrid")
    assert res_norm["is_anomaly"] is False
    assert res_norm["score"] == 0.0

    # Sudden jump
    res_anom = anomaly_detection_service.detect_anomaly(150.0, history, algorithm="hybrid")
    assert res_anom["is_anomaly"] is True
    assert res_anom["score"] > 0.7


@pytest.mark.asyncio
async def test_anomaly_detection_real_time_stream_and_events():
    history = [20.0, 21.0, 19.5, 20.5, 20.0]

    # Record normal score
    score_entry_norm = await anomaly_detection_service.record_and_evaluate(
        workspace_id="ws_stream_anom",
        metric_type="error_rate",
        current_value=20.2,
        history=history,
    )
    assert score_entry_norm["is_anomaly"] is False

    # Record anomalous spike
    score_entry_spike = await anomaly_detection_service.record_and_evaluate(
        workspace_id="ws_stream_anom",
        metric_type="error_rate",
        current_value=85.0,
        history=history,
    )
    assert score_entry_spike["is_anomaly"] is True

    # Check scores list
    scores = await anomaly_detection_service.get_anomaly_scores(workspace_id="ws_stream_anom")
    assert len(scores) == 2

    # Check anomaly events list
    events = await anomaly_detection_service.get_anomaly_events(workspace_id="ws_stream_anom")
    assert len(events) == 1
    assert events[0]["metric_type"] == "error_rate"
    assert events[0]["current_value"] == 85.0


def test_api_anomaly_scores_and_events():
    token = auth_service.generate_test_token(
        user_id="usr_tester",
        tenant_id="tenant_x",
        workspace_id="ws_api_anom",
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Query scores endpoint
    res_scores = client.get("/api/v1/analytics/anomalies/scores?workspace_id=ws_api_anom", headers=headers)
    assert res_scores.status_code == 200
    assert "scores" in res_scores.json()

    # Query events endpoint
    res_events = client.get("/api/v1/analytics/anomalies/events?workspace_id=ws_api_anom", headers=headers)
    assert res_events.status_code == 200
    assert "events" in res_events.json()
