# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_predictive_forecasting_engine"
# purpose: "Time-Series Feature Engineering, Multi-Model Trend & Seasonal Forecasting Engine (Linear, Poly, Holt-Winters, ARIMA, Ensemble, p10/p50/p90 Confidence Intervals)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union


# =====================================================================
# 1. Feature Engineering
# =====================================================================

@dataclass
class TimeSeriesPoint:
    timestamp: datetime
    value: float


class TimeSeriesFeatureEngineer:
    """Extracts lag features, rolling statistics, and cyclical seasonality encodings."""

    @staticmethod
    def extract_cyclical_features(dt: datetime) -> Dict[str, float]:
        """Calculates sine/cosine components for hour of day, day of week, and day of year."""
        hour = dt.hour + dt.minute / 60.0
        hour_rad = 2.0 * math.pi * hour / 24.0

        dow = dt.weekday() + (dt.hour / 24.0)
        dow_rad = 2.0 * math.pi * dow / 7.0

        doy = dt.timetuple().tm_yday
        doy_rad = 2.0 * math.pi * doy / 365.25

        return {
            "hour_sin": math.sin(hour_rad),
            "hour_cos": math.cos(hour_rad),
            "day_of_week_sin": math.sin(dow_rad),
            "day_of_week_cos": math.cos(dow_rad),
            "day_of_year_sin": math.sin(doy_rad),
            "day_of_year_cos": math.cos(doy_rad),
        }

    @staticmethod
    def extract_lag_features(values: List[float], lags: List[int]) -> Dict[str, Optional[float]]:
        """Extracts values at specified lag indices from the end of the series."""
        n = len(values)
        res = {}
        for lag in lags:
            if lag <= n and lag > 0:
                res[f"lag_{lag}"] = float(values[-lag])
            else:
                res[f"lag_{lag}"] = None
        return res

    @staticmethod
    def extract_rolling_stats(values: List[float], window: int) -> Dict[str, float]:
        """Extracts rolling mean, standard deviation, min, and max for the given window."""
        if not values:
            return {"rolling_mean": 0.0, "rolling_std": 0.0, "rolling_min": 0.0, "rolling_max": 0.0}
        
        slice_vals = values[-window:] if len(values) >= window else values
        n = len(slice_vals)
        mean_val = sum(slice_vals) / n
        if n > 1:
            variance = sum((x - mean_val) ** 2 for x in slice_vals) / (n - 1)
            std_val = math.sqrt(max(0.0, variance))
        else:
            std_val = 0.0

        return {
            "rolling_mean": mean_val,
            "rolling_std": std_val,
            "rolling_min": min(slice_vals),
            "rolling_max": max(slice_vals),
        }


# =====================================================================
# 2. Forecasting Models
# =====================================================================

class LinearTrendModel:
    """Ordinary Least Squares Linear Regression for Time-Series Trend."""

    def __init__(self):
        self.slope: float = 0.0
        self.intercept: float = 0.0
        self.r2_score: float = 0.0
        self.residual_std: float = 0.0
        self.n_samples: int = 0

    def fit(self, values: List[float]) -> "LinearTrendModel":
        n = len(values)
        self.n_samples = n
        if n < 2:
            self.slope = 0.0
            self.intercept = float(values[0]) if n == 1 else 0.0
            self.r2_score = 1.0
            self.residual_std = 0.0
            return self

        x = list(range(n))
        x_mean = (n - 1) / 2.0
        y_mean = sum(values) / n

        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            self.slope = 0.0
        else:
            self.slope = numerator / denominator
        self.intercept = y_mean - self.slope * x_mean

        # Residuals and R2
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        residuals = [values[i] - (self.intercept + self.slope * i) for i in range(n)]
        ss_res = sum(r ** 2 for r in residuals)

        self.r2_score = max(0.0, 1.0 - (ss_res / ss_tot)) if ss_tot > 1e-9 else 1.0
        self.residual_std = math.sqrt(ss_res / max(1, n - 2))
        return self

    def predict(self, steps_ahead: int) -> List[float]:
        """Predicts future values starting from step (n_samples)."""
        predictions = []
        for step in range(1, steps_ahead + 1):
            t = self.n_samples - 1 + step
            predictions.append(self.intercept + self.slope * t)
        return predictions


