# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-TEST-PHASE4-ROUTERS"
# purpose: "Integration & E2E tests for Capacity Analytics REST endpoints (DNK-ANALYTICS-005 Phase 4)"
# canonical_source: true
# alters_files: ["tests/analytics/test_capacity_phase4_routers.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-PHASE4"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_snapshot_ingest_and_query():
    payload = {
        "workspace_id": "ws-phase4-01",
        "cluster_id": "cluster-prod-01",
        "cpu_utilization_pct": 85.5,
        "memory_utilization_pct": 72.0,
        "gpu_utilization_pct": 0.0,
        "active_worker_count": 8,
        "queue_depth_total": 45,
    }

    # 1. Ingest
    res_ingest = client.post("/api/v1/capacity/snapshots", json=payload)
    assert res_ingest.status_code == 201
    data = res_ingest.json()
    assert data["status"] == "ingested"
    assert data["snapshot"]["workspace_id"] == "ws-phase4-01"

    # 2. List
    res_list = client.get("/api/v1/capacity/snapshots", params={"workspace_id": "ws-phase4-01"})
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["count"] >= 1
    assert list_data["snapshots"][0]["cluster_id"] == "cluster-prod-01"


def test_forecast_generate_and_query():
    payload = {
        "workspace_id": "ws-phase4-01",
        "cluster_id": "cluster-prod-01",
        "metric_name": "cpu_utilization_pct",
        "historical_values": [40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0],
        "horizons": ["15m", "1h", "24h", "7d"],
    }

    # 1. Generate multi-horizon
    res_gen = client.post("/api/v1/capacity/forecasts/generate", json=payload)
    assert res_gen.status_code == 200
    data = res_gen.json()
    assert "forecasts" in data
    assert "15m" in data["forecasts"]
    assert "7d" in data["forecasts"]

    # 2. Query
    res_get = client.get(
        "/api/v1/capacity/forecasts",
        params={"workspace_id": "ws-phase4-01", "horizon": "15m"},
    )
    assert res_get.status_code == 200
    get_data = res_get.json()
    assert get_data["count"] >= 1


def test_queue_metrics_and_health():
    metric_payload = {
        "workspace_id": "ws-phase4-01",
        "cluster_id": "cluster-prod-01",
        "queue_name": "task_ingestion_queue",
        "queue_depth": 120,
        "incoming_rate_tps": 50.0,
        "processing_rate_tps": 10.0,
        "avg_wait_time_ms": 1500.0,
        "p95_latency_ms": 3500.0,
        "dead_letter_count": 2,
    }

    # 1. Ingest metric & trigger detection
    res_queue = client.post("/api/v1/capacity/queues/metrics", json=metric_payload)
    assert res_queue.status_code == 201
    data = res_queue.json()
    assert data["status"] == "processed"

    # 2. Check queue health
    res_health = client.get(
        "/api/v1/capacity/queues/health",
        params={"workspace_id": "ws-phase4-01", "queue_name": "task_ingestion_queue"},
    )
    assert res_health.status_code == 200
    health_data = res_health.json()
    assert "health" in health_data

    # 3. Query anomaly alerts
    res_alerts = client.get("/api/v1/capacity/anomalies/alerts")
    assert res_alerts.status_code == 200
    alerts_data = res_alerts.json()
    assert "alerts" in alerts_data


def test_auto_scaling_eval_and_execution():
    eval_payload = {
        "workspace_id": "ws-phase4-01",
        "cluster_id": "cluster-prod-01",
        "current_replicas": 2,
        "telemetry": {
            "cpu_utilization_pct": 92.0,
            "memory_utilization_pct": 88.0,
            "queue_depth": 500,
        },
    }

    # 1. Evaluate scaling
    res_eval = client.post("/api/v1/capacity/scaling/evaluate", json=eval_payload)
    assert res_eval.status_code == 200
    data = res_eval.json()
    assert data["status"] == "evaluated"
    assert data["action_required"] is True
    rec_id = data["recommendation"]["id"]

    # 2. List recommendations
    res_list = client.get(
        "/api/v1/capacity/scaling/recommendations", params={"workspace_id": "ws-phase4-01"}
    )
    assert res_list.status_code == 200
    recs = res_list.json()["recommendations"]
    assert any(r["id"] == rec_id for r in recs)

    # 3. Execute recommendation
    res_exec = client.post(f"/api/v1/capacity/scaling/recommendations/{rec_id}/execute")
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["status"] == "executed"
    assert exec_data["recommendation"]["status"] == "executed"


def test_cost_report_generation():
    cost_payload = {
        "workspace_id": "ws-phase4-01",
        "cluster_id": "cluster-prod-01",
        "total_nodes": 10,
        "spot_nodes": 2,
        "idle_nodes": 1,
        "billing_period": "daily",
    }

    # 1. Generate cost report
    res_gen = client.post("/api/v1/capacity/cost/reports/generate", json=cost_payload)
    assert res_gen.status_code == 200
    data = res_gen.json()
    assert data["status"] == "generated"
    report = data["report"]
    assert report["potential_savings_usd"] > 0.0

    # 2. Query reports
    res_list = client.get(
        "/api/v1/capacity/cost/reports", params={"workspace_id": "ws-phase4-01"}
    )
    assert res_list.status_code == 200
    list_data = res_list.json()
    assert list_data["count"] >= 1
