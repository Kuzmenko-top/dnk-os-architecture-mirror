#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_analytics/drift_monitor.py"
# purpose: "Statistical & Entropy Drift Alarm Monitor for Google Gemini LLM responses, assimilated from Soup drift-alarm."
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
import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

logger = logging.getLogger("dnk_gemini_drift_monitor")


class AlarmSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class DriftMetricKind(str, Enum):
    LENGTH_SHIFT = "length_shift"
    ENTROPY_COLLAPSE = "entropy_collapse"
    LEXICAL_DIVERSITY = "lexical_diversity"
    JSON_CORRUPTION = "json_corruption"


@dataclass
class ResponseMetrics:
    text: str
    char_len: int
    word_count: int
    shannon_entropy: float
    type_token_ratio: float
    is_valid_json: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DriftAlarm:
    metric: DriftMetricKind
    severity: AlarmSeverity
    baseline_value: float
    current_value: float
    delta_or_z: float
    message: str


@dataclass
class WindowSummary:
    sample_count: int
    mean_char_len: float
    stdev_char_len: float
    mean_word_count: float
    mean_entropy: float
    stdev_entropy: float
    mean_ttr: float
    json_valid_rate: float


@dataclass
class DriftReport:
    is_healthy: bool
    alarms: List[DriftAlarm]
    baseline: Optional[WindowSummary]
    current_window: WindowSummary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_healthy": self.is_healthy,
            "alarm_count": len(self.alarms),
            "alarms": [
                {
                    "metric": a.metric.value,
                    "severity": a.severity.value,
                    "baseline_value": round(a.baseline_value, 4),
                    "current_value": round(a.current_value, 4),
                    "delta_or_z": round(a.delta_or_z, 4),
                    "message": a.message,
                }
                for a in self.alarms
            ],
            "baseline": self.baseline.__dict__ if self.baseline else None,
            "current_window": self.current_window.__dict__,
        }


@dataclass
class OnlineMetricAccumulator:
    """Computes online mean, sample variance, and exponential moving average (EMA) with O(1) memory.
    Implements Welford's algorithm for numerically stable running variance.
    """
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0
    ema_mean: float = 0.0
    ema_var: float = 0.0
    ema_alpha: float = 0.05

    def update(self, val: float) -> None:
        self.count += 1
        delta = val - self.mean
        self.mean += delta / self.count
        delta2 = val - self.mean
        self.m2 += delta * delta2

        # EMA tracking
        if self.count == 1:
            self.ema_mean = val
            self.ema_var = 0.0
        else:
            delta_ema = val - self.ema_mean
            self.ema_mean += self.ema_alpha * delta_ema
            self.ema_var = (1.0 - self.ema_alpha) * (self.ema_var + self.ema_alpha * (delta_ema**2))

    @property
    def variance(self) -> float:
        return self.m2 / (self.count - 1) if self.count > 1 else 0.0

    @property
    def stdev(self) -> float:
        return math.sqrt(self.variance)

    @property
    def ema_stdev(self) -> float:
        return math.sqrt(max(0.0, self.ema_var))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "mean": round(self.mean, 4),
            "stdev": round(self.stdev, 4),
            "ema_mean": round(self.ema_mean, 4),
            "ema_stdev": round(self.ema_stdev, 4),
        }


