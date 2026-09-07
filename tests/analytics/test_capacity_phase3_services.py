# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-ANALYTICS-005-PHASE3-SERVICES"
# purpose: "Unit tests for QueueAnomalyDetector and CapacityAutoscalerRecommender (DNK-ANALYTICS-005 Phase 3)"
# canonical_source: true
# alters_files: ["tests/analytics/test_capacity_phase3_services.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-PHASE3"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone
from apps.api.services.queue_anomaly_detector import QueueAnomalyDetector
from apps.api.services.capacity_autoscaler_recommender import CapacityAutoscalerRecommender


@pytest.fixture
def anomaly_detector():
    return QueueAnomalyDetector(z_score_threshold=3.0, window_size=20)


@pytest.fixture
def autoscaler():
    return CapacityAutoscalerRecommender(
        target_cpu_pct=70.0,
        target_queue_depth=20,
        min_replicas=2,
        max_replicas=20,
        hourly_node_cost_ondemand=0.20,
        hourly_node_cost_spot=0.06,
    )


# --- QueueAnomalyDetector Tests ---


def test_queue_anomaly_dead_letter_detection(anomaly_detector):
    metric = {
        "workspace_id": "ws-alpha",
        "queue_name": "ai-task-queue",
        "queue_depth": 5,
        "incoming_rate_tps": 10.0,
        "processing_rate_tps": 10.0,
        "avg_wait_time_ms": 50.0,
        "p95_latency_ms": 120.0,
        "dead_letter_count": 15,
        "active_workers": 4,
    }
    alerts = anomaly_detector.detect_anomalies(
        workspace_id="ws-alpha",
        cluster_id="cluster-eu",
        queue_name="ai-task-queue",
        current_metric=metric,
    )

    assert len(alerts) >= 1
    dlq_alert = next((a for a in alerts if a["metric_name"] == "dead_letter_count"), None)
    assert dlq_alert is not None
    assert dlq_alert["severity"] == "critical"
    assert dlq_alert["anomaly_type"] == "queue_overflow"


def test_queue_anomaly_starvation_detection(anomaly_detector):
    metric = {
        "workspace_id": "ws-alpha",
        "queue_name": "ai-task-queue",
        "queue_depth": 35,
        "incoming_rate_tps": 25.0,
        "processing_rate_tps": 0.0,
        "avg_wait_time_ms": 400.0,
        "p95_latency_ms": 800.0,
        "dead_letter_count": 0,
        "active_workers": 2,
    }
    alerts = anomaly_detector.detect_anomalies(
        workspace_id="ws-alpha",
        cluster_id="cluster-eu",
        queue_name="ai-task-queue",
        current_metric=metric,
    )

    starvation_alert = next((a for a in alerts if a["anomaly_type"] == "starvation"), None)
    assert starvation_alert is not None
    assert starvation_alert["severity"] == "critical"
    assert starvation_alert["detected_value"] == 0.0


def test_queue_anomaly_zscore_spike_detection(anomaly_detector):
    # Establish baseline history with small variance (depth ~10)
    for i in range(10):
        anomaly_detector.ingest_queue_metric({
            "workspace_id": "ws-alpha",
            "queue_name": "worker-queue",
            "queue_depth": 10 + (i % 2),
            "incoming_rate_tps": 5.0,
            "processing_rate_tps": 5.0,
            "avg_wait_time_ms": 20.0,
            "p95_latency_ms": 50.0,
            "dead_letter_count": 0,
        })

    # Ingest massive spike (depth = 120)
    spike_metric = {
        "workspace_id": "ws-alpha",
        "queue_name": "worker-queue",
        "queue_depth": 120,
        "incoming_rate_tps": 50.0,
        "processing_rate_tps": 5.0,
        "avg_wait_time_ms": 50.0,
        "p95_latency_ms": 100.0,
        "dead_letter_count": 0,
    }
    alerts = anomaly_detector.detect_anomalies(
        workspace_id="ws-alpha",
        cluster_id="cluster-eu",
        queue_name="worker-queue",
        current_metric=spike_metric,
    )

    spike_alert = next((a for a in alerts if a["anomaly_type"] == "spike"), None)
    assert spike_alert is not None
    assert spike_alert["z_score"] >= 3.0
    assert spike_alert["detected_value"] == 120.0


def test_queue_anomaly_latency_outlier(anomaly_detector):
    metric = {
        "workspace_id": "ws-alpha",
        "queue_name": "latency-queue",
        "queue_depth": 8,
        "incoming_rate_tps": 4.0,
        "processing_rate_tps": 4.0,
        "avg_wait_time_ms": 100.0,
        "p95_latency_ms": 1500.0,
        "dead_letter_count": 0,
        "active_workers": 2,
    }
    alerts = anomaly_detector.detect_anomalies(
        workspace_id="ws-alpha",
        cluster_id="cluster-eu",
        queue_name="latency-queue",
        current_metric=metric,
    )

    latency_alert = next((a for a in alerts if a["metric_name"] == "p95_latency_ms"), None)
    assert latency_alert is not None
    assert latency_alert["detected_value"] == 1500.0


