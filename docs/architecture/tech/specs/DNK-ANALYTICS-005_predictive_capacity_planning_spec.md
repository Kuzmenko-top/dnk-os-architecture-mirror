# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ANALYTICS-005_predictive_capacity_planning_spec.md"
# purpose: "TaskDNA Specification for DNK-ANALYTICS-005: Predictive Capacity Planning & ML Forecasting V2."
# canonical_source: true
# alters_files: [
#   "apps/api/db/models/capacity_snapshot.py",
#   "apps/api/db/models/load_forecast.py",
#   "apps/api/db/models/queue_metric.py",
#   "apps/api/db/models/anomaly_alert.py",
#   "apps/api/db/models/scaling_recommendation.py",
#   "apps/api/db/models/cost_optimization_report.py",
#   "apps/api/db/models/__init__.py",
#   "apps/api/services/capacity_forecasting_engine.py",
#   "apps/api/services/queue_anomaly_detector.py",
#   "apps/api/services/auto_scaling_advisor.py",
#   "apps/api/routers/capacity_analytics_router.py",
#   "apps/api/routers/capacity_analytics_ws.py",
#   "tests/analytics/test_capacity_models.py"
# ]
# triggers_tasks: [
#   "TASK-ANALYTICS-005-PHASE1-MODELS",
#   "TASK-ANALYTICS-005-PHASE2-FORECAST-ENGINE",
#   "TASK-ANALYTICS-005-PHASE3-ANOMALY-AUTOSCALING",
#   "TASK-ANALYTICS-005-PHASE4-REST-WS-ROUTER"
# ]
# status: "Draft"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych"
# --- END DNK-MRH-HEADER ---

# 📈 TaskDNA Spec: DNK-ANALYTICS-005 — Predictive Capacity Planning & ML Forecasting V2

## 1. Overview & Architectural Goals
DNK-ANALYTICS-005 delivers real-time telemetry, predictive capacity planning, ML-driven time-series load forecasting (ARIMA / Holt-Winters / surrogate ML), task queue anomaly detection (outliers, latency spikes, congestion), and automated horizontal scaling recommendations with spot/on-demand cost optimization.

## 2. Core Entities & ORM Models
1. **CapacitySnapshot** (`capacity_snapshot.py`):
   - Periodic telemetry snapshot of cluster/node metrics (CPU, RAM, GPU, IOPS, active agents, queue length, token throughput).
2. **LoadForecast** (`load_forecast.py`):
   - Multi-horizon predictive forecasts (15m, 1h, 24h, 7d) with confidence intervals (p50, p90, p99) and model metadata.
3. **QueueMetric** (`queue_metric.py`):
   - Detailed queue health metrics: queue depth, processing latency, task rejection rate, worker utilization.
4. **AnomalyAlert** (`anomaly_alert.py`):
   - Real-time detected anomalies (spike, drift, starvation, threshold breach) with severity and mitigation suggestions.
5. **ScalingRecommendation** (`scaling_recommendation.py`):
   - Recommended scale-up / scale-down / scale-out actions with target replicas, trigger reasons, and execution status.
6. **CostOptimizationReport** (`cost_optimization_report.py`):
   - Analysis of cluster expenditure, idle resource wastage, Spot vs On-Demand savings, and recommended instance types.

## 3. Four-Phase Delivery Plan
- **Phase 1**: TaskDNA Spec & 6 Core ORM Models with validation, `to_dict()` serialization and unit tests.
- **Phase 2**: Predictive Capacity Forecasting Engine (time-series smoothing, trend extrapolation, confidence bounds).
- **Phase 3**: Queue Anomaly Detector & Auto-Scaling Advisor with cost optimization algorithms.
- **Phase 4**: FastAPI REST Router + WebSocket Streaming Telemetry endpoints with E2E integration tests.
