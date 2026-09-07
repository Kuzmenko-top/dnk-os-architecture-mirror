# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-SERVICE-FORECASTING-ENGINE"
# purpose: "Predictive Capacity Forecasting Engine with Multi-Horizon ML and Quantile Modeling"
# canonical_source: true
# alters_files: ["apps/api/services/capacity_forecasting_engine.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-PHASE2"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import math
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple


class CapacityForecastingEngine:
    """Engine for time-series forecasting, trend extrapolation, and confidence quantile estimation."""

    def __init__(self):
        # In-memory storage for metric time series: {f"{cluster_id}:{metric_name}": [(timestamp, value), ...]}
        self._time_series: Dict[str, List[Tuple[datetime, float]]] = {}
        # In-memory generated forecasts: {forecast_id: forecast_dict}
        self._forecasts: Dict[str, Dict[str, Any]] = {}
        # In-memory snapshots: List of snapshot dicts
        self._snapshots: List[Dict[str, Any]] = []

    def _get_key(self, cluster_id: str, metric_name: str) -> str:
        return f"{cluster_id}:{metric_name}"

    def ingest_metric(
        self,
        cluster_id: str,
        metric_name: str,
        value: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Ingest a single metric data point."""
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        elif timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        key = self._get_key(cluster_id, metric_name)
        if key not in self._time_series:
            self._time_series[key] = []
        self._time_series[key].append((timestamp, float(value)))
        # Keep sorted by timestamp
        self._time_series[key].sort(key=lambda x: x[0])

    def ingest_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest all numeric metrics from a CapacitySnapshot dict."""
        cluster_id = snapshot.get("cluster_id", "default-cluster")
        raw_ts = snapshot.get("timestamp")
        if isinstance(raw_ts, str):
            try:
                ts = datetime.fromisoformat(raw_ts)
            except Exception:
                ts = datetime.now(timezone.utc)
        elif isinstance(raw_ts, datetime):
            ts = raw_ts
        else:
            ts = datetime.now(timezone.utc)

        snapshot_record = dict(snapshot)
        if "id" not in snapshot_record:
            snapshot_record["id"] = f"snap_{uuid.uuid4().hex[:12]}"
        if "timestamp" not in snapshot_record or not snapshot_record["timestamp"]:
            snapshot_record["timestamp"] = ts.isoformat()
        if "created_at" not in snapshot_record:
            snapshot_record["created_at"] = ts.isoformat()

        self._snapshots.append(snapshot_record)

        metrics = [
            ("cpu", snapshot.get("cpu_utilization_pct")),
            ("cpu_utilization_pct", snapshot.get("cpu_utilization_pct")),
            ("memory", snapshot.get("memory_utilization_pct")),
            ("memory_utilization_pct", snapshot.get("memory_utilization_pct")),
            ("gpu", snapshot.get("gpu_utilization_pct")),
            ("gpu_utilization_pct", snapshot.get("gpu_utilization_pct")),
            ("network_iops", snapshot.get("network_iops_mbps")),
            ("active_agents", snapshot.get("active_agents_count")),
            ("queue_depth", snapshot.get("queue_depth") or snapshot.get("queue_depth_total")),
            ("token_throughput", snapshot.get("token_throughput_tps") or snapshot.get("token_throughput_per_sec")),
        ]

        for metric_name, val in metrics:
            if val is not None:
                self.ingest_metric(cluster_id, metric_name, float(val), ts)

        return snapshot_record

    def get_snapshots(
        self, workspace_id: Optional[str] = None, cluster_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve stored snapshots filtered by workspace and cluster."""
        snaps = list(self._snapshots)
        if workspace_id:
            snaps = [s for s in snaps if s.get("workspace_id") == workspace_id]
        if cluster_id:
            snaps = [s for s in snaps if s.get("cluster_id") == cluster_id]
        return sorted(snaps, key=lambda s: s.get("timestamp", ""), reverse=True)

    def get_historical_series(
        self, cluster_id: str, metric_name: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Retrieve recent historical data points for a metric."""
        key = self._get_key(cluster_id, metric_name)
        series = self._time_series.get(key, [])
        selected = series[-limit:] if limit > 0 else series
        return [{"timestamp": dt.isoformat(), "value": val} for dt, val in selected]

    def _double_exponential_smoothing(
        self, series: List[float], alpha: float = 0.3, beta: float = 0.1, steps_ahead: int = 1
    ) -> Tuple[List[float], float]:
        """Holt's Linear Trend / Double Exponential Smoothing."""
        if not series:
            return ([0.0] * steps_ahead, 0.0)
        if len(series) == 1:
            return ([series[0]] * steps_ahead, 0.0)

        level = series[0]
        trend = series[1] - series[0]

        residuals = []
        for i in range(1, len(series)):
            val = series[i]
            prev_level = level
            pred = level + trend
            residuals.append(val - pred)

            level = alpha * val + (1.0 - alpha) * (prev_level + trend)
            trend = beta * (level - prev_level) + (1.0 - beta) * trend

        # Generate future steps
        forecasts = []
        for m in range(1, steps_ahead + 1):
            pred_val = max(0.0, level + m * trend)
            forecasts.append(pred_val)

        # Compute standard error of residuals
        if residuals:
            variance = sum(r * r for r in residuals) / len(residuals)
            std_err = math.sqrt(variance)
        else:
            std_err = 0.0

        return (forecasts, std_err)

    def _linear_regression_forecast(
        self, series: List[float], steps_ahead: int = 1
    ) -> Tuple[List[float], float, float]:
        """Linear trend extrapolation returning (predictions, std_err, r_squared)."""
        n = len(series)
        if n < 2:
            val = series[0] if n == 1 else 0.0
            return ([val] * steps_ahead, 0.0, 1.0)

        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = sum(series) / n

        numerator = sum((x_vals[i] - x_mean) * (series[i] - y_mean) for i in range(n))
        denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0.0
        intercept = y_mean - slope * x_mean

        residuals = [series[i] - (intercept + slope * x_vals[i]) for i in range(n)]
        ss_res = sum(r * r for r in residuals)
        ss_tot = sum((y - y_mean) ** 2 for y in series)
        r_squared = max(0.0, min(1.0, 1.0 - (ss_res / ss_tot))) if ss_tot > 0 else 1.0

        std_err = math.sqrt(ss_res / n) if n > 0 else 0.0

        predictions = [max(0.0, intercept + slope * (n + m)) for m in range(steps_ahead)]
        return (predictions, std_err, r_squared)

    def evaluate_model_accuracy(
        self, actuals: List[float], predictions: List[float]
    ) -> Dict[str, float]:
        """Evaluate goodness-of-fit metrics between actual and predicted sequences."""
        if not actuals or not predictions or len(actuals) != len(predictions):
            return {"mae": 0.0, "mse": 0.0, "mape": 0.0, "r2": 0.0}

        n = len(actuals)
        errors = [actuals[i] - predictions[i] for i in range(n)]
        mae = sum(abs(e) for e in errors) / n
        mse = sum(e * e for e in errors) / n

        # MAPE
        non_zero_mape = [
            abs(errors[i] / actuals[i]) for i in range(n) if actuals[i] != 0
        ]
        mape = (sum(non_zero_mape) / len(non_zero_mape) * 100.0) if non_zero_mape else 0.0

        # R-squared
        mean_act = sum(actuals) / n
        ss_tot = sum((y - mean_act) ** 2 for y in actuals)
        ss_res = sum(e * e for e in errors)
        r2 = max(0.0, min(1.0, 1.0 - (ss_res / ss_tot))) if ss_tot > 0 else 1.0

        return {
            "mae": round(mae, 4),
            "mse": round(mse, 4),
            "mape": round(mape, 2),
            "r2": round(r2, 4),
        }

    def generate_forecast(
        self,
        workspace_id: str,
        cluster_id: str,
        metric_name: str,
        forecast_horizon: str = "1h",
        model_algorithm: str = "holt_winters",
    ) -> Dict[str, Any]:
        """Generate multi-step forecast with p50, p90, p99 quantiles and confidence metrics."""
        key = self._get_key(cluster_id, metric_name)
        data = self._time_series.get(key, [])

        horizon_configs = {
            "15m": {"steps": 15, "step_delta": timedelta(minutes=1), "valid_hours": 0.5},
            "1h": {"steps": 12, "step_delta": timedelta(minutes=5), "valid_hours": 1.0},
            "24h": {"steps": 24, "step_delta": timedelta(hours=1), "valid_hours": 24.0},
            "7d": {"steps": 14, "step_delta": timedelta(hours=12), "valid_hours": 168.0},
        }

        cfg = horizon_configs.get(forecast_horizon, horizon_configs["1h"])
        steps = cfg["steps"]
        step_delta = cfg["step_delta"]
        valid_duration = timedelta(hours=cfg["valid_hours"])

        now_utc = datetime.now(timezone.utc)
        series_values = [pt[1] for pt in data]

        if not series_values:
            # Baseline dummy fallback if no data ingested yet
            series_values = [50.0]

        if model_algorithm == "linear_regression":
            pred_series, std_err, r2 = self._linear_regression_forecast(series_values, steps_ahead=steps)
            confidence = max(0.70, min(0.99, r2 if len(series_values) >= 5 else 0.85))
        else:
            # Holt-Winters / Double Exponential Smoothing by default
            pred_series, std_err = self._double_exponential_smoothing(series_values, alpha=0.35, beta=0.15, steps_ahead=steps)
            confidence = min(0.98, max(0.65, 0.95 - (std_err / (max(series_values) + 1e-6))))

        # Quantile multipliers for normal distribution (p50: 0, p90: 1.282, p99: 2.326)
        z90 = 1.282
        z99 = 2.326

        forecast_points = []
        last_timestamp = data[-1][0] if data else now_utc

        for idx, p50 in enumerate(pred_series):
            # Variance increases slightly with forecast distance
            step_uncertainty = std_err * math.sqrt(1.0 + 0.1 * idx)
            p90 = max(p50, p50 + z90 * step_uncertainty)
            p99 = max(p90, p50 + z99 * step_uncertainty)

            pt_ts = last_timestamp + (idx + 1) * step_delta
            forecast_points.append({
                "step": idx + 1,
                "timestamp": pt_ts.isoformat(),
                "p50": round(p50, 2),
                "p90": round(p90, 2),
                "p99": round(p99, 2),
            })

        # Summary aggregate values
        agg_p50 = round(sum(pt["p50"] for pt in forecast_points) / len(forecast_points), 2)
        agg_p90 = round(max(pt["p90"] for pt in forecast_points), 2)
        agg_p99 = round(max(pt["p99"] for pt in forecast_points), 2)

        forecast_id = f"fc_{uuid.uuid4().hex[:12]}"
        forecast_record = {
            "id": forecast_id,
            "workspace_id": workspace_id,
            "cluster_id": cluster_id,
            "metric_name": metric_name,
            "forecast_horizon": forecast_horizon,
            "predicted_value_p50": agg_p50,
            "predicted_value_p90": agg_p90,
            "predicted_value_p99": agg_p99,
            "confidence_score": round(confidence, 4),
            "model_algorithm": model_algorithm,
            "forecast_series": forecast_points,
            "forecast_generated_at": now_utc.isoformat(),
            "valid_until": (now_utc + valid_duration).isoformat(),
            "created_at": now_utc.isoformat(),
        }

        self._forecasts[forecast_id] = forecast_record
        return forecast_record

    def generate_multi_horizon_forecast(
        self,
        workspace_id: str,
        cluster_id: str,
        metric_name: str,
        model_algorithm: str = "holt_winters",
        historical_values: Optional[List[float]] = None,
        horizons: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Generate forecasts across standard horizons: 15m, 1h, 24h, 7d."""
        if historical_values:
            now_utc = datetime.now(timezone.utc)
            for idx, val in enumerate(historical_values):
                ts = now_utc - timedelta(minutes=len(historical_values) - idx)
                self.ingest_metric(cluster_id, metric_name, val, ts)

        target_horizons = horizons or ["15m", "1h", "24h", "7d"]
        results = {}
        for h in target_horizons:
            results[h] = self.generate_forecast(
                workspace_id=workspace_id,
                cluster_id=cluster_id,
                metric_name=metric_name,
                forecast_horizon=h,
                model_algorithm=model_algorithm,
            )
        return results

    def get_forecast_by_id(self, forecast_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a cached forecast record by its ID."""
        return self._forecasts.get(forecast_id)

    def get_forecasts(
        self,
        workspace_id: Optional[str] = None,
        cluster_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        horizon: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve generated forecast records filtered by criteria."""
        recs = list(self._forecasts.values())
        if workspace_id:
            recs = [r for r in recs if r.get("workspace_id") == workspace_id]
        if cluster_id:
            recs = [r for r in recs if r.get("cluster_id") == cluster_id]
        if metric_name:
            recs = [r for r in recs if r.get("metric_name") == metric_name]
        if horizon:
            recs = [r for r in recs if r.get("forecast_horizon") == horizon]
        return sorted(recs, key=lambda x: x.get("forecast_generated_at", ""), reverse=True)
