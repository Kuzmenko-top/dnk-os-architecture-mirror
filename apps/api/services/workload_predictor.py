# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_workload_predictor"
# purpose: "Workload Predictor for Queue Depth, Worker Capacity Planning & Proactive Pre-Scaling Triggers"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from apps.api.services.predictive_forecasting_engine import (
    LinearTrendModel,
    PolynomialTrendModel,
    ConfidenceIntervalCalculator,
)


@dataclass
class WorkloadMetricPoint:
    timestamp: float
    queue_depth: int
    incoming_rate: float
    current_workers: int


class WorkloadPredictor:
    """Predicts future queue depth, recommends worker pool capacity, and fires proactive scale triggers."""

    def __init__(
        self,
        target_sla_latency_sec: float = 30.0,
        single_worker_throughput_per_min: float = 10.0,
        headroom_buffer: float = 0.20,
        scale_up_depth_threshold: int = 50,
        min_workers: int = 1,
        max_workers: int = 50,
    ):
        self.target_sla_latency_sec = max(1.0, target_sla_latency_sec)
        self.single_worker_throughput_per_min = max(0.1, single_worker_throughput_per_min)
        self.headroom_buffer = max(0.0, min(headroom_buffer, 1.0))
        self.scale_up_depth_threshold = scale_up_depth_threshold
        self.min_workers = min_workers
        self.max_workers = max_workers

    def calculate_required_workers(
        self,
        predicted_queue_depth: float,
        incoming_task_rate_per_min: float = 10.0,
    ) -> int:
        """
        Calculates recommended worker count N based on queue depth, target SLA latency and worker throughput.
        N = ceil( (Queue / TargetSLA_min + IncomingRate) / WorkerThroughput * (1 + Headroom) )
        """
        sla_target_min = self.target_sla_latency_sec / 60.0
        queue_drain_rate = predicted_queue_depth / sla_target_min if sla_target_min > 0 else predicted_queue_depth
        total_demand_rate = queue_drain_rate + incoming_task_rate_per_min
        raw_workers = (total_demand_rate / self.single_worker_throughput_per_min) * (1.0 + self.headroom_buffer)
        needed = math.ceil(max(float(self.min_workers), raw_workers))
        return min(self.max_workers, needed)

    def predict_workload(
        self,
        workspace_id: str,
        pool_id: Optional[str],
        history: Optional[List[WorkloadMetricPoint]] = None,
        queue_history: Optional[List[int]] = None,
        current_workers: int = 1,
        horizon_minutes: int = 15,
    ) -> Dict[str, Any]:
        """
        Fits trend model on workload history and generates capacity recommendation and proactive scaling triggers.
        """
        if history:
            q_vals = [float(p.queue_depth) for p in history]
            inc_vals = [float(p.incoming_rate) for p in history]
            curr_workers = history[-1].current_workers if history else current_workers
            avg_incoming = sum(inc_vals) / len(inc_vals) if inc_vals else 10.0
        elif queue_history:
            q_vals = [float(q) for q in queue_history]
            inc_vals = [10.0] * len(q_vals)
            curr_workers = current_workers
            avg_incoming = 10.0
        else:
            q_vals = [5.0]
            inc_vals = [10.0]
            curr_workers = current_workers
            avg_incoming = 10.0

        n_steps = max(1, horizon_minutes // 15)

        # Fit trend model
        poly = PolynomialTrendModel(degree=2, auto_degree=True).fit(q_vals)
        preds = poly.predict(n_steps)
        predicted_q = max(0, int(round(preds[-1])))

        # Fit incoming rate trend
        if history and len(inc_vals) >= 2:
            inc_poly = LinearTrendModel().fit(inc_vals)
            predicted_inc = max(1.0, inc_poly.predict(n_steps)[-1])
        else:
            predicted_inc = avg_incoming

        recommended_workers = self.calculate_required_workers(
            predicted_queue_depth=predicted_q,
            incoming_task_rate_per_min=predicted_inc,
        )

        triggered = (
            (predicted_q >= self.scale_up_depth_threshold)
            or (recommended_workers > curr_workers)
        )

        res_std = poly.residual_std
        confidence = round(max(0.60, min(0.98, 1.0 - (res_std / (predicted_q + 1.0)))), 2)

        now = datetime.now(timezone.utc)
        target_time = now + timedelta(minutes=horizon_minutes)

        return {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "pool_id": pool_id,
            "predicted_at": now.isoformat(),
            "target_time": target_time.isoformat(),
            "predicted_queue_depth": predicted_q,
            "current_worker_count": curr_workers,
            "recommended_worker_count": recommended_workers,
            "confidence_score": confidence,
            "triggered_scaling": triggered,
            "scaling_delta": recommended_workers - curr_workers,
            "horizon_minutes": horizon_minutes,
        }