class PolynomialTrendModel:
    """Polynomial Curve Fitting with optimal degree selection (1 to max_degree)."""

    def __init__(self, degree: int = 2, auto_degree: bool = False, max_degree: int = 4):
        self.degree = degree
        self.auto_degree = auto_degree
        self.max_degree = max_degree
        self.coefficients: List[float] = []
        self.r2_score: float = 0.0
        self.residual_std: float = 0.0
        self.n_samples: int = 0

    def _fit_degree(self, values: List[float], deg: int) -> Tuple[List[float], float, float]:
        """Fits a polynomial of specific degree using Gaussian elimination on normal equations."""
        n = len(values)
        if n <= deg:
            deg = max(1, n - 1)

        # Build Vandermonde normal equations X^T X a = X^T y
        m = deg + 1
        A = [[0.0] * m for _ in range(m)]
        b = [0.0] * m

        # Precompute power sums of x
        powers = [0.0] * (2 * deg + 1)
        for p in range(2 * deg + 1):
            powers[p] = sum(float(i ** p) for i in range(n))

        for row in range(m):
            for col in range(m):
                A[row][col] = powers[row + col]
            b[row] = sum(float(values[i] * (i ** row)) for i in range(n))

        # Solve system A * coeffs = b using Gaussian elimination with partial pivoting
        coeffs = self._solve_linear_system(A, b)

        # Calculate R2 and residual std
        y_mean = sum(values) / n
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        residuals = []
        for i in range(n):
            y_pred = sum(coeffs[p] * (i ** p) for p in range(m))
            residuals.append(values[i] - y_pred)
        ss_res = sum(r ** 2 for r in residuals)
        r2 = max(0.0, 1.0 - (ss_res / ss_tot)) if ss_tot > 1e-9 else 1.0
        std_res = math.sqrt(ss_res / max(1, n - m))

        return coeffs, r2, std_res

    def _solve_linear_system(self, A: List[List[float]], b: List[float]) -> List[float]:
        """Solves A x = b using Gaussian elimination with partial pivoting."""
        n = len(b)
        # Augmented matrix
        M = [row[:] + [b[i]] for i, row in enumerate(A)]

        for i in range(n):
            # Pivot
            max_row = i
            max_val = abs(M[i][i])
            for r in range(i + 1, n):
                if abs(M[r][i]) > max_val:
                    max_val = abs(M[r][i])
                    max_row = r
            if max_row != i:
                M[i], M[max_row] = M[max_row], M[i]

            pivot = M[i][i]
            if abs(pivot) < 1e-12:
                pivot = 1e-12

            for c in range(i, n + 1):
                M[i][c] /= pivot

            for r in range(n):
                if r != i:
                    factor = M[r][i]
                    for c in range(i, n + 1):
                        M[r][c] -= factor * M[i][c]

        return [M[i][n] for i in range(n)]

    def fit(self, values: List[float]) -> "PolynomialTrendModel":
        n = len(values)
        self.n_samples = n
        if n < 3:
            linear = LinearTrendModel().fit(values)
            self.coefficients = [linear.intercept, linear.slope]
            self.r2_score = linear.r2_score
            self.residual_std = linear.residual_std
            return self

        if not self.auto_degree:
            deg = min(self.degree, max(1, n - 2))
            self.coefficients, self.r2_score, self.residual_std = self._fit_degree(values, deg)
        else:
            # Auto-degree selection via BIC penalty: n * ln(MSE) + k * ln(n)
            best_deg = 1
            best_bic = float("inf")
            best_res = None

            for deg in range(1, min(self.max_degree + 1, n - 1)):
                coeffs, r2, std_res = self._fit_degree(values, deg)
                mse = max(1e-6, std_res ** 2)
                k = deg + 1
                bic = n * math.log(mse) + k * math.log(n)
                if bic < best_bic:
                    best_bic = bic
                    best_deg = deg
                    best_res = (coeffs, r2, std_res)

            if best_res is not None:
                self.degree = best_deg
                self.coefficients, self.r2_score, self.residual_std = best_res
            else:
                self.coefficients, self.r2_score, self.residual_std = self._fit_degree(values, 1)

        return self

    def predict(self, steps_ahead: int) -> List[float]:
        predictions = []
        for step in range(1, steps_ahead + 1):
            t = self.n_samples - 1 + step
            val = sum(self.coefficients[p] * (t ** p) for p in range(len(self.coefficients)))
            predictions.append(val)
        return predictions


