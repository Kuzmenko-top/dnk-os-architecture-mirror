# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_real_time_anomaly_detector"
# purpose: "Real-Time Streaming Anomaly Detection Engine (Z-Score, IQR, Holt-Winters, Lightweight Isolation Forest, Ensemble) for DNK-ANALYTICS-004"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class ZScoreDetector:
    """Statistical detector based on rolling standard score (Z-Score)."""

    @staticmethod
    def detect(
        current_value: float,
        history: List[float],
        sensitivity: float = 0.80,
    ) -> Dict[str, Any]:
        """
        Sensitivity in [0.0, 1.0] maps to Z threshold in [1.5, 4.0] (higher sensitivity -> lower threshold).
        """
        if not history or len(history) < 3:
            return {
                "detector": "zscore",
                "anomaly_score": 0.0,
                "is_anomalous": False,
                "lower_bound": None,
                "upper_bound": None,
                "z_value": 0.0,
            }

        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std_dev = math.sqrt(variance)

        # Higher sensitivity -> stricter (lower z threshold)
        # sensitivity 0.0 -> threshold 4.0; sensitivity 1.0 -> threshold 1.5
        z_thresh = 4.0 - (sensitivity * 2.5)

        if std_dev < 1e-6:
            diff = abs(current_value - mean)
            is_anom = diff > 1e-4
            score = 1.0 if is_anom else 0.0
            return {
                "detector": "zscore",
                "anomaly_score": score,
                "is_anomalous": is_anom,
                "lower_bound": mean - 1e-4,
                "upper_bound": mean + 1e-4,
                "z_value": 99.0 if is_anom else 0.0,
            }

        z = abs(current_value - mean) / std_dev
        lower_bound = mean - (z_thresh * std_dev)
        upper_bound = mean + (z_thresh * std_dev)
        is_anom = current_value < lower_bound or current_value > upper_bound

        # Calibrate anomaly score to [0.0, 1.0]
        score = min(1.0, max(0.0, z / (z_thresh * 1.5)))

        return {
            "detector": "zscore",
            "anomaly_score": round(score, 4),
            "is_anomalous": is_anom,
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
            "z_value": round(z, 4),
        }


class IQRDetector:
    """Outlier detector based on Interquartile Range (IQR)."""

    @staticmethod
    def detect(
        current_value: float,
        history: List[float],
        sensitivity: float = 0.80,
    ) -> Dict[str, Any]:
        """
        Sensitivity maps to IQR multiplier in [1.0, 3.0] (higher sensitivity -> smaller multiplier).
        """
        if not history or len(history) < 4:
            return {
                "detector": "iqr",
                "anomaly_score": 0.0,
                "is_anomalous": False,
                "lower_bound": None,
                "upper_bound": None,
                "iqr_value": 0.0,
            }

        sorted_h = sorted(history)
        n = len(sorted_h)
        q1 = sorted_h[int(n * 0.25)]
        q3 = sorted_h[int(n * 0.75)]
        iqr = q3 - q1

        # multiplier from 3.0 (low sensitivity) down to 1.0 (high sensitivity)
        multiplier = 3.0 - (sensitivity * 2.0)

        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)

        if iqr < 1e-6:
            diff = abs(current_value - q1)
            is_anom = diff > 1e-4
            score = 1.0 if is_anom else 0.0
            return {
                "detector": "iqr",
                "anomaly_score": score,
                "is_anomalous": is_anom,
                "lower_bound": q1,
                "upper_bound": q3,
                "iqr_value": 0.0,
            }

        is_anom = current_value < lower_bound or current_value > upper_bound

        distance = max(0.0, lower_bound - current_value, current_value - upper_bound)
        score = min(1.0, distance / (iqr * multiplier + 1e-6)) if is_anom else min(0.4, abs(current_value - (q1 + q3) / 2) / ((q3 - q1 + 1e-6) * multiplier))

        return {
            "detector": "iqr",
            "anomaly_score": round(min(1.0, max(0.0, score)), 4),
            "is_anomalous": is_anom,
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
            "iqr_value": round(iqr, 4),
        }


