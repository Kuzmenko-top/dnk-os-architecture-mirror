# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_workload_prediction"
# purpose: "Unit & Integration Tests for Workload Predictor, Capacity Planning, and Proactive Scaling Triggers"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.workload_predictor import WorkloadPredictor, WorkloadMetricPoint


def test_workload_predictor_initialization():
    predictor = WorkloadPredictor(target_sla_latency_sec=30.0, single_worker_throughput_per_min=10.0, headroom_buffer=0.25)
    assert predictor.target_sla_latency_sec == 30.0
    assert predictor.single_worker_throughput_per_min == 10.0
    assert predictor.headroom_buffer == 0.25


def test_capacity_planning_calculation():
    predictor = WorkloadPredictor(target_sla_latency_sec=30.0, single_worker_throughput_per_min=10.0, headroom_buffer=0.20)
    # 100 queue depth, 20 incoming rate
    workers = predictor.calculate_required_workers(predicted_queue_depth=100.0, incoming_task_rate_per_min=20.0)
    # expected: (100 / (30/60) + 20) = 200 + 20 = 220 tasks/min demand -> 220 / 10 = 22 workers * 1.2 = 26.4 -> 27
    assert workers >= 20
    assert isinstance(workers, int)


def test_workload_prediction_with_history():
    predictor = WorkloadPredictor()
    history = [
        WorkloadMetricPoint(timestamp=1000 + i * 60, queue_depth=10 + i * 2, incoming_rate=5.0 + i * 0.5, current_workers=2)
        for i in range(20)
    ]

    res = predictor.predict_workload(
        workspace_id="ws-alpha-001",
        pool_id="pool-worker-001",
        history=history,
        horizon_minutes=60,
    )

    assert res["workspace_id"] == "ws-alpha-001"
    assert res["pool_id"] == "pool-worker-001"
    assert res["predicted_queue_depth"] > 0
    assert res["recommended_worker_count"] >= 1
    assert 0.0 <= res["confidence_score"] <= 1.0


def test_proactive_scaling_trigger_activation():
    predictor = WorkloadPredictor(scale_up_depth_threshold=50)
    # High queue depth surging
    history = [
        WorkloadMetricPoint(timestamp=1000 + i * 60, queue_depth=30 + i * 5, incoming_rate=20.0, current_workers=2)
        for i in range(15)
    ]

    res = predictor.predict_workload(
        workspace_id="ws-alpha-001",
        pool_id="pool-worker-001",
        history=history,
        horizon_minutes=15,
    )

    assert res["triggered_scaling"] is True
    assert res["recommended_worker_count"] > 2


def test_proactive_scaling_no_trigger_on_stable_load():
    predictor = WorkloadPredictor(scale_up_depth_threshold=50)
    # Low queue depth stable
    history = [
        WorkloadMetricPoint(timestamp=1000 + i * 60, queue_depth=5, incoming_rate=2.0, current_workers=4)
        for i in range(15)
    ]

    res = predictor.predict_workload(
        workspace_id="ws-alpha-001",
        pool_id="pool-worker-001",
        history=history,
        horizon_minutes=15,
    )

    assert res["triggered_scaling"] is False
    assert res["recommended_worker_count"] <= 4
