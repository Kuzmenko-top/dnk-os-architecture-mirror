# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_anomaly_detection_service"
# purpose: "Time-Series Anomaly Detection using Z-Score, EWMA adaptive smoothing, and hybrid scoring"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


class TimeSeriesPreprocessor:
    """Preprocesses series data with windowing, IQR outlier filtering, and normalization."""

    @staticmethod
    def remove_outliers_iqr(series: List[float], multiplier: float = 1.5) -> List[float]:
        """Filter extreme outliers using the Interquartile Range (IQR) method."""
        if len(series) < 4:
            return list(series)
        sorted_s = sorted(series)
        n = len(sorted_s)
        q1 = sorted_s[int(n * 0.25)]
        q3 = sorted_s[int(n * 0.75)]
        iqr = q3 - q1
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        return [x for x in series if lower_bound <= x <= upper_bound]

    @staticmethod
    def normalize_min_max(series: List[float]) -> List[float]:
        """Normalize series values to [0.0, 1.0] range."""
        if not series:
            return []
        min_v = min(series)
        max_v = max(series)
        if abs(max_v - min_v) < 1e-9:
            return [0.5 for _ in series]
        return [(x - min_v) / (max_v - min_v) for x in series]


class ZScoreDetector:
    """Statistical anomaly detector based on rolling standard score."""

    @staticmethod
    def compute_z_score(
        current_value: float,
        history: List[float],
        z_threshold: float = 2.5,
    ) -> Tuple[float, bool]:
        """
        Compute Z-score and flag anomaly if score exceeds threshold.
        Returns (normalized_score_0_to_1, is_anomaly).
        """
        if not history or len(history) < 3:
            return 0.0, False

        mean = sum(history) / len(history)
        variance = sum((x - mean) ** 2 for x in history) / len(history)
        std_dev = math.sqrt(variance)

        if std_dev < 1e-6:
            # Zero variance: if current equals mean, score is 0; otherwise if different, score is 1
            diff = abs(current_value - mean)
            if diff > 1e-4:
                return 1.0, True
            return 0.0, False

        z = abs(current_value - mean) / std_dev
        is_anomaly = z >= z_threshold

        # Normalize z to [0.0, 1.0] where z=3.0 maps to ~1.0
        normalized_score = min(1.0, z / 3.0)
        return round(normalized_score, 4), is_anomaly


class EWMADetector:
    """Exponentially Weighted Moving Average detector with adaptive variance smoothing."""

    def __init__(self, alpha: float = 0.3, beta: float = 0.3):
        self.alpha = alpha  # Mean smoothing factor
        self.beta = beta    # Variance smoothing factor

    def compute_ewma_score(
        self,
        current_value: float,
        history: List[float],
        deviation_threshold: float = 2.5,
    ) -> Tuple[float, bool]:
        """
        Compute EWMA adaptive deviation score.
        Returns (normalized_score_0_to_1, is_anomaly).
        """
        if not history:
            return 0.0, False

        # Compute rolling EWMA mean and variance
        ewma_mean = history[0]
        ewma_var = 0.0

        for val in history[1:]:
            diff = val - ewma_mean
            ewma_mean = self.alpha * val + (1 - self.alpha) * ewma_mean
            ewma_var = self.beta * (diff ** 2) + (1 - self.beta) * ewma_var

        ewma_std = math.sqrt(ewma_var)

        if ewma_std < 1e-6:
            diff = abs(current_value - ewma_mean)
            if diff > 1e-4:
                return 1.0, True
            return 0.0, False

        deviation = abs(current_value - ewma_mean) / ewma_std
        is_anomaly = deviation >= deviation_threshold

        normalized_score = min(1.0, deviation / 3.0)
        return round(normalized_score, 4), is_anomaly


