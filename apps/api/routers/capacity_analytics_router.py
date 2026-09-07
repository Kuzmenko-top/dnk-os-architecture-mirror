# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-ROUTER-CAPACITY-ANALYTICS"
# purpose: "FastAPI REST API Router for Predictive Capacity Planning, ML Forecasting & Auto-Scaling"
# canonical_source: true
# alters_files: ["apps/api/routers/capacity_analytics_router.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-PHASE4"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from apps.api.services.capacity_forecasting_engine import CapacityForecastingEngine
from apps.api.services.queue_anomaly_detector import QueueAnomalyDetector
from apps.api.services.capacity_autoscaler_recommender import CapacityAutoscalerRecommender

router = APIRouter(prefix="/api/v1/capacity", tags=["Predictive Capacity & Load Forecasting"])

_forecasting_engine = CapacityForecastingEngine()
_anomaly_detector = QueueAnomalyDetector()
_autoscaler = CapacityAutoscalerRecommender()


def get_capacity_services() -> Dict[str, Any]:
    return {
        "forecasting_engine": _forecasting_engine,
        "anomaly_detector": _anomaly_detector,
        "autoscaler": _autoscaler,
    }


# ------------------------------------------------------------------------------
# Pydantic Request Models
# ------------------------------------------------------------------------------


class IngestSnapshotRequest(BaseModel):
    workspace_id: str
    cluster_id: str
    node_id: Optional[str] = "node-01"
    cpu_utilization_pct: float = Field(..., ge=0.0, le=100.0)
    memory_utilization_pct: float = Field(..., ge=0.0, le=100.0)
    gpu_utilization_pct: Optional[float] = Field(0.0, ge=0.0, le=100.0)
    iops_read: Optional[float] = 0.0
    iops_write: Optional[float] = 0.0
    network_rx_mbps: Optional[float] = 0.0
    network_tx_mbps: Optional[float] = 0.0
    active_worker_count: Optional[int] = 1
    queue_depth_total: Optional[int] = 0
    token_throughput_per_sec: Optional[float] = 0.0
    custom_metrics: Optional[Dict[str, Any]] = Field(default_factory=dict)


class GenerateForecastRequest(BaseModel):
    workspace_id: str
    cluster_id: str
    metric_name: str = "cpu_utilization_pct"
    historical_values: Optional[List[float]] = None
    horizons: Optional[List[str]] = Field(default_factory=lambda: ["15m", "1h", "24h", "7d"])


class IngestQueueMetricRequest(BaseModel):
    workspace_id: str
    cluster_id: Optional[str] = "cluster-default"
    queue_name: str
    queue_depth: int = Field(..., ge=0)
    incoming_rate_tps: Optional[float] = 0.0
    processing_rate_tps: Optional[float] = 0.0
    avg_wait_time_ms: Optional[float] = 0.0
    p95_latency_ms: Optional[float] = 0.0
    dead_letter_count: Optional[int] = 0
    active_workers: Optional[int] = 1


class EvaluateScalingRequest(BaseModel):
    workspace_id: str
    cluster_id: str
    current_replicas: int = Field(..., ge=1)
    telemetry: Dict[str, Any]
    forecast: Optional[Dict[str, Any]] = None


class GenerateCostReportRequest(BaseModel):
    workspace_id: str
    cluster_id: str
    total_nodes: int = Field(..., ge=1)
    spot_nodes: int = Field(0, ge=0)
    idle_nodes: Optional[int] = 0
    billing_period: Optional[str] = "daily"


# ------------------------------------------------------------------------------
# REST Endpoints: Telemetry & Capacity Snapshots
# ------------------------------------------------------------------------------


@router.post("/snapshots", status_code=status.HTTP_201_CREATED)
async def ingest_snapshot(payload: IngestSnapshotRequest):
    """Ingest point-in-time infrastructure capacity and utilization snapshot."""
    snapshot_dict = payload.model_dump()
    result = _forecasting_engine.ingest_snapshot(snapshot_dict)
    return {"status": "ingested", "snapshot": result}