class HoltWintersDetector:
    """
    Forecasting-based anomaly detector using Double/Triple Exponential Smoothing (Holt-Winters).
    Computes forecasted value and detects anomalies when residual exceeds error bound.
    """

    @staticmethod
    def forecast_and_detect(
        current_value: float,
        history: List[float],
        sensitivity: float = 0.80,
        alpha: float = 0.3,
        beta: float = 0.1,
    ) -> Dict[str, Any]:
        if not history or len(history) < 4:
            return {
                "detector": "holt_winters",
                "anomaly_score": 0.0,
                "is_anomalous": False,
                "forecasted_value": current_value,
                "residual": 0.0,
                "lower_bound": None,
                "upper_bound": None,
            }

        # Level and Trend initialization
        level = history[0]
        trend = history[1] - history[0]

        residuals: List[float] = []

        for i in range(1, len(history)):
            val = history[i]
            prev_level = level
            pred = level + trend
            residuals.append(abs(val - pred))
            level = alpha * val + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend

        # Forecast next step (for current_value)
        forecast = level + trend
        actual_residual = abs(current_value - forecast)

        avg_residual = (sum(residuals) / len(residuals)) if residuals else 1.0
        var_residual = (sum((r - avg_residual) ** 2 for r in residuals) / len(residuals)) if residuals else 1.0
        std_residual = math.sqrt(var_residual) if var_residual > 0 else 1.0

        # Sensitivity threshold multiplier: 4.0 down to 1.5
        thresh_mult = 4.0 - (sensitivity * 2.5)
        error_bound = max(1e-4, thresh_mult * (avg_residual + std_residual))

        lower_bound = forecast - error_bound
        upper_bound = forecast + error_bound
        is_anom = current_value < lower_bound or current_value > upper_bound

        score = min(1.0, max(0.0, actual_residual / (error_bound * 1.5)))

        return {
            "detector": "holt_winters",
            "anomaly_score": round(score, 4),
            "is_anomalous": is_anom,
            "forecasted_value": round(forecast, 4),
            "residual": round(actual_residual, 4),
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
        }


class LightweightIsolationForestDetector:
    """
    Lightweight 1D Isolation Forest detector using randomized binary partitioning trees.
    Calculates average path length to isolate the target value relative to history.
    """

    @staticmethod
    def _c_factor(n: int) -> float:
        """Average path length of unsuccessful search in BST."""
        if n <= 1:
            return 1.0
        if n == 2:
            return 1.0
        euler_mascheroni = 0.5772156649
        return 2.0 * (math.log(n - 1) + euler_mascheroni) - (2.0 * (n - 1) / n)

    @classmethod
    def detect(
        cls,
        current_value: float,
        history: List[float],
        sensitivity: float = 0.80,
        num_trees: int = 25,
        max_depth: int = 8,
    ) -> Dict[str, Any]:
        if not history or len(history) < 5:
            return {
                "detector": "isolation_forest",
                "anomaly_score": 0.0,
                "is_anomalous": False,
                "lower_bound": None,
                "upper_bound": None,
            }

        data = list(history) + [current_value]
        min_v = min(data)
        max_v = max(data)

        if abs(max_v - min_v) < 1e-6:
            return {
                "detector": "isolation_forest",
                "anomaly_score": 0.0,
                "is_anomalous": False,
                "lower_bound": min_v,
                "upper_bound": max_v,
            }

        # Compute average isolation depth for current_value across randomized trees
        rng = random.Random(42)  # Deterministic seed for stability
        depths: List[int] = []

        for _ in range(num_trees):
            current_min = min_v
            current_max = max_v
            depth = 0
            while depth < max_depth and (current_max - current_min) > 1e-6:
                split_point = rng.uniform(current_min, current_max)
                depth += 1
                if current_value < split_point:
                    current_max = split_point
                else:
                    current_min = split_point
                # Stop if isolated
                subset = [x for x in data if current_min <= x <= current_max]
                if len(subset) <= 1:
                    break
            depths.append(depth)

        avg_depth = sum(depths) / len(depths)
        c = cls._c_factor(len(data))
        # Isolation forest anomaly score: s = 2 ^ (- avg_depth / c)
        raw_score = 2.0 ** (- (avg_depth / max(1.0, c)))

        # Cutoff threshold adjusted by sensitivity (e.g. 0.60 down to 0.45)
        cutoff = 0.70 - (sensitivity * 0.25)
        is_anom = raw_score >= cutoff

        # Bounds estimate from history
        h_sorted = sorted(history)
        lower_bound = h_sorted[0]
        upper_bound = h_sorted[-1]

        return {
            "detector": "isolation_forest",
            "anomaly_score": round(min(1.0, max(0.0, raw_score)), 4),
            "is_anomalous": is_anom,
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
        }