@dataclass
class OnlineBaselineTracker:
    """Maintains running statistical distribution of model outputs across multiple dimensions in O(1) space."""
    ema_alpha: float = 0.05
    char_len: OnlineMetricAccumulator = field(default_factory=OnlineMetricAccumulator)
    word_count: OnlineMetricAccumulator = field(default_factory=OnlineMetricAccumulator)
    entropy: OnlineMetricAccumulator = field(default_factory=OnlineMetricAccumulator)
    ttr: OnlineMetricAccumulator = field(default_factory=OnlineMetricAccumulator)
    total_samples: int = 0
    valid_json_count: int = 0

    def __post_init__(self) -> None:
        self.char_len.ema_alpha = self.ema_alpha
        self.word_count.ema_alpha = self.ema_alpha
        self.entropy.ema_alpha = self.ema_alpha
        self.ttr.ema_alpha = self.ema_alpha

    def update(self, metrics: ResponseMetrics) -> None:
        self.total_samples += 1
        self.char_len.update(float(metrics.char_len))
        self.word_count.update(float(metrics.word_count))
        self.entropy.update(float(metrics.shannon_entropy))
        self.ttr.update(float(metrics.type_token_ratio))
        if metrics.is_valid_json:
            self.valid_json_count += 1

    def to_window_summary(self, use_ema: bool = False) -> WindowSummary:
        if self.total_samples == 0:
            return WindowSummary(
                sample_count=0,
                mean_char_len=0.0,
                stdev_char_len=0.0,
                mean_word_count=0.0,
                mean_entropy=0.0,
                stdev_entropy=0.0,
                mean_ttr=0.0,
                json_valid_rate=1.0,
            )

        mean_len = self.char_len.ema_mean if use_ema else self.char_len.mean
        std_len = self.char_len.ema_stdev if use_ema else self.char_len.stdev
        mean_words = self.word_count.ema_mean if use_ema else self.word_count.mean
        mean_ent = self.entropy.ema_mean if use_ema else self.entropy.mean
        std_ent = self.entropy.ema_stdev if use_ema else self.entropy.stdev
        mean_t = self.ttr.ema_mean if use_ema else self.ttr.mean
        valid_rate = self.valid_json_count / self.total_samples

        return WindowSummary(
            sample_count=self.total_samples,
            mean_char_len=round(mean_len, 2),
            stdev_char_len=round(std_len, 2),
            mean_word_count=round(mean_words, 2),
            mean_entropy=round(mean_ent, 4),
            stdev_entropy=round(std_ent, 4),
            mean_ttr=round(mean_t, 4),
            json_valid_rate=round(valid_rate, 4),
        )

    def reset(self) -> None:
        self.total_samples = 0
        self.valid_json_count = 0
        self.char_len = OnlineMetricAccumulator(ema_alpha=self.ema_alpha)
        self.word_count = OnlineMetricAccumulator(ema_alpha=self.ema_alpha)
        self.entropy = OnlineMetricAccumulator(ema_alpha=self.ema_alpha)
        self.ttr = OnlineMetricAccumulator(ema_alpha=self.ema_alpha)


