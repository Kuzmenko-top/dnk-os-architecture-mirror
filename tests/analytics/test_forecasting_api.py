# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_forecasting_api"
# purpose: "Integration Tests for Analytics Forecasting API endpoints & WebSocket stream"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.services.predictive_forecasting_service import predictive_forecasting_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_service_state():
    predictive_forecasting_service.clear()
    yield
    predictive_forecasting_service.clear()


def test_forecast_models_crud_api():
    # 1. Create Model
    resp = client.post(
        "/api/v1/analytics/forecast/models",
        json={
            "workspace_id": "ws-test-001",
            "metric_type": "queue_depth",
            "model_name": "holt_winters",
            "training_window_days": 14,
            "retrain_frequency_hours": 12,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    model = data.get("model", data)
    model_id = model["id"]
    assert model["model_name"] == "holt_winters"
    assert model["enabled"] is True

    # 2. List Models
    list_resp = client.get("/api/v1/analytics/forecast/models?workspace_id=ws-test-001")
    assert list_resp.status_code == 200
    models_data = list_resp.json()
    models = models_data.get("models", models_data) if isinstance(models_data, dict) else models_data
    assert len(models) == 1
    assert models[0]["id"] == model_id

    # 3. Update Model
    put_resp = client.put(
        f"/api/v1/analytics/forecast/models/{model_id}",
        json={"retrain_frequency_hours": 6, "enabled": False},
    )
    assert put_resp.status_code == 200
    put_data = put_resp.json()
    updated_model = put_data.get("model", put_data)
    assert updated_model["retrain_frequency_hours"] == 6
    assert updated_model["enabled"] is False

    # 4. Trigger Retrain
    train_resp = client.post(f"/api/v1/analytics/forecast/models/{model_id}/train")
    assert train_resp.status_code == 200
    assert train_resp.json()["status"] == "retrained"

    # 5. Delete Model
    del_resp = client.delete(f"/api/v1/analytics/forecast/models/{model_id}")
    assert del_resp.status_code == 204 or del_resp.status_code == 200

    # Verify List Empty
    list_resp2 = client.get("/api/v1/analytics/forecast/models?workspace_id=ws-test-001")
    models_data2 = list_resp2.json()
    models2 = models_data2.get("models", models_data2) if isinstance(models_data2, dict) else models_data2
    assert len(models2) == 0


def test_forecast_snapshots_api():
    resp = client.get("/api/v1/analytics/forecast/snapshots?workspace_id=ws-test-001&metric_type=queue_depth")
    assert resp.status_code == 200
    res = resp.json()
    snapshots = res.get("snapshots", res) if isinstance(res, dict) else res
    assert isinstance(snapshots, list)
    assert len(snapshots) >= 1

    latest_resp = client.get("/api/v1/analytics/forecast/snapshots/latest?workspace_id=ws-test-001")
    assert latest_resp.status_code == 200
    latest = latest_resp.json()
    snapshots_dict = latest.get("latest_snapshots", latest)
    assert "queue_depth" in snapshots_dict
    assert "predictions" in snapshots_dict["queue_depth"]


def test_workload_predictions_api():
    preds_resp = client.get("/api/v1/analytics/workload/predictions?workspace_id=ws-test-001&pool_id=pool-001")
    assert preds_resp.status_code == 200
    preds = preds_resp.json()
    assert isinstance(preds, list)
    assert len(preds) >= 1

    rec_resp = client.get("/api/v1/analytics/workload/predictions/recommended?workspace_id=ws-test-001&pool_id=pool-001")
    assert rec_resp.status_code == 200
    rec = rec_resp.json()
    assert "recommended_worker_count" in rec
    assert rec["recommended_worker_count"] >= 1


def test_forecast_accuracy_api():
    acc_resp = client.get("/api/v1/analytics/forecast/accuracy?workspace_id=ws-test-001")
    assert acc_resp.status_code == 200
    acc = acc_resp.json()
    assert "accuracy_evaluations" in acc or isinstance(acc, list)


def test_websocket_forecast_live_stream():
    with client.websocket_connect("/api/v1/analytics/forecast/live?workspace_id=ws-test-001") as websocket:
        data = websocket.receive_json()
        assert data["type"] == "INIT_FORECAST_STATE"
        assert data["status"] == "connected"