@router.get("/snapshots")
async def list_snapshots(
    workspace_id: str = Query(...),
    cluster_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Retrieve historical telemetry snapshots."""
    snapshots = _forecasting_engine.get_snapshots(workspace_id=workspace_id, cluster_id=cluster_id)
    return {"workspace_id": workspace_id, "count": len(snapshots[:limit]), "snapshots": snapshots[:limit]}


# ------------------------------------------------------------------------------
# REST Endpoints: Predictive ML Forecasting
# ------------------------------------------------------------------------------


@router.post("/forecasts/generate")
async def generate_capacity_forecast(payload: GenerateForecastRequest):
    """Generate multi-horizon ML capacity forecasts (15m, 1h, 24h, 7d)."""
    forecasts = _forecasting_engine.generate_multi_horizon_forecast(
        workspace_id=payload.workspace_id,
        cluster_id=payload.cluster_id,
        metric_name=payload.metric_name,
        historical_values=payload.historical_values,
        horizons=payload.horizons,
    )
    return {
        "workspace_id": payload.workspace_id,
        "cluster_id": payload.cluster_id,
        "metric_name": payload.metric_name,
        "forecasts": forecasts,
    }


@router.get("/forecasts")
async def get_forecasts(
    workspace_id: str = Query(...),
    cluster_id: Optional[str] = Query(None),
    metric_name: Optional[str] = Query(None),
    horizon: Optional[str] = Query(None),
):
    """Query generated load forecasts."""
    forecasts = _forecasting_engine.get_forecasts(
        workspace_id=workspace_id,
        cluster_id=cluster_id,
        metric_name=metric_name,
        horizon=horizon,
    )
    return {"workspace_id": workspace_id, "count": len(forecasts), "forecasts": forecasts}


# ------------------------------------------------------------------------------
# REST Endpoints: Queue Metrics & Anomaly Detection
# ------------------------------------------------------------------------------


@router.post("/queues/metrics", status_code=status.HTTP_201_CREATED)
async def ingest_queue_metrics(payload: IngestQueueMetricRequest):
    """Ingest queue metrics and evaluate for real-time latency or starvation anomalies."""
    metric_dict = payload.model_dump()
    _anomaly_detector.ingest_queue_metric(metric_dict)
    alerts = _anomaly_detector.detect_anomalies(
        workspace_id=payload.workspace_id,
        cluster_id=payload.cluster_id or "cluster-default",
        queue_name=payload.queue_name,
        current_metric=metric_dict,
    )
    return {"status": "processed", "metric": metric_dict, "alerts_triggered": alerts}


@router.get("/queues/health")
async def get_queue_health(workspace_id: str = Query(...), queue_name: str = Query(...)):
    """Retrieve queue health assessment (healthy, warning, critical)."""
    summary = _anomaly_detector.get_queue_health_summary(
        workspace_id=workspace_id, queue_name=queue_name
    )
    return {"workspace_id": workspace_id, "queue_name": queue_name, "health": summary}


@router.get("/anomalies/alerts")
async def get_anomaly_alerts(
    workspace_id: Optional[str] = Query(None),
    cluster_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
):
    """List active anomaly alerts."""
    alerts = _anomaly_detector.get_active_alerts(workspace_id=workspace_id, cluster_id=cluster_id)
    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    return {"count": len(alerts), "alerts": alerts}


@router.post("/anomalies/alerts/{alert_id}/resolve")
async def resolve_anomaly_alert(alert_id: str):
    """Mark an anomaly alert as resolved."""
    resolved = _anomaly_detector.resolve_alert(alert_id)
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert '{alert_id}' not found"
        )
    return {"status": "resolved", "alert": resolved}


# ------------------------------------------------------------------------------
# REST Endpoints: Capacity Auto-Scaling & Cost Reports
# ------------------------------------------------------------------------------


@router.post("/scaling/evaluate")
async def evaluate_scaling_recommendation(payload: EvaluateScalingRequest):
    """Evaluate current telemetry and predictive forecasts to issue scaling recommendations."""
    recommendation = _autoscaler.evaluate_scaling(
        workspace_id=payload.workspace_id,
        cluster_id=payload.cluster_id,
        current_replicas=payload.current_replicas,
        telemetry=payload.telemetry,
        forecast=payload.forecast,
    )
    return {
        "status": "evaluated",
        "action_required": recommendation is not None,
        "recommendation": recommendation,
    }


@router.get("/scaling/recommendations")
async def list_scaling_recommendations(workspace_id: Optional[str] = Query(None)):
    """List pending auto-scaling recommendations."""
    recs = _autoscaler.get_pending_recommendations(workspace_id=workspace_id)
    return {"count": len(recs), "recommendations": recs}


@router.post("/scaling/recommendations/{recommendation_id}/execute")
async def execute_scaling_recommendation(recommendation_id: str):
    """Execute a horizontal scaling recommendation."""
    executed = _autoscaler.execute_recommendation(recommendation_id)
    if not executed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation '{recommendation_id}' not found",
        )
    return {"status": "executed", "recommendation": executed}


@router.post("/cost/reports/generate")
async def generate_cost_optimization_report(payload: GenerateCostReportRequest):
    """Generate spot vs on-demand and idle capacity cost optimization report."""
    report = _autoscaler.generate_cost_report(
        workspace_id=payload.workspace_id,
        cluster_id=payload.cluster_id,
        total_nodes=payload.total_nodes,
        spot_nodes=payload.spot_nodes,
        idle_nodes=payload.idle_nodes or 0,
        billing_period=payload.billing_period or "daily",
    )
    return {"status": "generated", "report": report}


@router.get("/cost/reports")
async def list_cost_reports(
    workspace_id: Optional[str] = Query(None), cluster_id: Optional[str] = Query(None)
):
    """Retrieve cost optimization reports."""
    reports = _autoscaler.get_cost_reports(workspace_id=workspace_id, cluster_id=cluster_id)
    return {"count": len(reports), "reports": reports}
