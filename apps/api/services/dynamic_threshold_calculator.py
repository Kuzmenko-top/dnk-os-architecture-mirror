# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_dynamic_threshold_calculator"
# purpose: "Dynamic Threshold Auto-Tuning Engine based on Rolling Historical Statistics for DNK-ANALYTICS-004"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class DynamicThresholdCalculator:
    """
    Computes rolling dynamic thresholds (mean, std, p10, p50, p90, upper/lower bounds)
    and performs adaptive auto-tuning for metric anomaly detection.
    """

    @staticmethod
    def calculate_percentile(sorted_data: List[float], percentile: float) -> float:
        """Calculate arbitrary percentile (0.0 - 1.0) on sorted float array."""
        if not sorted_data:
            return 0.0
        n = len(sorted_data)
        if n == 1:
            return sorted_data[0]
        index = (n - 1) * percentile
        lower_idx = int(math.floor(index))
        upper_idx = int(math.ceil(index))
        if lower_idx == upper_idx:
            return sorted_data[lower_idx]
        fraction = index - lower_idx
        return sorted_data[lower_idx] + fraction * (sorted_data[upper_idx] - sorted_data[lower_idx])

    @classmethod
    def compute_thresholds(
        cls,
        history_values: List[float],
        sensitivity: float = 0.80,
        rolling_window_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Calculate rolling statistics and lower/upper bounds.
        Sensitivity in [0.0, 1.0]:
          0.0: wide bounds (mean +/- 3.5 std, or 10th-90th wide envelope)
          1.0: tight bounds (mean +/- 1.5 std, or 25th-75th envelope)
        """
        if not history_values:
            return {
                "rolling_window_hours": rolling_window_hours,
                "mean_value": 0.0,
                "std_value": 0.0,
                "percentile_p10": 0.0,
                "percentile_p50": 0.0,
                "percentile_p90": 0.0,
                "lower_bound": 0.0,
                "upper_bound": 0.0,
                "sample_size": 0,
            }

        n = len(history_values)
        mean_v = sum(history_values) / n
        variance = sum((x - mean_v) ** 2 for x in history_values) / n if n > 1 else 0.0
        std_v = math.sqrt(variance)

        sorted_vals = sorted(history_values)
        p10 = cls.calculate_percentile(sorted_vals, 0.10)
        p50 = cls.calculate_percentile(sorted_vals, 0.50)
        p90 = cls.calculate_percentile(sorted_vals, 0.90)

        # Standard multiplier adjusted by sensitivity
        # sensitivity 0.0 -> std_mult = 3.5; sensitivity 1.0 -> std_mult = 1.5
        std_mult = 3.5 - (sensitivity * 2.0)

        lower_bound = max(0.0, mean_v - (std_mult * std_v)) if min(history_values) >= 0 else mean_v - (std_mult * std_v)
        upper_bound = mean_v + (std_mult * std_v)

        return {
            "rolling_window_hours": rolling_window_hours,
            "mean_value": round(mean_v, 4),
            "std_value": round(std_v, 4),
            "percentile_p10": round(p10, 4),
            "percentile_p50": round(p50, 4),
            "percentile_p90": round(p90, 4),
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
            "sample_size": n,
        }

    @classmethod
    def auto_tune_sensitivity(
        cls,
        history_values: List[float],
        target_false_positive_rate: float = 0.01,
    ) -> float:
        """
        Auto-tune detector sensitivity based on baseline noise in historical data.
        Returns recommended sensitivity in [0.50, 0.95].
        """
        if len(history_values) < 10:
            return 0.80

        n = len(history_values)
        mean_v = sum(history_values) / n
        std_v = math.sqrt(sum((x - mean_v) ** 2 for x in history_values) / n)

        if std_v < 1e-6:
            return 0.95

        cv = std_v / (abs(mean_v) + 1e-6)  # coefficient of variation

        # If data is highly variable (noisy), reduce sensitivity to prevent alert fatigue
        if cv > 0.8:
            return 0.60
        elif cv > 0.4:
            return 0.75
        elif cv < 0.1:
            return 0.90
        else:
            return 0.80