class RealTimeAnomalyDetector:
    """
    Main Orchestrator for Real-Time Streaming Anomaly Detection.
    Supports individual detectors and Ensemble scoring with multi-model blending.
    """

    def __init__(self):
        self.detectors = {
            "zscore": ZScoreDetector.detect,
            "iqr": IQRDetector.detect,
            "holt_winters": HoltWintersDetector.forecast_and_detect,
            "isolation_forest": LightweightIsolationForestDetector.detect,
        }

    def evaluate_metric(
        self,
        current_value: float,
        history: List[float],
        detector_type: str = "zscore",
        sensitivity: float = 0.80,
    ) -> Dict[str, Any]:
        """Evaluate a single metric point against historical window using chosen detector."""
        if detector_type == "ensemble":
            return self.evaluate_ensemble(current_value, history, sensitivity)

        detector_fn = self.detectors.get(detector_type, ZScoreDetector.detect)
        return detector_fn(current_value, history, sensitivity)

    def evaluate_ensemble(
        self,
        current_value: float,
        history: List[float],
        sensitivity: float = 0.80,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Ensemble detection combining Z-Score, IQR, Holt-Winters, and Isolation Forest.
        Returns blended anomaly score in [0.00, 1.00] and consensus anomaly status.
        """
        if weights is None:
            weights = {
                "zscore": 0.30,
                "iqr": 0.30,
                "holt_winters": 0.25,
                "isolation_forest": 0.15,
            }

        results: Dict[str, Dict[str, Any]] = {}
        weighted_score = 0.0
        total_weight = 0.0
        votes_anomalous = 0

        lower_bounds: List[float] = []
        upper_bounds: List[float] = []

        for name, fn in self.detectors.items():
            res = fn(current_value, history, sensitivity)
            results[name] = res
            w = weights.get(name, 0.25)
            weighted_score += res["anomaly_score"] * w
            total_weight += w
            if res["is_anomalous"]:
                votes_anomalous += 1

            if res.get("lower_bound") is not None:
                lower_bounds.append(res["lower_bound"])
            if res.get("upper_bound") is not None:
                upper_bounds.append(res["upper_bound"])

        ensemble_score = weighted_score / total_weight if total_weight > 0 else 0.0

        # Consensus: at least 2 detectors or score >= 0.70
        is_anom = (votes_anomalous >= 2) or (ensemble_score >= 0.70)

        effective_lower = min(lower_bounds) if lower_bounds else None
        effective_upper = max(upper_bounds) if upper_bounds else None

        return {
            "detector": "ensemble",
            "anomaly_score": round(min(1.0, max(0.0, ensemble_score)), 4),
            "is_anomalous": is_anom,
            "votes_anomalous": votes_anomalous,
            "total_detectors": len(self.detectors),
            "lower_bound": effective_lower,
            "upper_bound": effective_upper,
            "sub_detectors": results,
        }