class GeminiDriftMonitor:
    """Monitors statistical, lexical, and structural drift in Google Gemini outputs over time.
    Assimilated from MakazhanAlpamys/Soup drift-alarm architecture.
    Detects length shifts, entropy collapse (repetition loops), and JSON syntax degeneration.
    Supports both batch window analysis and streaming O(1) online baselines via Welford + EMA.
    """

    def __init__(
        self,
        length_z_warning: float = 2.5,
        length_z_critical: float = 3.5,
        entropy_drop_warning: float = 0.15,
        entropy_drop_critical: float = 0.30,
        json_failure_rate_critical: float = 0.10,
        ema_alpha: float = 0.05,
    ) -> None:
        self.length_z_warning = length_z_warning
        self.length_z_critical = length_z_critical
        self.entropy_drop_warning = entropy_drop_warning
        self.entropy_drop_critical = entropy_drop_critical
        self.json_failure_rate_critical = json_failure_rate_critical
        self.ema_alpha = ema_alpha

        self.baseline_history: List[ResponseMetrics] = []
        self.current_window: List[ResponseMetrics] = []
        self.baseline_tracker = OnlineBaselineTracker(ema_alpha=ema_alpha)

    @staticmethod
    def calculate_metrics(text: str, metadata: Optional[Dict[str, Any]] = None) -> ResponseMetrics:
        """Computes statistical and information-theoretic metrics for a single response."""
        char_len = len(text)
        tokens = re.findall(r"\w+", text.lower())
        word_count = len(tokens)

        if word_count == 0:
            shannon_entropy = 0.0
            ttr = 0.0
        else:
            counts = Counter(tokens)
            probs = [cnt / word_count for cnt in counts.values()]
            shannon_entropy = -sum(p * math.log2(p) for p in probs)
            ttr = len(counts) / word_count

        # Check JSON validity if text looks like JSON
        is_valid_json = True
        trimmed = text.strip()
        if trimmed.startswith("{") or trimmed.startswith("["):
            try:
                json.loads(trimmed)
                is_valid_json = True
            except Exception:
                is_valid_json = False

        return ResponseMetrics(
            text=text,
            char_len=char_len,
            word_count=word_count,
            shannon_entropy=shannon_entropy,
            type_token_ratio=ttr,
            is_valid_json=is_valid_json,
            metadata=metadata or {},
        )

    def set_baseline(self, samples: Sequence[str]) -> WindowSummary:
        """Establishes baseline distribution parameters from verified benchmark outputs."""
        self.baseline_history = [self.calculate_metrics(s) for s in samples]
        self.baseline_tracker.reset()
        for m in self.baseline_history:
            self.baseline_tracker.update(m)
        return self._summarize(self.baseline_history)

    def update_baseline_online(
        self, text_or_metrics: Union[str, ResponseMetrics], metadata: Optional[Dict[str, Any]] = None
    ) -> ResponseMetrics:
        """Online streaming update of baseline distribution using Welford's algorithm and EMA in O(1) space."""
        if isinstance(text_or_metrics, str):
            metrics = self.calculate_metrics(text_or_metrics, metadata)
        else:
            metrics = text_or_metrics
        self.baseline_tracker.update(metrics)
        return metrics

    def clear_baseline(self) -> None:
        """Clears both batch baseline history and online baseline tracker."""
        self.baseline_history.clear()
        self.baseline_tracker.reset()

    def record_response(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> ResponseMetrics:
        """Records a live response into the sliding inspection window."""
        metrics = self.calculate_metrics(text, metadata)
        self.current_window.append(metrics)
        return metrics

    def clear_current_window(self) -> None:
        """Clears the evaluation window for the next batch."""
        self.current_window.clear()

    @staticmethod
    def _summarize(samples: Sequence[ResponseMetrics]) -> WindowSummary:
        if not samples:
            return WindowSummary(
                sample_count=0,
                mean_char_len=0.0,
                stdev_char_len=0.0,
                mean_word_count=0.0,
                mean_entropy=0.0,
                stdev_entropy=0.0,
                mean_ttr=0.0,
                json_valid_rate=1.0,
            )

        n = len(samples)
        char_lens = [s.char_len for s in samples]
        word_counts = [s.word_count for s in samples]
        entropies = [s.shannon_entropy for s in samples]
        ttrs = [s.type_token_ratio for s in samples]
        json_valid = [1 if s.is_valid_json else 0 for s in samples]

        mean_char = statistics.mean(char_lens)
        stdev_char = statistics.stdev(char_lens) if n > 1 else 0.0

        mean_words = statistics.mean(word_counts)
        mean_ent = statistics.mean(entropies)
        stdev_ent = statistics.stdev(entropies) if n > 1 else 0.0

        mean_t = statistics.mean(ttrs)
        valid_rate = sum(json_valid) / n

        return WindowSummary(
            sample_count=n,
            mean_char_len=mean_char,
            stdev_char_len=stdev_char,
            mean_word_count=mean_words,
            mean_entropy=mean_ent,
            stdev_entropy=stdev_ent,
            mean_ttr=mean_t,
            json_valid_rate=valid_rate,
        )

    def evaluate_drift(self, use_online_baseline: bool = False, use_ema: bool = False) -> DriftReport:
        """Analyzes current window against baseline to detect drift anomalies and alarms.
        Supports evaluation against batch baseline history or O(1) online baseline tracker (Welford or EMA).
        """
        cur_summary = self._summarize(self.current_window)
        alarms: List[DriftAlarm] = []

        if use_online_baseline or (not self.baseline_history and self.baseline_tracker.total_samples > 0):
            base_summary = self.baseline_tracker.to_window_summary(use_ema=use_ema)
        elif self.baseline_history:
            base_summary = self._summarize(self.baseline_history)
        else:
            base_summary = None

        if not base_summary or base_summary.sample_count == 0 or cur_summary.sample_count == 0:
            return DriftReport(
                is_healthy=True,
                alarms=[],
                baseline=base_summary,
                current_window=cur_summary,
            )

        # 1. Length Shift (Z-Score with variance floor)
        stdev_floor = max(base_summary.stdev_char_len, max(2.0, 0.15 * base_summary.mean_char_len))
        z_len = (cur_summary.mean_char_len - base_summary.mean_char_len) / stdev_floor
        abs_z = abs(z_len)
        if abs_z >= self.length_z_critical:
            alarms.append(
                DriftAlarm(
                    metric=DriftMetricKind.LENGTH_SHIFT,
                    severity=AlarmSeverity.CRITICAL,
                    baseline_value=base_summary.mean_char_len,
                    current_value=cur_summary.mean_char_len,
                    delta_or_z=z_len,
                    message=f"Critical length drift detected: Z={z_len:.2f} (mean {cur_summary.mean_char_len:.1f} vs baseline {base_summary.mean_char_len:.1f})",
                )
            )
        elif abs_z >= self.length_z_warning:
            alarms.append(
                DriftAlarm(
                    metric=DriftMetricKind.LENGTH_SHIFT,
                    severity=AlarmSeverity.WARNING,
                    baseline_value=base_summary.mean_char_len,
                    current_value=cur_summary.mean_char_len,
                    delta_or_z=z_len,
                    message=f"Warning length drift detected: Z={z_len:.2f} (mean {cur_summary.mean_char_len:.1f} vs baseline {base_summary.mean_char_len:.1f})",
                )
            )

        # 2. Entropy Collapse (Repetition / Mode collapse)
        if base_summary.mean_entropy > 0:
            rel_entropy_drop = (base_summary.mean_entropy - cur_summary.mean_entropy) / base_summary.mean_entropy
            if rel_entropy_drop >= self.entropy_drop_critical:
                alarms.append(
                    DriftAlarm(
                        metric=DriftMetricKind.ENTROPY_COLLAPSE,
                        severity=AlarmSeverity.CRITICAL,
                        baseline_value=base_summary.mean_entropy,
                        current_value=cur_summary.mean_entropy,
                        delta_or_z=rel_entropy_drop,
                        message=f"Critical entropy collapse: {rel_entropy_drop * 100:.1f}% drop (current {cur_summary.mean_entropy:.2f} bits vs base {base_summary.mean_entropy:.2f} bits)",
                    )
                )
            elif rel_entropy_drop >= self.entropy_drop_warning:
                alarms.append(
                    DriftAlarm(
                        metric=DriftMetricKind.ENTROPY_COLLAPSE,
                        severity=AlarmSeverity.WARNING,
                        baseline_value=base_summary.mean_entropy,
                        current_value=cur_summary.mean_entropy,
                        delta_or_z=rel_entropy_drop,
                        message=f"Warning entropy drop: {rel_entropy_drop * 100:.1f}% drop (current {cur_summary.mean_entropy:.2f} bits vs base {base_summary.mean_entropy:.2f} bits)",
                    )
                )

        # 3. JSON Corruption
        json_failure_rate = 1.0 - cur_summary.json_valid_rate
        if json_failure_rate >= self.json_failure_rate_critical:
            alarms.append(
                DriftAlarm(
                    metric=DriftMetricKind.JSON_CORRUPTION,
                    severity=AlarmSeverity.CRITICAL,
                    baseline_value=base_summary.json_valid_rate,
                    current_value=cur_summary.json_valid_rate,
                    delta_or_z=json_failure_rate,
                    message=f"Critical JSON corruption rate: {json_failure_rate * 100:.1f}% responses failed JSON validation",
                )
            )

        is_healthy = not any(a.severity == AlarmSeverity.CRITICAL for a in alarms)
        return DriftReport(
            is_healthy=is_healthy,
            alarms=alarms,
            baseline=base_summary,
            current_window=cur_summary,
        )

    def get_telemetry_exporter(self, model_name: str = "gemini-2.5-pro") -> Any:
        """Returns a configured GeminiTelemetryExporter for this drift monitor."""
        from services.dnk_analytics.telemetry_exporter import GeminiTelemetryExporter
        return GeminiTelemetryExporter(monitor=self, model_name=model_name)

    def export_prometheus_text(self, model_name: str = "gemini-2.5-pro") -> str:
        """Exports current monitor metrics in Prometheus exposition text format."""
        return self.get_telemetry_exporter(model_name=model_name).export_prometheus_text()

    def export_visual_shell_telemetry(self, model_name: str = "gemini-2.5-pro") -> Dict[str, Any]:
        """Exports structured JSON telemetry dictionary for DNK Visual Shell and Grafana."""
        return self.get_telemetry_exporter(model_name=model_name).export_visual_shell_telemetry()