def test_queue_alert_lifecycle_and_summary(anomaly_detector):
    metric = {
        "workspace_id": "ws-lifecycle",
        "queue_name": "q-1",
        "queue_depth": 50,
        "incoming_rate_tps": 30.0,
        "processing_rate_tps": 0.0,
        "avg_wait_time_ms": 500.0,
        "p95_latency_ms": 1200.0,
        "dead_letter_count": 5,
    }
    alerts = anomaly_detector.detect_anomalies("ws-lifecycle", "cluster-1", "q-1", metric)
    assert len(alerts) >= 1

    active = anomaly_detector.get_active_alerts(workspace_id="ws-lifecycle")
    assert len(active) >= 1

    # Check health summary (should be critical)
    summary = anomaly_detector.get_queue_health_summary("ws-lifecycle", "q-1")
    assert summary["status"] in ["critical", "warning"]
    assert summary["open_alerts_count"] >= 1

    # Resolve alert
    first_id = active[0]["id"]
    resolved = anomaly_detector.resolve_alert(first_id)
    assert resolved["status"] == "resolved"


# --- CapacityAutoscalerRecommender Tests ---


def test_autoscaler_scale_out_on_cpu(autoscaler):
    telemetry = {"cpu_utilization_pct": 92.0, "queue_depth": 5}
    rec = autoscaler.evaluate_scaling(
        workspace_id="ws-scale",
        cluster_id="cluster-prod",
        current_replicas=4,
        telemetry=telemetry,
    )

    assert rec is not None
    assert rec["recommendation_type"] == "scale_out"
    assert rec["recommended_replicas"] > 4
    assert rec["target_metric"] == "cpu"
    assert rec["estimated_cost_delta_usd_per_hour"] > 0


def test_autoscaler_scale_out_on_queue_pressure(autoscaler):
    telemetry = {"cpu_utilization_pct": 50.0, "queue_depth": 80}
    rec = autoscaler.evaluate_scaling(
        workspace_id="ws-scale",
        cluster_id="cluster-prod",
        current_replicas=3,
        telemetry=telemetry,
    )

    assert rec is not None
    assert rec["recommendation_type"] == "scale_out"
    assert rec["recommended_replicas"] >= 6
    assert rec["target_metric"] == "queue_depth"


def test_autoscaler_proactive_scale_out_on_forecast(autoscaler):
    telemetry = {"cpu_utilization_pct": 55.0, "queue_depth": 10}
    forecast = {"predicted_value_p90": 88.0}
    rec = autoscaler.evaluate_scaling(
        workspace_id="ws-scale",
        cluster_id="cluster-prod",
        current_replicas=4,
        telemetry=telemetry,
        forecast=forecast,
    )

    assert rec is not None
    assert rec["recommendation_type"] == "scale_out"
    assert rec["recommended_replicas"] > 4


def test_autoscaler_scale_in_on_low_load(autoscaler):
    telemetry = {"cpu_utilization_pct": 15.0, "queue_depth": 1}
    rec = autoscaler.evaluate_scaling(
        workspace_id="ws-scale",
        cluster_id="cluster-prod",
        current_replicas=8,
        telemetry=telemetry,
    )

    assert rec is not None
    assert rec["recommendation_type"] == "scale_in"
    assert rec["recommended_replicas"] < 8
    assert rec["estimated_cost_delta_usd_per_hour"] < 0


def test_autoscaler_maintain_state(autoscaler):
    telemetry = {"cpu_utilization_pct": 60.0, "queue_depth": 12}
    rec = autoscaler.evaluate_scaling(
        workspace_id="ws-scale",
        cluster_id="cluster-prod",
        current_replicas=5,
        telemetry=telemetry,
    )
    assert rec is None


def test_autoscaler_cost_optimization_report(autoscaler):
    report = autoscaler.generate_cost_report(
        workspace_id="ws-cost",
        cluster_id="cluster-prod",
        total_nodes=10,
        spot_nodes=2,
        idle_nodes=1,
        billing_period="daily",
    )

    assert report["current_spend_usd"] > 0
    assert report["optimized_spend_usd"] < report["current_spend_usd"]
    assert report["potential_savings_usd"] > 0
    assert report["savings_percentage"] > 0
    assert len(report["optimization_opportunities"]) >= 1


def test_autoscaler_recommendation_execution(autoscaler):
    telemetry = {"cpu_utilization_pct": 95.0, "queue_depth": 10}
    rec = autoscaler.evaluate_scaling(
        workspace_id="ws-exec",
        cluster_id="cluster-1",
        current_replicas=2,
        telemetry=telemetry,
    )
    assert rec is not None

    pending = autoscaler.get_pending_recommendations("ws-exec")
    assert len(pending) == 1

    executed = autoscaler.execute_recommendation(rec["id"])
    assert executed["status"] == "executed"
    assert executed["executed_at"] is not None
