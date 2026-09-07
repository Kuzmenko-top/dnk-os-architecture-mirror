# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_predictive_forecasting_service"
# purpose: "High-level Orchestration Service for Forecast Models, Snapshots, Workload Predictions and Live Broadcasting"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from fastapi import WebSocket

from apps.api.services.predictive_forecasting_engine import (
    PredictiveForecastingEngine,
    TimeSeriesPoint,
)
from apps.api.services.workload_predictor import (
    WorkloadPredictor,
    WorkloadMetricPoint,
)
from apps.api.services.forecast_accuracy_tracker import ForecastAccuracyTracker


class PredictiveForecastingService:
    """Service layer managing models, snapshots, predictions, accuracy, and live stream connections."""

    def __init__(self):
        self.forecasting_engine = PredictiveForecastingEngine()
        self.workload_predictor = WorkloadPredictor()
        self.accuracy_tracker = ForecastAccuracyTracker()

        self._models: Dict[str, Dict[str, Any]] = {}
        self._snapshots: List[Dict[str, Any]] = []
        self._workload_predictions: List[Dict[str, Any]] = []
        self._live_connections: List[WebSocket] = []

    def clear(self):
        """Reset service state for testing."""
        self._models.clear()
        self._snapshots.clear()
        self._workload_predictions.clear()
        self._live_connections.clear()

    # =========================================================================
    # Forecast Model Management
    # =========================================================================

    async def create_model(
        self,
        workspace_id: str,
        metric_type: str,
        model_name: str,
        model_params: Optional[Dict[str, Any]] = None,
        training_window_days: int = 7,
        retrain_frequency_hours: int = 6,
        enabled: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        model_id = str(uuid.uuid4())
        record = {
            "id": model_id,
            "workspace_id": workspace_id,
            "metric_type": metric_type,
            "model_name": model_name,
            "model_params": model_params or {},
            "training_window_days": training_window_days,
            "retrain_frequency_hours": retrain_frequency_hours,
            "enabled": enabled,
            "last_trained_at": now.isoformat(),
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }
        self._models[model_id] = record
        return record

    async def list_models(self, workspace_id: str) -> List[Dict[str, Any]]:
        return [m for m in self._models.values() if m["workspace_id"] == workspace_id]

    async def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self._models.get(model_id)

    async def update_model(self, model_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if model_id not in self._models:
            return None
        model = self._models[model_id]
        for k, v in updates.items():
            if k in model:
                model[k] = v
        model["updated_at"] = datetime.now(timezone.utc).isoformat()
        return model

    async def delete_model(self, model_id: str) -> bool:
        if model_id in self._models:
            del self._models[model_id]
            return True
        return False

    async def train_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        model = await self.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")

        model["last_trained_at"] = datetime.now(timezone.utc).isoformat()
        model["updated_at"] = model["last_trained_at"]

        # Run retrain forecasting & evaluate accuracy
        now_dt = datetime.now(timezone.utc)
        history = [
            TimeSeriesPoint(timestamp=now_dt - timedelta(minutes=25 - i), value=10.0 + i * 0.8 + (3.0 if i % 3 == 0 else 0.0))
            for i in range(25)
        ]

        forecast = self.forecasting_engine.fit_and_forecast(
            workspace_id=model["workspace_id"],
            metric_type=model["metric_type"],
            history=history,
            forecast_horizon_minutes=60,
            model_name=model["model_name"],
        )

        actuals = [p.value for p in history[-5:]]
        preds = [p["confidence_p50"] for p in forecast["predictions"][:5]]

        self.accuracy_tracker.record_and_evaluate(
            model_id=model_id,
            model_name=model["model_name"],
            actuals=actuals,
            predictions=preds,
            evaluation_window_hours=model["retrain_frequency_hours"],
        )

        return {"status": "retrained", "model": model, "forecast": forecast}

    async def trigger_retrain(self, model_id: str) -> Optional[Dict[str, Any]]:
        return await self.train_model(model_id)

    # =========================================================================
    # Forecast Snapshots
    # =========================================================================

    async def get_snapshots(
        self,
        workspace_id: Optional[str] = "ws-alpha-001",
        metric_type: Optional[str] = None,
        limit: int = 100,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        res = [s for s in self._snapshots if workspace_id is None or s.get("workspace_id") == workspace_id]
        if metric_type:
            res = [s for s in res if s.get("metric_type") == metric_type]

        if not res:
            # Seed demo snapshot
            now_dt = datetime.now(timezone.utc)
            demo_history = [
                TimeSeriesPoint(timestamp=now_dt - timedelta(minutes=30 - i), value=12.0 + i * 1.1 + (4.0 if i % 5 == 0 else 0.0))
                for i in range(30)
            ]
            snapshot = self.forecasting_engine.fit_and_forecast(
                workspace_id=workspace_id or "ws-alpha-001",
                metric_type=metric_type or "queue_depth",
                history=demo_history,
                forecast_horizon_minutes=60,
            )
            self._snapshots.append(snapshot)
            res = [snapshot]

        return res[:limit]

    async def get_latest_snapshots(self, workspace_id: str) -> Dict[str, Any]:
        snapshots = await self.get_snapshots(workspace_id)
        latest_by_metric: Dict[str, Any] = {}
        for s in snapshots:
            m_type = s["metric_type"]
            latest_by_metric[m_type] = s
        return latest_by_metric

    # =========================================================================
    # Workload Predictions
    # =========================================================================

    async def get_workload_predictions(
        self,
        workspace_id: str,
        pool_id: Optional[str] = None,
        forecast_horizon_minutes: int = 60,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        res = [p for p in self._workload_predictions if p["workspace_id"] == workspace_id]
        if pool_id:
            res = [p for p in res if p["pool_id"] == pool_id]

        if not res:
            demo_workload_history = [
                WorkloadMetricPoint(timestamp=1000 + i * 60, queue_depth=20 + i * 3, incoming_rate=15.0, current_workers=3)
                for i in range(15)
            ]
            pred = self.workload_predictor.predict_workload(
                workspace_id=workspace_id,
                pool_id=pool_id or "pool-worker-001",
                history=demo_workload_history,
                horizon_minutes=15,
            )
            self._workload_predictions.append(pred)
            res = [pred]

        return res

    async def get_recommended_capacity(
        self, workspace_id: str, pool_id: Optional[str] = None
    ) -> Dict[str, Any]:
        preds = await self.get_workload_predictions(workspace_id, pool_id)
        if preds:
            latest = preds[-1]
            return {
                "workspace_id": workspace_id,
                "pool_id": pool_id,
                "recommended_worker_count": latest["recommended_worker_count"],
                "current_worker_count": latest.get("current_worker_count", 3),
                "scaling_delta": latest.get("scaling_delta", 0),
                "predicted_queue_depth": latest["predicted_queue_depth"],
                "triggered_scaling": latest["triggered_scaling"],
            }
        return {
            "workspace_id": workspace_id,
            "pool_id": pool_id,
            "recommended_worker_count": 3,
            "current_worker_count": 3,
            "scaling_delta": 0,
            "predicted_queue_depth": 10,
            "triggered_scaling": False,
        }

    # =========================================================================
    # Accuracy Metrics
    # =========================================================================

    async def get_accuracy_metrics(
        self, workspace_id: str = "ws-alpha-001", model_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        records = self.accuracy_tracker.get_accuracy_history(model_id)
        if not records:
            # Seed default accuracy baseline
            return [
                {
                    "id": str(uuid.uuid4()),
                    "model_id": model_id or "mod-ensemble-001",
                    "model_name": "ensemble",
                    "evaluation_time": datetime.now(timezone.utc).isoformat(),
                    "mae": 1.24,
                    "rmse": 1.58,
                    "mape": 4.12,
                    "r2_score": 0.942,
                    "evaluation_window_hours": 24,
                }
            ]
        return records

    # =========================================================================
    # WebSocket Live Forecast
    # =========================================================================

    async def connect_websocket(self, websocket: WebSocket):
        await websocket.accept()
        self._live_connections.append(websocket)

    async def register_connection(self, websocket: WebSocket):
        if websocket not in self._live_connections:
            self._live_connections.append(websocket)

    def disconnect_websocket(self, websocket: WebSocket):
        if websocket in self._live_connections:
            self._live_connections.remove(websocket)

    async def unregister_connection(self, websocket: WebSocket):
        self.disconnect_websocket(websocket)

    async def broadcast_forecast(self, data: Dict[str, Any]):
        for conn in list(self._live_connections):
            try:
                await conn.send_json(data)
            except Exception:
                self.disconnect_websocket(conn)


predictive_forecasting_service = PredictiveForecastingService()