class HoltWintersModel:
    """Triple Exponential Smoothing (Holt-Winters) for Level, Trend, and Seasonality."""

    def __init__(
        self,
        season_length: int = 12,
        alpha: float = 0.3,
        beta: float = 0.1,
        gamma: float = 0.2,
        seasonal_type: str = "additive",
    ):
        self.season_length = max(2, season_length)
        self.alpha = min(max(alpha, 0.01), 0.99)
        self.beta = min(max(beta, 0.01), 0.99)
        self.gamma = min(max(gamma, 0.01), 0.99)
        self.seasonal_type = seasonal_type.lower()
        self.level: float = 0.0
        self.trend: float = 0.0
        self.seasonals: List[float] = []
        self.residual_std: float = 0.0
        self.n_samples: int = 0

    def fit(self, values: List[float]) -> "HoltWintersModel":
        n = len(values)
        self.n_samples = n
        m = self.season_length

        if n < 2 * m:
            # Fallback if not enough seasonal cycles
            m = max(1, n // 2)
            self.season_length = m

        # Initialize level and trend
        self.level = sum(values[:m]) / m if m > 0 else (values[0] if n > 0 else 0.0)
        if n >= 2 * m and m > 0:
            self.trend = (sum(values[m:2 * m]) / m - sum(values[:m]) / m) / m
        else:
            self.trend = (values[-1] - values[0]) / max(1, n - 1) if n > 1 else 0.0

        # Initial seasonal indices
        self.seasonals = [0.0] * m
        for i in range(m):
            if i < n:
                if self.seasonal_type == "multiplicative" and abs(self.level) > 1e-4:
                    self.seasonals[i] = values[i] / self.level
                else:
                    self.seasonals[i] = values[i] - self.level

        # Run filtering loop
        levels = [self.level]
        trends = [self.trend]
        residuals = []

        for i in range(n):
            val = values[i]
            season_idx = i % m
            prev_level = levels[-1]
            prev_trend = trends[-1]
            prev_season = self.seasonals[season_idx]

            if self.seasonal_type == "multiplicative":
                s_factor = prev_season if abs(prev_season) > 1e-4 else 1.0
                curr_level = self.alpha * (val / s_factor) + (1 - self.alpha) * (prev_level + prev_trend)
                curr_trend = self.beta * (curr_level - prev_level) + (1 - self.beta) * prev_trend
                curr_season = self.gamma * (val / (curr_level if abs(curr_level) > 1e-4 else 1.0)) + (1 - self.gamma) * prev_season
                pred = (prev_level + prev_trend) * s_factor
            else:
                curr_level = self.alpha * (val - prev_season) + (1 - self.alpha) * (prev_level + prev_trend)
                curr_trend = self.beta * (curr_level - prev_level) + (1 - self.beta) * prev_trend
                curr_season = self.gamma * (val - curr_level) + (1 - self.gamma) * prev_season
                pred = prev_level + prev_trend + prev_season

            residuals.append(val - pred)
            levels.append(curr_level)
            trends.append(curr_trend)
            self.seasonals[season_idx] = curr_season

        self.level = levels[-1]
        self.trend = trends[-1]
        variance = sum(r ** 2 for r in residuals) / max(1, n)
        self.residual_std = math.sqrt(variance)
        return self

    def predict(self, steps_ahead: int) -> List[float]:
        predictions = []
        m = self.season_length
        for h in range(1, steps_ahead + 1):
            season_idx = (self.n_samples + h - 1) % m
            seasonal_val = self.seasonals[season_idx] if self.seasonals else 0.0

            if self.seasonal_type == "multiplicative":
                val = (self.level + h * self.trend) * (seasonal_val if seasonal_val != 0 else 1.0)
            else:
                val = self.level + h * self.trend + seasonal_val
            predictions.append(val)
        return predictions


class ARIMABaselineModel:
    """Auto-Regressive Integrated Moving Average (ARIMA) baseline model (p, d, q)."""

    def __init__(self, p: int = 2, d: int = 1, q: int = 1):
        self.p = max(0, p)
        self.d = max(0, min(d, 2))
        self.q = max(0, q)
        self.ar_coeffs: List[float] = []
        self.ma_coeffs: List[float] = []
        self.history: List[float] = []
        self.diff_history: List[float] = []
        self.residuals: List[float] = []
        self.residual_std: float = 0.0

    def _difference(self, data: List[float], order: int) -> List[float]:
        current = list(data)
        for _ in range(order):
            if len(current) < 2:
                break
            current = [current[i] - current[i - 1] for i in range(1, len(current))]
        return current

    def fit(self, values: List[float]) -> "ARIMABaselineModel":
        self.history = list(values)
        n = len(values)
        if n < self.p + self.d + 2:
            self.ar_coeffs = [0.5] if self.p > 0 else []
            self.ma_coeffs = [0.1] if self.q > 0 else []
            self.residual_std = 1.0
            return self

        diff_series = self._difference(values, self.d)
        self.diff_history = diff_series
        nd = len(diff_series)

        if nd <= self.p:
            self.ar_coeffs = [0.5] if self.p > 0 else []
            self.residual_std = 1.0
            return self

        # OLS estimation of AR parameters
        X = []
        Y = []
        for i in range(self.p, nd):
            row = [diff_series[i - j - 1] for j in range(self.p)]
            X.append(row)
            Y.append(diff_series[i])

        # Normal equations (X^T X) beta = X^T Y
        m = self.p
        XtX = [[0.0] * m for _ in range(m)]
        XtY = [0.0] * m

        for i in range(len(X)):
            for r in range(m):
                for c in range(m):
                    XtX[r][c] += X[i][r] * X[i][c]
                XtY[r] += X[i][r] * Y[i]

        # Regularize diagonal
        for r in range(m):
            XtX[r][r] += 1e-4

        # Solve system
        poly = PolynomialTrendModel()
        self.ar_coeffs = poly._solve_linear_system(XtX, XtY)

        # Estimate residuals
        self.residuals = []
        for i in range(len(X)):
            y_hat = sum(self.ar_coeffs[j] * X[i][j] for j in range(m))
            self.residuals.append(Y[i] - y_hat)

        # Simple MA(q) estimation from residuals
        self.ma_coeffs = [0.1] * self.q

        variance = sum(r ** 2 for r in self.residuals) / max(1, len(self.residuals)) if self.residuals else 1.0
        self.residual_std = math.sqrt(variance)
        return self

    def predict(self, steps_ahead: int) -> List[float]:
        """Multi-step autoregressive roll-forward prediction."""
        if not self.history:
            return [0.0] * steps_ahead

        diff_forecast = []
        recent_diffs = list(self.diff_history) if self.diff_history else [0.0]
        recent_resids = list(self.residuals) if self.residuals else [0.0]

        for _ in range(steps_ahead):
            val = 0.0
            # AR term
            for j in range(self.p):
                idx = len(recent_diffs) - 1 - j
                if idx >= 0:
                    val += self.ar_coeffs[j] * recent_diffs[idx]
            # MA term
            for k in range(self.q):
                if k < len(recent_resids):
                    val += self.ma_coeffs[k] * recent_resids[-(k + 1)]

            diff_forecast.append(val)
            recent_diffs.append(val)
            recent_resids.append(0.0)

        # Invert differencing
        if self.d == 0:
            return diff_forecast

        predictions = []
        last_val = self.history[-1]
        for delta in diff_forecast:
            last_val += delta
            predictions.append(last_val)

        return predictions


class EnsembleForecaster:
    """Weighted ensemble combining Linear, Polynomial, Holt-Winters, and ARIMA forecasts."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "linear": 0.20,
            "polynomial": 0.30,
            "holt_winters": 0.30,
            "arima": 0.20,
        }
        self._normalize_weights()

    def _normalize_weights(self):
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
        else:
            self.weights = {"linear": 0.25, "polynomial": 0.25, "holt_winters": 0.25, "arima": 0.25}

    def forecast(self, model_predictions: Dict[str, List[float]]) -> List[float]:
        """Combines multiple model prediction lists into a single weighted forecast."""
        if not model_predictions:
            return []

        first_key = next(iter(model_predictions))
        length = len(model_predictions[first_key])
        combined = [0.0] * length

        active_weight_sum = 0.0
        for model_name, preds in model_predictions.items():
            w = self.weights.get(model_name, 0.0)
            if w > 0:
                active_weight_sum += w
                for i in range(min(length, len(preds))):
                    combined[i] += w * preds[i]

        if active_weight_sum > 0 and abs(active_weight_sum - 1.0) > 1e-4:
            combined = [val / active_weight_sum for val in combined]

        return combined


# =====================================================================
# 3. Confidence Interval Calculator
# =====================================================================

class ConfidenceIntervalCalculator:
    """Calculates p10, p50, and p90 prediction intervals using residual variance scaling."""

    Z_P10: float = -1.28155
    Z_P90: float = 1.28155

    @classmethod
    def calculate_intervals(
        cls,
        predicted_values: List[float],
        residual_std: float,
        metric_type: str = "generic",
    ) -> List[Dict[str, float]]:
        """
        Computes p10, p50, and p90 bands for each forecast step.
        Standard error scales with sqrt(step) as forecast horizon extends.
        """
        intervals = []
        base_std = max(0.01, residual_std)

        for step, p50 in enumerate(predicted_values, start=1):
            horizon_scale = math.sqrt(step)
            step_std = base_std * horizon_scale

            p10 = p50 + cls.Z_P10 * step_std
            p90 = p50 + cls.Z_P90 * step_std

            if metric_type in ("queue_depth", "worker_count", "latency_p95"):
                p10 = max(0.0, p10)
                p50 = max(0.0, p50)
                p90 = max(0.0, p90)
            elif metric_type == "error_rate":
                p10 = min(max(0.0, p10), 100.0)
                p50 = min(max(0.0, p50), 100.0)
                p90 = min(max(0.0, p90), 100.0)

            intervals.append({
                "p10": round(p10, 4),
                "p50": round(p50, 4),
                "p90": round(p90, 4),
            })

        return intervals


# =====================================================================
# 4. Master Predictive Forecasting Engine
# =====================================================================

class PredictiveForecastingEngine:
    """
    Main orchestration service for time-series forecasting.
    Fits all models, generates ensemble, calculates p10/p50/p90 confidence bands,
    and returns standardized forecast snapshots across horizons.
    """

    HORIZONS_MINUTES = [15, 60, 360, 1440]

    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {}
        self._snapshots: List[Dict[str, Any]] = []

    def fit_and_forecast(
        self,
        workspace_id: str,
        metric_type: str,
        history: List[TimeSeriesPoint],
        model_name: str = "ensemble",
        forecast_horizon_minutes: int = 60,
        step_minutes: int = 15,
        model_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Fits specified model or full ensemble and outputs forecast snapshot with confidence bands.
        """
        if not history:
            return {
                "workspace_id": workspace_id,
                "metric_type": metric_type,
                "model_used": model_name,
                "forecast_horizon_minutes": forecast_horizon_minutes,
                "confidence_score": 0.0,
                "predictions": [],
            }

        params = model_params or {}
        values = [p.value for p in history]
        n_steps = max(1, forecast_horizon_minutes // max(1, step_minutes))

        # Model fits
        linear_model = LinearTrendModel().fit(values)
        poly_model = PolynomialTrendModel(degree=params.get("poly_degree", 2), auto_degree=True).fit(values)
        hw_model = HoltWintersModel(
            season_length=params.get("season_length", 12),
            alpha=params.get("alpha", 0.3),
            beta=params.get("beta", 0.1),
            gamma=params.get("gamma", 0.2),
        ).fit(values)
        arima_model = ARIMABaselineModel(
            p=params.get("arima_p", 2),
            d=params.get("arima_d", 1),
            q=params.get("arima_q", 1),
        ).fit(values)

        pred_map = {
            "linear": linear_model.predict(n_steps),
            "polynomial": poly_model.predict(n_steps),
            "holt_winters": hw_model.predict(n_steps),
            "arima": arima_model.predict(n_steps),
        }

        # Select final prediction series
        selected_model = model_name.lower()
        if selected_model == "ensemble":
            ensemble = EnsembleForecaster()
            final_preds = ensemble.forecast(pred_map)
            res_std = (
                0.25 * linear_model.residual_std
                + 0.25 * poly_model.residual_std
                + 0.25 * hw_model.residual_std
                + 0.25 * arima_model.residual_std
            )
        elif selected_model in pred_map:
            final_preds = pred_map[selected_model]
            if selected_model == "linear":
                res_std = linear_model.residual_std
            elif selected_model == "polynomial":
                res_std = poly_model.residual_std
            elif selected_model == "holt_winters":
                res_std = hw_model.residual_std
            else:
                res_std = arima_model.residual_std
        else:
            ensemble = EnsembleForecaster()
            final_preds = ensemble.forecast(pred_map)
            selected_model = "ensemble"
            res_std = 1.0

        # Confidence intervals
        intervals = ConfidenceIntervalCalculator.calculate_intervals(
            predicted_values=final_preds,
            residual_std=res_std,
            metric_type=metric_type,
        )

        # Generate output snapshots with timestamps
        last_dt = history[-1].timestamp
        snapshot_records = []
        for i, (pred_val, interval) in enumerate(zip(final_preds, intervals), start=1):
            target_time = last_dt + timedelta(minutes=i * step_minutes)
            snapshot_records.append({
                "id": str(uuid.uuid4()),
                "workspace_id": workspace_id,
                "metric_type": metric_type,
                "forecast_horizon_minutes": i * step_minutes,
                "predicted_at": datetime.now(timezone.utc).isoformat(),
                "target_time": target_time.isoformat(),
                "predicted_value": round(float(pred_val), 4),
                "confidence_p10": interval["p10"],
                "confidence_p50": interval["p50"],
                "confidence_p90": interval["p90"],
                "model_used": selected_model,
                "confidence_score": round(max(0.5, min(1.0, 1.0 - (res_std / (abs(pred_val) + 1.0)))), 2),
            })

        conf_score = round(max(0.5, min(1.0, 1.0 - (res_std / (abs(final_preds[0]) + 1.0 if final_preds else 1.0)))), 2)

        return {
            "workspace_id": workspace_id,
            "metric_type": metric_type,
            "model_used": selected_model,
            "forecast_horizon_minutes": forecast_horizon_minutes,
            "confidence_score": conf_score,
            "predictions": snapshot_records,
            "model_metrics": {
                "linear_r2": round(linear_model.r2_score, 4),
                "polynomial_r2": round(poly_model.r2_score, 4),
                "residual_std": round(res_std, 4),
            },
        }
