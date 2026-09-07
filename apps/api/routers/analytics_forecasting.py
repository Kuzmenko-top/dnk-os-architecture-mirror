# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_analytics_forecasting"
# purpose: "FastAPI Router & WebSocket stream for Predictive Analytics & ML Forecasting (Snapshots, Capacity Planning, Accuracy Tracking)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from apps.api.middleware.tenant_authorization import require_tenant_and_workspace
from apps.api.services.predictive_forecasting_service import predictive_forecasting_service

router = APIRouter(prefix="/api/v1/analytics", tags=["Predictive Analytics & Forecasting"])


# ==========================
# Pydantic Schemas
# ==========================

class ForecastModelCreateRequest(BaseModel):
    workspace_id: str
    metric_type: str = Field(description="queue_depth, worker_count, latency_p95, error_rate")
    model_name: str = Field(description="linear, polynomial, holt_winters, arima, ensemble")
    model_params: Optional[Dict[str, Any]] = None
    training_window_days: int = 7
    retrain_frequency_hours: int = 6
    enabled: bool = True


class ForecastModelUpdateRequest(BaseModel):
    model_name: Optional[str] = None
    model_params: Optional[Dict[str, Any]] = None
    training_window_days: Optional[int] = None
    retrain_frequency_hours: Optional[int] = None
    enabled: Optional[bool] = None


# ==========================
# 1. Forecast Model Config Endpoints
# ==========================

@router.post("/forecast/models", status_code=status.HTTP_201_CREATED)
async def create_forecast_model(
    payload: ForecastModelCreateRequest,
):
    """Create a new forecast model configuration."""
    model = await predictive_forecasting_service.create_model(
        workspace_id=payload.workspace_id,
        metric_type=payload.metric_type,
        model_name=payload.model_name,
        model_params=payload.model_params,
        training_window_days=payload.training_window_days,
        retrain_frequency_hours=payload.retrain_frequency_hours,
        enabled=payload.enabled,
    )
    return {"status": "created", "model": model}


@router.get("/forecast/models")
async def list_forecast_models(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
):
    """List forecast model configurations."""
    models = await predictive_forecasting_service.list_models(workspace_id=workspace_id)
    return {"models": models, "total": len(models)}


@router.put("/forecast/models/{model_id}")
async def update_forecast_model(
    model_id: str,
    payload: ForecastModelUpdateRequest,
):
    """Update an existing forecast model configuration."""
    updated = await predictive_forecasting_service.update_model(
        model_id=model_id,
        updates=payload.model_dump(exclude_unset=True),
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model {model_id} not found")
    return {"status": "updated", "model": updated}


@router.delete("/forecast/models/{model_id}")
async def delete_forecast_model(model_id: str):
    """Delete a forecast model configuration."""
    success = await predictive_forecasting_service.delete_model(model_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Model {model_id} not found")
    return {"status": "deleted", "model_id": model_id}


@router.post("/forecast/models/{model_id}/train")
async def train_forecast_model(model_id: str):
    """Trigger manual retraining for a forecast model."""
    try:
        res = await predictive_forecasting_service.trigger_retrain(model_id)
        return {"status": "retrained", "result": res}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ==========================
# 2. Forecast Snapshots Endpoints
# ==========================

@router.get("/forecast/snapshots")
async def get_forecast_snapshots(
    workspace_id: Optional[str] = Query("ws-alpha-001", description="Workspace ID"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    limit: int = Query(100, ge=1, le=500),
):
    """Retrieve forecast snapshots with confidence intervals (p10, p50, p90)."""
    snapshots = await predictive_forecasting_service.get_snapshots(
        workspace_id=workspace_id,
        metric_type=metric_type,
        limit=limit,
    )
    return {"snapshots": snapshots, "total": len(snapshots)}


@router.get("/forecast/snapshots/latest")
async def get_latest_forecast_snapshots(
    workspace_id: str = Query("ws-alpha-001", description="Workspace ID"),
):
    """Retrieve the latest forecast snapshot per metric type."""
    latest = await predictive_forecasting_service.get_latest_snapshots(workspace_id=workspace_id)
    return {"latest_snapshots": latest}


@router.get("/forecast/snapshots/{metric_type}")
async def get_forecast_snapshots_by_type(
    metric_type: str,
    workspace_id: Optional[str] = Query("ws-alpha-001", description="Workspace ID"),
    limit: int = Query(50, ge=1, le=200),
):
    """Retrieve forecast snapshots for a specific metric type."""
    snapshots = await predictive_forecasting_service.get_snapshots(
        workspace_id=workspace_id,
        metric_type=metric_type,
        limit=limit,
    )
    return {"metric_type": metric_type, "snapshots": snapshots, "total": len(snapshots)}


# ==========================
# 3. Workload Predictions & Capacity Planning
# ==========================

@router.get("/workload/predictions")
async def get_workload_predictions(
    workspace_id: str = Query("ws-alpha-001", description="Workspace ID"),
    pool_id: Optional[str] = Query(None, description="Optional worker pool ID"),
    horizon_minutes: int = Query(60, ge=15, le=1440),
):
    """Retrieve workload forecasts and scaling triggers."""
    predictions = await predictive_forecasting_service.get_workload_predictions(
        workspace_id=workspace_id,
        pool_id=pool_id,
        forecast_horizon_minutes=horizon_minutes,
    )
    return predictions


@router.get("/workload/predictions/recommended")
async def get_recommended_capacity(
    workspace_id: str = Query("ws-alpha-001", description="Workspace ID"),
    pool_id: Optional[str] = Query(None, description="Optional worker pool ID"),
):
    """Retrieve recommended worker capacity based on peak forecasted queue depths."""
    recommended = await predictive_forecasting_service.get_recommended_capacity(
        workspace_id=workspace_id,
        pool_id=pool_id,
    )
    return recommended


# ==========================
# 4. Forecast Accuracy Metrics
# ==========================

@router.get("/forecast/accuracy")
async def get_forecast_accuracy(
    model_id: Optional[str] = Query(None, description="Optional model ID"),
):
    """Retrieve model evaluation metrics (MAE, RMSE, MAPE, R2 score)."""
    accuracy = await predictive_forecasting_service.get_accuracy_metrics(model_id=model_id)
    return {"accuracy_evaluations": accuracy, "total": len(accuracy)}


# ==========================
# 5. WebSocket Live Forecast Stream
# ==========================

@router.websocket("/forecast/live")
async def websocket_forecast_live(websocket: WebSocket):
    """WebSocket endpoint streaming real-time forecast updates and capacity triggers."""
    await websocket.accept()
    await predictive_forecasting_service.register_connection(websocket)
    try:
        # Send initial handshake state
        initial_payload = {
            "type": "INIT_FORECAST_STATE",
            "timestamp": "now",
            "status": "connected",
        }
        await websocket.send_text(json.dumps(initial_payload))

        while True:
            data = await websocket.receive_text()
            msg = json.loads(data) if data else {}
            if msg.get("action") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif msg.get("action") == "request_refresh":
                ws_id = msg.get("workspace_id", "ws-alpha-001")
                latest = await predictive_forecasting_service.get_latest_snapshots(ws_id)
                await websocket.send_text(json.dumps({
                    "type": "LATEST_FORECAST_UPDATE",
                    "data": latest,
                }))
    except WebSocketDisconnect:
        await predictive_forecasting_service.unregister_connection(websocket)
    except Exception:
        await predictive_forecasting_service.unregister_connection(websocket)
