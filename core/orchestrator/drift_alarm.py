#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/drift_alarm.py"
# purpose: "Statistical Output Drift & API Degradation Alarm for Google Gemini / LLM responses, assimilated from Soup."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import logging
import math
import os
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("dnk_drift_alarm")


class DriftVerdict(str, Enum):
    STABLE = "STABLE"
    DRIFT_DETECTED = "DRIFT_DETECTED"
    CRITICAL_ANOMALY = "CRITICAL_ANOMALY"


@dataclass
class SampleMetric:
    output_length: int
    latency_ms: float
    tools_called: List[str] = field(default_factory=list)
    success: bool = True
    extra_signals: Dict[str, float] = field(default_factory=dict)


@dataclass
class MetricDriftReport:
    metric_name: str
    baseline_mean: float
    current_mean: float
    drift_score: float  # PSI or normalized divergence
    has_drift: bool
    threshold: float
    details: str = ""


@dataclass
class DriftAlarmReport:
    verdict: DriftVerdict
    metrics: List[MetricDriftReport]
    overall_drift_score: float
    alarm_triggered: bool
    recommendation: str
    sample_count_baseline: int
    sample_count_current: int
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DriftAlarm:
    """Monitors distribution shifts across model responses (token lengths, latency,
    tool call variety, failure rates) to detect silent model degradation or silent API changes.
    Assimilated from the drift-alarm pattern in MakazhanAlpamys/Soup.
    """

    # PSI standard thresholds
    DEFAULT_PSI_THRESHOLD = 0.20
    CRITICAL_PSI_THRESHOLD = 0.40

    def __init__(
        self,
        component_name: str = "gemini_api",
        drift_threshold: float = DEFAULT_PSI_THRESHOLD,
        min_samples: int = 5,
    ):
        self.component_name = component_name
        self.drift_threshold = drift_threshold
        self.min_samples = min_samples
        self.baseline_samples: List[SampleMetric] = []
        self.current_samples: List[SampleMetric] = []

    def record_baseline(self, sample: SampleMetric) -> None:
        """Add a verified healthy sample to the baseline distribution."""
        self.baseline_samples.append(sample)

    def record_current(self, sample: SampleMetric) -> None:
        """Add a recent production or candidate sample for drift evaluation."""
        self.current_samples.append(sample)

    def set_baseline(self, samples: List[SampleMetric]) -> None:
        self.baseline_samples = list(samples)

    def set_current(self, samples: List[SampleMetric]) -> None:
        self.current_samples = list(samples)

    @staticmethod
    def calculate_psi(
        baseline: List[float],
        current: List[float],
        bins: Optional[int] = None,
    ) -> float:
        """Calculates Population Stability Index (PSI) between two continuous distributions
        with adaptive binning and Laplace smoothing to prevent noise explosion on small samples.
        """
        if not baseline or not current:
            return 0.0

        if bins is None:
            bins = min(5, max(2, len(baseline) // 4))

        all_values = baseline + current
        min_v = min(all_values)
        max_v = max(all_values)

        if math.isclose(min_v, max_v):
            return 0.0

        bin_width = (max_v - min_v) / bins
        bin_edges = [min_v + i * bin_width for i in range(bins + 1)]

        def get_counts(vals: List[float]) -> List[int]:
            counts = [0] * bins
            for v in vals:
                placed = False
                for b in range(bins):
                    if b == bins - 1:
                        if bin_edges[b] <= v <= bin_edges[b + 1]:
                            counts[b] += 1
                            placed = True
                            break
                    else:
                        if bin_edges[b] <= v < bin_edges[b + 1]:
                            counts[b] += 1
                            placed = True
                            break
                if not placed:
                    counts[-1] += 1
            return counts

        b_cnt = get_counts(baseline)
        c_cnt = get_counts(current)
        total_b = len(baseline)
        total_c = len(current)

        psi = 0.0
        for b_c, c_c in zip(b_cnt, c_cnt):
            # Laplace smoothing across bins
            p_b = (b_c + 1.0) / (total_b + bins)
            p_c = (c_c + 1.0) / (total_c + bins)
            psi += (p_c - p_b) * math.log(p_c / p_b)

        return max(0.0, float(psi))

    @staticmethod
    def calculate_categorical_psi(
        baseline_cats: List[str],
        current_cats: List[str],
    ) -> float:
        """Calculates PSI for categorical distributions with Laplace smoothing."""
        all_cats = sorted(set(baseline_cats).union(set(current_cats)))
        if not all_cats:
            return 0.0

        total_b = len(baseline_cats)
        total_c = len(current_cats)
        num_cats = len(all_cats)

        psi = 0.0
        for cat in all_cats:
            count_b = baseline_cats.count(cat)
            count_c = current_cats.count(cat)

            p_b = (count_b + 1.0) / (total_b + num_cats)
            p_c = (count_c + 1.0) / (total_c + num_cats)

            psi += (p_c - p_b) * math.log(p_c / p_b)

        return max(0.0, float(psi))

    def evaluate(self) -> DriftAlarmReport:
        """Evaluates whether current responses have drifted from baseline."""
        if len(self.baseline_samples) < self.min_samples or len(self.current_samples) < self.min_samples:
            return DriftAlarmReport(
                verdict=DriftVerdict.STABLE,
                metrics=[],
                overall_drift_score=0.0,
                alarm_triggered=False,
                recommendation=f"Insufficient samples (baseline: {len(self.baseline_samples)}, current: {len(self.current_samples)}, min: {self.min_samples}).",
                sample_count_baseline=len(self.baseline_samples),
                sample_count_current=len(self.current_samples),
            )

        metric_reports: List[MetricDriftReport] = []

        # 1. Output Length Drift
        b_len = [float(s.output_length) for s in self.baseline_samples]
        c_len = [float(s.output_length) for s in self.current_samples]
        len_psi = self.calculate_psi(b_len, c_len)
        has_len_drift = len_psi >= self.drift_threshold
        metric_reports.append(
            MetricDriftReport(
                metric_name="output_length",
                baseline_mean=sum(b_len) / len(b_len),
                current_mean=sum(c_len) / len(c_len),
                drift_score=round(len_psi, 4),
                has_drift=has_len_drift,
                threshold=self.drift_threshold,
                details=f"Length PSI: {len_psi:.4f} (baseline mean: {sum(b_len)/len(b_len):.1f}, current: {sum(c_len)/len(c_len):.1f})",
            )
        )

        # 2. Latency Drift
        b_lat = [s.latency_ms for s in self.baseline_samples]
        c_lat = [s.latency_ms for s in self.current_samples]
        lat_psi = self.calculate_psi(b_lat, c_lat)
        has_lat_drift = lat_psi >= self.drift_threshold
        metric_reports.append(
            MetricDriftReport(
                metric_name="latency_ms",
                baseline_mean=sum(b_lat) / len(b_lat),
                current_mean=sum(c_lat) / len(c_lat),
                drift_score=round(lat_psi, 4),
                has_drift=has_lat_drift,
                threshold=self.drift_threshold,
                details=f"Latency PSI: {lat_psi:.4f}",
            )
        )

        # 3. Tool Calling Distribution Drift
        b_tools: List[str] = []
        for s in self.baseline_samples:
            b_tools.extend(s.tools_called or ["__no_tool__"])
        c_tools: List[str] = []
        for s in self.current_samples:
            c_tools.extend(s.tools_called or ["__no_tool__"])

        tool_psi = self.calculate_categorical_psi(b_tools, c_tools)
        has_tool_drift = tool_psi >= self.drift_threshold
        metric_reports.append(
            MetricDriftReport(
                metric_name="tool_calling_distribution",
                baseline_mean=float(len(b_tools) / len(self.baseline_samples)),
                current_mean=float(len(c_tools) / len(self.current_samples)),
                drift_score=round(tool_psi, 4),
                has_drift=has_tool_drift,
                threshold=self.drift_threshold,
                details=f"Tool distribution PSI: {tool_psi:.4f}",
            )
        )

        # Overall Score & Verdict
        overall_score = max(m.drift_score for m in metric_reports)
        any_drift = any(m.has_drift for m in metric_reports)
        is_critical = overall_score >= self.CRITICAL_PSI_THRESHOLD

        if is_critical:
            verdict = DriftVerdict.CRITICAL_ANOMALY
            recommendation = (
                f"CRITICAL DRIFT detected (score: {overall_score:.4f}). "
                "Freeze production traffic, verify frontier model version changes, and check prompt templates."
            )
        elif any_drift:
            verdict = DriftVerdict.DRIFT_DETECTED
            recommendation = (
                f"Moderate DRIFT detected (score: {overall_score:.4f}). "
                "Monitor next batch and run adversarial validation before shipping mutations."
            )
        else:
            verdict = DriftVerdict.STABLE
            recommendation = "Model behavior is within calibrated statistical stability limits."

        return DriftAlarmReport(
            verdict=verdict,
            metrics=metric_reports,
            overall_drift_score=round(overall_score, 4),
            alarm_triggered=any_drift,
            recommendation=recommendation,
            sample_count_baseline=len(self.baseline_samples),
            sample_count_current=len(self.current_samples),
        )

    def save_baseline(self, filepath: str) -> None:
        """Persists the baseline samples to JSON."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(s) for s in self.baseline_samples]
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"component": self.component_name, "baseline": data}, f, indent=2)

    def load_baseline(self, filepath: str) -> None:
        """Loads baseline samples from JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)
            samples_data = payload.get("baseline", [])
            self.baseline_samples = [SampleMetric(**item) for item in samples_data]