class AnomalyDetectionService:
    """Orchestrates multi-algorithm anomaly detection, score caching, and event logging."""

    def __init__(self):
        self.preprocessor = TimeSeriesPreprocessor()
        self.zscore_detector = ZScoreDetector()
        self.ewma_detector = EWMADetector(alpha=0.3, beta=0.3)
        self._anomaly_scores: Dict[str, List[Dict[str, Any]]] = {}  # workspace_id -> list of score items
        self._anomaly_events: List[Dict[str, Any]] = []

    def detect_anomaly(
        self,
        current_value: float,
        history: List[float],
        algorithm: str = "hybrid",
        clean_outliers: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluate time series data for anomalies using ZScore, EWMA, or Hybrid approach.
        """
        data = self.preprocessor.remove_outliers_iqr(history) if clean_outliers else history

        z_score, z_anomaly = self.zscore_detector.compute_z_score(current_value, data)
        ewma_score, ewma_anomaly = self.ewma_detector.compute_ewma_score(current_value, data)

        if algorithm == "zscore":
            final_score = z_score
            is_anomaly = z_anomaly
        elif algorithm == "ewma":
            final_score = ewma_score
            is_anomaly = ewma_anomaly
        else:  # hybrid: weighted 50/50, anomaly if either triggers or score > 0.75
            final_score = round(0.5 * z_score + 0.5 * ewma_score, 4)
            is_anomaly = z_anomaly or ewma_anomaly or (final_score >= 0.75)

        return {
            "score": final_score,
            "is_anomaly": is_anomaly,
            "z_score": z_score,
            "ewma_score": ewma_score,
            "algorithm": algorithm,
        }

    async def record_and_evaluate(
        self,
        workspace_id: str,
        metric_type: str,
        current_value: float,
        history: List[float],
        algorithm: str = "hybrid",
        window_seconds: int = 300,
    ) -> Dict[str, Any]:
        """Run anomaly detection, cache the anomaly score for heatmap, and log if anomaly."""
        res = self.detect_anomaly(current_value, history, algorithm=algorithm)
        score = res["score"]
        is_anomaly = res["is_anomaly"]
        now = datetime.now(timezone.utc)

        score_entry = {
            "id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "metric_type": metric_type,
            "score": score,
            "detected_at": now.isoformat(),
            "algorithm": algorithm,
            "window_seconds": window_seconds,
            "is_anomaly": is_anomaly,
            "metric_value": float(current_value),
        }

        self._anomaly_scores.setdefault(workspace_id, []).append(score_entry)
        # Keep recent 200 scores per workspace
        if len(self._anomaly_scores[workspace_id]) > 200:
            self._anomaly_scores[workspace_id] = self._anomaly_scores[workspace_id][-200:]

        if is_anomaly:
            event = {
                "id": str(uuid.uuid4()),
                "workspace_id": workspace_id,
                "metric_type": metric_type,
                "score": score,
                "detected_at": now.isoformat(),
                "algorithm": algorithm,
                "current_value": float(current_value),
                "severity": "critical" if score >= 0.85 else "warning",
            }
            self._anomaly_events.append(event)
            score_entry["event_id"] = event["id"]

        return score_entry

    async def get_anomaly_scores(
        self,
        workspace_id: str,
        metric_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent anomaly scores for heatmap visualization."""
        scores = self._anomaly_scores.get(workspace_id, [])
        if metric_type:
            scores = [s for s in scores if s["metric_type"] == metric_type]
        return sorted(scores, key=lambda s: s["detected_at"], reverse=True)[:limit]

    async def get_anomaly_events(
        self,
        workspace_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve detected anomaly events."""
        events = self._anomaly_events
        if workspace_id:
            events = [e for e in events if e["workspace_id"] == workspace_id]
        return sorted(events, key=lambda e: e["detected_at"], reverse=True)[:limit]

    def clear(self):
        """Helper to reset in-memory state for testing."""
        self._anomaly_scores.clear()
        self._anomaly_events.clear()


anomaly_detection_service = AnomalyDetectionService()
