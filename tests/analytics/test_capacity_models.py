# --- DNK-MRH-HEADER ---
# mrh_id: "TEST-ANALYTICS-005-MODELS"
# purpose: "Unit tests for DNK-ANALYTICS-005 Capacity Planning ORM models"
# canonical_source: true
# alters_files: ["tests/analytics/test_capacity_models.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-PHASE1"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timezone
from apps.api.db.models.capacity_snapshot import CapacitySnapshot
from apps.api.db.models.load_forecast import LoadForecast
from apps.api.db.models.queue_metric import QueueMetric
from apps.api.db.models.anomaly_alert import AnomalyAlert
from apps.api.db.models.scaling_recommendation import ScalingRecommendation
from apps.api.db.models.cost_optimization_report import CostOptimizationReport


def test_capacity_snapshot_model():
    snap = CapacitySnapshot(
        workspace_id="ws-test-01",
        cluster_id="cluster-eu-west-1",
        node_id="worker-node-042",
        cpu_utilization_pct=65.5,
        memory_utilization_pct=78.2,
        gpu_utilization_pct=40.0,
        network_iops_mbps=125.4,
        active_agents_count=8,
        queue_depth=15,
        token_throughput_tps=320.5,
        metrics_payload={"disk_io": "normal", "temp_c": 45},
    )
    d = snap.to_dict()
    assert d["workspace_id"] == "ws-test-01"
    assert d["cluster_id"] == "cluster-eu-west-1"
    assert d["node_id"] == "worker-node-042"
    assert d["cpu_utilization_pct"] == 65.5
    assert d["memory_utilization_pct"] == 78.2
    assert d["gpu_utilization_pct"] == 40.0
    assert d["network_iops_mbps"] == 125.4
    assert d["active_agents_count"] == 8
    assert d["queue_depth"] == 15
    assert d["token_throughput_tps"] == 320.5
    assert d["metrics_payload"]["temp_c"] == 45


def test_load_forecast_model():
    fc = LoadForecast(
        workspace_id="ws-test-01",
        cluster_id="cluster-eu-west-1",
        metric_name="cpu",
        forecast_horizon="24h",
        predicted_value_p50=72.0,
        predicted_value_p90=85.5,
        predicted_value_p99=94.2,
        confidence_score=0.98,
        model_algorithm="arima_v2",
        forecast_series=[{"step": 1, "p50": 70.0}, {"step": 2, "p50": 74.0}],
    )
    d = fc.to_dict()
    assert d["workspace_id"] == "ws-test-01"
    assert d["metric_name"] == "cpu"
    assert d["forecast_horizon"] == "24h"
    assert d["predicted_value_p50"] == 72.0
    assert d["predicted_value_p90"] == 85.5
    assert d["predicted_value_p99"] == 94.2
    assert d["confidence_score"] == 0.98
    assert d["model_algorithm"] == "arima_v2"
    assert len(d["forecast_series"]) == 2


def test_queue_metric_model():
    qm = QueueMetric(
        workspace_id="ws-test-01",
        queue_name="high_priority_inference_queue",
        queue_depth=42,
        incoming_rate_tps=55.0,
        processing_rate_tps=50.0,
        avg_wait_time_ms=120.5,
        p95_latency_ms=280.0,
        dead_letter_count=0,
        active_workers=6,
    )
    d = qm.to_dict()
    assert d["workspace_id"] == "ws-test-01"
    assert d["queue_name"] == "high_priority_inference_queue"
    assert d["queue_depth"] == 42
    assert d["incoming_rate_tps"] == 55.0
    assert d["processing_rate_tps"] == 50.0
    assert d["avg_wait_time_ms"] == 120.5
    assert d["p95_latency_ms"] == 280.0
    assert d["dead_letter_count"] == 0
    assert d["active_workers"] == 6


def test_anomaly_alert_model():
    alert = AnomalyAlert(
        workspace_id="ws-test-01",
        cluster_id="cluster-eu-west-1",
        anomaly_type="spike",
        severity="critical",
        metric_name="token_throughput_tps",
        detected_value=1250.0,
        expected_value=300.0,
        z_score=4.85,
        description="Massive spike in token consumption detected",
        suggested_action="Scale out worker pool or enable rate limiting",
        status="open",
    )
    d = alert.to_dict()
    assert d["anomaly_type"] == "spike"
    assert d["severity"] == "critical"
    assert d["metric_name"] == "token_throughput_tps"
    assert d["detected_value"] == 1250.0
    assert d["expected_value"] == 300.0
    assert d["z_score"] == 4.85
    assert d["status"] == "open"


def test_scaling_recommendation_model():
    rec = ScalingRecommendation(
        workspace_id="ws-test-01",
        cluster_id="cluster-eu-west-1",
        recommendation_type="scale_out",
        current_replicas=4,
        recommended_replicas=8,
        target_metric="queue_depth",
        estimated_cost_delta_usd_per_hour=0.96,
        rationale="Queue depth exceeded 100 tasks with rising p95 latency",
        urgency="high",
        status="pending",
    )
    d = rec.to_dict()
    assert d["recommendation_type"] == "scale_out"
    assert d["current_replicas"] == 4
    assert d["recommended_replicas"] == 8
    assert d["target_metric"] == "queue_depth"
    assert d["estimated_cost_delta_usd_per_hour"] == 0.96
    assert d["urgency"] == "high"
    assert d["status"] == "pending"


def test_cost_optimization_report_model():
    rep = CostOptimizationReport(
        workspace_id="ws-test-01",
        cluster_id="cluster-eu-west-1",
        billing_period="daily",
        current_spend_usd=150.0,
        optimized_spend_usd=95.0,
        potential_savings_usd=55.0,
        savings_percentage=36.67,
        spot_instance_ratio=0.60,
        idle_resource_cost_usd=25.0,
        optimization_opportunities=[
            {"type": "spot_migration", "savings_usd": 35.0},
            {"type": "idle_shutdown", "savings_usd": 20.0},
        ],
    )
    d = rep.to_dict()
    assert d["billing_period"] == "daily"
    assert d["current_spend_usd"] == 150.0
    assert d["optimized_spend_usd"] == 95.0
    assert d["potential_savings_usd"] == 55.0
    assert d["savings_percentage"] == 36.67
    assert d["spot_instance_ratio"] == 0.60
    assert d["idle_resource_cost_usd"] == 25.0
    assert len(d["optimization_opportunities"]) == 2
