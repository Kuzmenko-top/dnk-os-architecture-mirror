# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_forecast_accuracy_tracker"
# purpose: "Accuracy Evaluation & Model Tracking Service (MAE, RMSE, MAPE, R2 Score)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ForecastAccuracyTracker:
    """Evaluates forecast accuracy (MAE, RMSE, MAPE, R2 score) and tracks model performance."""

    def __init__(self):
        self._accuracy_records: List[Dict[str, Any]] = []

    def calculate_metrics(
        self,
        actuals: Optional[List[float]] = None,
        predictions: Optional[List[float]] = None,
        actual_values: Optional[List[float]] = None,
        predicted_values: Optional[List[float]] = None,
    ) -> Dict[str, float]:
        """Calculates MAE, RMSE, MAPE, and R2 score between actual and predicted series."""
        acts = actuals if actuals is not None else (actual_values or [])
        preds = predictions if predictions is not None else (predicted_values or [])

        n = min(len(acts), len(preds))
        if n == 0:
            return {"mae": 0.0, "rmse": 0.0, "mape": 0.0, "r2_score": 0.0, "sample_count": 0.0}

        errors = [acts[i] - preds[i] for i in range(n)]
        mae = sum(abs(e) for e in errors) / n
        rmse = math.sqrt(sum(e ** 2 for e in errors) / n)

        mape_elements = []
        for i in range(n):
            denom = abs(acts[i])
            if denom > 1e-4:
                mape_elements.append(abs(errors[i]) / denom)
            else:
                mape_elements.append(0.0)
        mape = (sum(mape_elements) / n) * 100.0

        y_mean = sum(acts[:n]) / n
        ss_tot = sum((y - y_mean) ** 2 for y in acts[:n])
        ss_res = sum(e ** 2 for e in errors)
        r2 = max(-1.0, min(1.0, 1.0 - (ss_res / ss_tot))) if ss_tot > 1e-9 else 1.0

        return {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "mape": round(mape, 2),
            "r2_score": round(r2, 4),
            "sample_count": float(n),
        }

    def record_and_evaluate(
        self,
        model_id: str,
        model_name: str,
        actuals: List[float],
        predictions: List[float],
        evaluation_window_hours: int = 24,
    ) -> Dict[str, Any]:
        """Calculates metrics and stores record in accuracy tracking store."""
        metrics = self.calculate_metrics(actuals=actuals, predictions=predictions)
        now = datetime.now(timezone.utc)
        record = {
            "id": str(uuid.uuid4()),
            "model_id": model_id,
            "model_name": model_name,
            "evaluation_time": now.isoformat(),
            "mae": metrics["mae"],
            "rmse": metrics["rmse"],
            "mape": metrics["mape"],
            "r2_score": metrics["r2_score"],
            "evaluation_window_hours": evaluation_window_hours,
        }
        self._accuracy_records.append(record)
        return record

    def get_accuracy_history(self, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if model_id:
            return [r for r in self._accuracy_records if r["model_id"] == model_id]
        return list(self._accuracy_records)
