# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canary_analysis_engine"
# purpose: "Statistical Canary Analysis Engine (Mann-Whitney U, T-test, Thresholds) (DNK-PLATFORM-SCALE-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import math
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class CanaryAnalysisInput(BaseModel):
    deployment_id: str
    blue_metrics: Dict[str, Any]  # {latency_samples: [...], error_rate: float, p95_ms: float, request_count: int}
    green_metrics: Dict[str, Any]
    statistical_test: str = "mann_whitney_u"  # 'mann_whitney_u', 't_test'
    significance_level: float = 0.05  # alpha = 5%
    allowed_latency_degradation_pct: float = 10.0  # max 10% latency increase
    allowed_error_rate_delta: float = 0.005  # max 0.5% error rate increase
    min_sample_size: int = 10


class CanaryAnalysisResult(BaseModel):
    deployment_id: str
    analysis_time: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    statistical_test: str
    test_statistic: float
    p_value: float
    is_significant: bool
    is_degraded: bool
    recommendation: str  # 'promote', 'rollback', 'wait', 'hold'
    analysis_notes: str
    blue_snapshot: Dict[str, Any]
    green_snapshot: Dict[str, Any]


class CanaryAnalysisEngine:
    """
    Statistical engine for comparing telemetry between Active (Blue) and Candidate (Green) environments.
    Supports Mann-Whitney U rank-sum test, Welch's T-test, and multi-dimensional thresholding.
    """

    @staticmethod
    def _normal_cdf(x: float) -> float:
        """Approximates standard normal cumulative distribution function using math.erf."""
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

    @classmethod
    def mann_whitney_u_test(
        cls,
        sample_a: List[float],
        sample_b: List[float],
    ) -> Tuple[float, float]:
        """
        Calculates the Mann-Whitney U statistic and two-tailed p-value.
        sample_a = Blue (Baseline), sample_b = Green (Candidate).
        """
        n1 = len(sample_a)
        n2 = len(sample_b)

        if n1 < 3 or n2 < 3:
            return 0.0, 1.0

        # Combine and rank samples
        combined = [(val, 0) for val in sample_a] + [(val, 1) for val in sample_b]
        combined.sort(key=lambda item: item[0])

        ranks = [0.0] * len(combined)
        i = 0
        while i < len(combined):
            j = i
            while j < len(combined) and combined[j][0] == combined[i][0]:
                j += 1
            # Tie handling: average rank for identical values (1-based ranking)
            avg_rank = (i + 1 + j) / 2.0
            for k in range(i, j):
                ranks[k] = avg_rank
            i = j

        rank_sum_a = sum(ranks[idx] for idx, item in enumerate(combined) if item[1] == 0)
        u1 = n1 * n2 + (n1 * (n1 + 1)) / 2.0 - rank_sum_a
        u2 = n1 * n2 - u1
        u_stat = min(u1, u2)

        # Normal approximation for p-value
        mean_u = (n1 * n2) / 2.0
        std_u = math.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12.0)

        if std_u == 0:
            return u_stat, 1.0

        z = (u_stat - mean_u) / std_u
        p_val = 2.0 * cls._normal_cdf(-abs(z))
        return round(u_stat, 4), round(max(0.0, min(1.0, p_val)), 4)

    @classmethod
    def welch_t_test(
        cls,
        sample_a: List[float],
        sample_b: List[float],
    ) -> Tuple[float, float]:
        """
        Calculates Welch's unequal variances t-test statistic and two-tailed p-value.
        """
        n1 = len(sample_a)
        n2 = len(sample_b)

        if n1 < 2 or n2 < 2:
            return 0.0, 1.0

        mean1 = sum(sample_a) / n1
        mean2 = sum(sample_b) / n2

        var1 = sum((x - mean1) ** 2 for x in sample_a) / (n1 - 1) if n1 > 1 else 0.0
        var2 = sum((x - mean2) ** 2 for x in sample_b) / (n2 - 1) if n2 > 1 else 0.0

        denom = math.sqrt((var1 / n1) + (var2 / n2)) if ((var1 / n1) + (var2 / n2)) > 0 else 0.0
        if denom == 0:
            return 0.0, 1.0

        t_stat = (mean2 - mean1) / denom
        p_val = 2.0 * cls._normal_cdf(-abs(t_stat))
        return round(t_stat, 4), round(max(0.0, min(1.0, p_val)), 4)

    def analyze_canary(self, input_data: CanaryAnalysisInput) -> CanaryAnalysisResult:
        """
        Runs comprehensive statistical and threshold analysis to recommend deployment progression.
        """
        blue = input_data.blue_metrics
        green = input_data.green_metrics

        blue_latencies: List[float] = blue.get("latency_samples", [])
        green_latencies: List[float] = green.get("latency_samples", [])

        # Fallback if raw latency arrays not provided
        if not blue_latencies:
            blue_latencies = [blue.get("p95_ms", 100.0)] * input_data.min_sample_size
        if not green_latencies:
            green_latencies = [green.get("p95_ms", 100.0)] * input_data.min_sample_size

        # 1. Sample Size Check
        if len(green_latencies) < input_data.min_sample_size:
            return CanaryAnalysisResult(
                deployment_id=input_data.deployment_id,
                statistical_test=input_data.statistical_test,
                test_statistic=0.0,
                p_value=1.0,
                is_significant=False,
                is_degraded=False,
                recommendation="wait",
                analysis_notes=f"Insufficient sample size ({len(green_latencies)} < {input_data.min_sample_size}). Waiting for more traffic.",
                blue_snapshot=blue,
                green_snapshot=green,
            )

        # 2. Run Statistical Test
        if input_data.statistical_test == "t_test":
            stat, p_val = self.welch_t_test(blue_latencies, green_latencies)
        else:
            stat, p_val = self.mann_whitney_u_test(blue_latencies, green_latencies)

        is_significant = p_val < input_data.significance_level

        # 3. Latency & Error Rate Evaluation
        blue_p95 = blue.get("p95_ms", sum(blue_latencies) / len(blue_latencies))
        green_p95 = green.get("p95_ms", sum(green_latencies) / len(green_latencies))

        latency_degradation_pct = 0.0
        if blue_p95 > 0:
            latency_degradation_pct = ((green_p95 - blue_p95) / blue_p95) * 100.0

        blue_err = blue.get("error_rate", 0.0)
        green_err = green.get("error_rate", 0.0)
        error_rate_delta = green_err - blue_err

        # Check Degradation
        is_latency_degraded = latency_degradation_pct > input_data.allowed_latency_degradation_pct
        is_error_degraded = error_rate_delta > input_data.allowed_error_rate_delta
        is_degraded = is_error_degraded or (is_latency_degraded and is_significant)

        # 4. Formulate Recommendation
        notes: List[str] = []
        if is_error_degraded:
            notes.append(
                f"Critical error rate delta (+{error_rate_delta * 100:.2f}% > +{input_data.allowed_error_rate_delta * 100:.2f}%)"
            )
        if is_latency_degraded:
            notes.append(
                f"Latency p95 degraded (+{latency_degradation_pct:.1f}% > +{input_data.allowed_latency_degradation_pct:.1f}%, p={p_val})"
            )

        if is_degraded:
            recommendation = "rollback"
            summary_note = f"Degradation detected: {'; '.join(notes)}. Immediate rollback advised."
        elif is_significant and latency_degradation_pct > 0:
            recommendation = "hold"
            summary_note = f"Statistical difference detected (p={p_val}), but within tolerated degradation limits."
        else:
            recommendation = "promote"
            summary_note = (
                f"Candidate performance healthy. Latency change {latency_degradation_pct:.1f}%, error delta {error_rate_delta * 100:.2f}% (p={p_val})."
            )

        return CanaryAnalysisResult(
            deployment_id=input_data.deployment_id,
            statistical_test=input_data.statistical_test,
            test_statistic=stat,
            p_value=p_val,
            is_significant=is_significant,
            is_degraded=is_degraded,
            recommendation=recommendation,
            analysis_notes=summary_note,
            blue_snapshot=blue,
            green_snapshot=green,
        )
