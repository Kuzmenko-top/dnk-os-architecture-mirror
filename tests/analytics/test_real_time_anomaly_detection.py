# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_real_time_anomaly_detection"
# purpose: "Unit & API Integration Tests for Real-Time Anomaly Detection Engine (DNK-ANALYTICS-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient

from apps.api.main import app
from apps.api.services.real_time_anomaly_detector import (
    ZScoreDetector,
    IQRDetector,
    HoltWintersDetector,
    LightweightIsolationForestDetector,
    RealTimeAnomalyDetector,
)

client = TestClient(app)


def test_zscore_detector_normal_and_anomaly():
    history = [10.0, 10.2, 9.8, 10.1, 10.3, 9.9, 10.0, 10.1]
    normal_res = ZScoreDetector.detect(current_value=10.2, history=history, sensitivity=0.80)
    assert normal_res["is_anomalous"] is False
    assert normal_res["anomaly_score"] < 0.50

    anomaly_res = ZScoreDetector.detect(current_value=50.0, history=history, sensitivity=0.80)
    assert anomaly_res["is_anomalous"] is True
    assert anomaly_res["anomaly_score"] > 0.80


def test_iqr_detector_normal_and_anomaly():
    history = [100.0, 102.0, 101.0, 99.0, 103.0, 98.0, 100.5, 101.5]
    normal_res = IQRDetector.detect(current_value=101.0, history=history, sensitivity=0.80)
    assert normal_res["is_anomalous"] is False

    anomaly_res = IQRDetector.detect(current_value=300.0, history=history, sensitivity=0.80)
    assert anomaly_res["is_anomalous"] is True
    assert anomaly_res["anomaly_score"] > 0.70


def test_holt_winters_detector():
    history = [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0]
    # Forecast for step 8 should be ~24.0
    res_normal = HoltWintersDetector.forecast_and_detect(current_value=24.0, history=history, sensitivity=0.80)
    assert res_normal["is_anomalous"] is False

    res_anom = HoltWintersDetector.forecast_and_detect(current_value=100.0, history=history, sensitivity=0.80)
    assert res_anom["is_anomalous"] is True


def test_isolation_forest_detector():
    history = [50.0, 51.0, 49.0, 52.0, 48.0, 50.5, 51.2, 49.8]
    res_normal = LightweightIsolationForestDetector.detect(current_value=50.2, history=history, sensitivity=0.80)
    assert res_normal["is_anomalous"] is False

    res_anom = LightweightIsolationForestDetector.detect(current_value=250.0, history=history, sensitivity=0.80)
    assert res_anom["is_anomalous"] is True


def test_real_time_anomaly_orchestrator_ensemble():
    orchestrator = RealTimeAnomalyDetector()
    history = [20.0, 21.0, 19.5, 20.5, 20.1, 19.8, 20.2]

    res_single = orchestrator.evaluate_metric(current_value=20.0, history=history, detector_type="zscore")
    assert res_single["detector"] == "zscore"

    res_ensemble = orchestrator.evaluate_metric(current_value=200.0, history=history, detector_type="ensemble")
    assert res_ensemble["detector"] == "ensemble"
    assert res_ensemble["is_anomalous"] is True
    assert "sub_detectors" in res_ensemble


def test_anomaly_detection_configs_crud_api():
    workspace_id = "test-ws-004"

    # Create config
    payload = {
        "workspace_id": workspace_id,
        "metric_type": "latency_p95",
        "detector_type": "zscore",
        "sensitivity": 0.85,
        "rolling_window_hours": 24,
        "enabled": True,
    }
    create_res = client.post("/api/v1/anomaly-detection/configs", json=payload)
    assert create_res.status_code == 200
    config_data = create_res.json()
    assert config_data["metric_type"] == "latency_p95"
    config_id = config_data["id"]

    # List configs
    list_res = client.get(f"/api/v1/anomaly-detection/configs?workspace_id={workspace_id}")
    assert list_res.status_code == 200
    configs = list_res.json()
    assert len(configs) >= 1

    # Update config
    update_res = client.put(f"/api/v1/anomaly-detection/configs/{config_id}", json={"sensitivity": 0.90})
    assert update_res.status_code == 200
    assert update_res.json()["sensitivity"] == 0.90

    # Delete config
    del_res = client.delete(f"/api/v1/anomaly-detection/configs/{config_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"
