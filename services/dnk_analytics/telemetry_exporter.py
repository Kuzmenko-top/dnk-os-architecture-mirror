# --- DNK-MRH-HEADER ---
# mrh_id: "services_dnk_analytics_telemetry_exporter"
# purpose: "Prometheus text protocol exposition and Visual Shell JSON telemetry exporter for Gemini drift and self-healing"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# --- END DNK-MRH-HEADER ---

import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from services.dnk_analytics.drift_monitor import GeminiDriftMonitor, DriftReport
    from core.orchestrator.gemini_self_heal import HealExecutionResult, GeminiSelfHealer


class GeminiTelemetryExporter:
    """Exports Gemini drift and self-healing telemetry in standard Prometheus exposition format
    and JSON payloads for DNK Visual Shell and Grafana dashboards.
    """

    def __init__(
        self,
        monitor: Optional["GeminiDriftMonitor"] = None,
        self_healer: Optional["GeminiSelfHealer"] = None,
        model_name: str = "gemini-2.5-pro",
    ) -> None:
        self.monitor = monitor
        self.self_healer = self_healer
        self.model_name = model_name

        # Cumulative event counters
        self.samples_total: int = 0
        self.drift_alarms_total: Dict[Tuple[str, str], int] = {}  # (alarm_type, severity) -> count
        self.self_healings_total: Dict[Tuple[str, str], int] = {}  # (strategy, status) -> count
        self.retries_total: int = 0

        # Last snapshot state
        self.last_report: Optional[Any] = None
        self.last_healing_result: Optional[Any] = None
        self.healing_history: List[Dict[str, Any]] = []

    def record_drift_report(self, report: "DriftReport") -> None:
        """Records a completed drift evaluation report and increments counters."""
        self.last_report = report
        if report.current_window:
            self.samples_total = max(self.samples_total, report.current_window.sample_count)
        for alarm in report.alarms:
            key = (alarm.metric.value, alarm.severity.value)
            self.drift_alarms_total[key] = self.drift_alarms_total.get(key, 0) + 1

    def record_healing_result(self, result: "HealExecutionResult") -> None:
        """Records a self-healing execution cycle outcome."""
        self.last_healing_result = result
        self.retries_total += max(0, result.total_attempts - 1)
        status = "success" if result.success else "failed"

        for action in result.healing_actions:
            key = (action, status)
            self.self_healings_total[key] = self.self_healings_total.get(key, 0) + 1

        self.healing_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success": result.success,
            "healed": result.healed,
            "total_attempts": result.total_attempts,
            "healing_actions": list(result.healing_actions),
        })
        # Keep last 50 events in history
        if len(self.healing_history) > 50:
            self.healing_history.pop(0)

    def export_prometheus_text(self) -> str:
        """Formats all collected metrics into standard Prometheus exposition format (version 0.0.4)."""
        lines: List[str] = []
        labels = f'model="{self.model_name}"'

        # Current window metrics
        cur_summary = None
        base_summary = None
        is_healthy = 1.0

        if self.last_report:
            cur_summary = self.last_report.current_window
            base_summary = self.last_report.baseline
            is_healthy = 1.0 if self.last_report.is_healthy else 0.0
        elif self.monitor and self.monitor.current_window:
            cur_summary = self.monitor._summarize(self.monitor.current_window)
            if self.monitor.baseline_history:
                base_summary = self.monitor._summarize(self.monitor.baseline_history)
            elif self.monitor.baseline_tracker.total_samples > 0:
                base_summary = self.monitor.baseline_tracker.to_window_summary()

        # Online tracker fallback
        tracker = self.monitor.baseline_tracker if self.monitor else None

        # 1. Shannon Entropy
        lines.append("# HELP dnk_gemini_entropy_mean Current window mean Shannon entropy")
        lines.append("# TYPE dnk_gemini_entropy_mean gauge")
        mean_entropy = cur_summary.mean_entropy if cur_summary else (tracker.entropy.mean if tracker else 0.0)
        lines.append(f"dnk_gemini_entropy_mean{{{labels}}} {mean_entropy:.4f}")

        lines.append("# HELP dnk_gemini_entropy_stdev Current window Shannon entropy standard deviation")
        lines.append("# TYPE dnk_gemini_entropy_stdev gauge")
        std_entropy = cur_summary.stdev_entropy if cur_summary else (tracker.entropy.stdev if tracker else 0.0)
        lines.append(f"dnk_gemini_entropy_stdev{{{labels}}} {std_entropy:.4f}")

        lines.append("# HELP dnk_gemini_entropy_ema Exponential moving average of Shannon entropy")
        lines.append("# TYPE dnk_gemini_entropy_ema gauge")
        ema_entropy = tracker.entropy.ema_mean if tracker else 0.0
        lines.append(f"dnk_gemini_entropy_ema{{{labels}}} {ema_entropy:.4f}")

        # 2. Character Length
        lines.append("# HELP dnk_gemini_char_length_mean Current window mean character length")
        lines.append("# TYPE dnk_gemini_char_length_mean gauge")
        mean_len = cur_summary.mean_char_len if cur_summary else (tracker.char_len.mean if tracker else 0.0)
        lines.append(f"dnk_gemini_char_length_mean{{{labels}}} {mean_len:.2f}")

        lines.append("# HELP dnk_gemini_char_length_stdev Current window character length standard deviation")
        lines.append("# TYPE dnk_gemini_char_length_stdev gauge")
        std_len = cur_summary.stdev_char_len if cur_summary else (tracker.char_len.stdev if tracker else 0.0)
        lines.append(f"dnk_gemini_char_length_stdev{{{labels}}} {std_len:.2f}")

        lines.append("# HELP dnk_gemini_char_length_ema Exponential moving average of character length")
        lines.append("# TYPE dnk_gemini_char_length_ema gauge")
        ema_len = tracker.char_len.ema_mean if tracker else 0.0
        lines.append(f"dnk_gemini_char_length_ema{{{labels}}} {ema_len:.2f}")

        # 3. Word Count
        lines.append("# HELP dnk_gemini_word_count_mean Current window mean word count")
        lines.append("# TYPE dnk_gemini_word_count_mean gauge")
        mean_words = cur_summary.mean_word_count if cur_summary else (tracker.word_count.mean if tracker else 0.0)
        lines.append(f"dnk_gemini_word_count_mean{{{labels}}} {mean_words:.2f}")

        lines.append("# HELP dnk_gemini_word_count_ema Exponential moving average of word count")
        lines.append("# TYPE dnk_gemini_word_count_ema gauge")
        ema_words = tracker.word_count.ema_mean if tracker else 0.0
        lines.append(f"dnk_gemini_word_count_ema{{{labels}}} {ema_words:.2f}")

        # 4. Type-Token Ratio (TTR)
        lines.append("# HELP dnk_gemini_ttr_mean Current window mean Type-Token Ratio (lexical diversity)")
        lines.append("# TYPE dnk_gemini_ttr_mean gauge")
        mean_ttr = cur_summary.mean_ttr if cur_summary else (tracker.ttr.mean if tracker else 0.0)
        lines.append(f"dnk_gemini_ttr_mean{{{labels}}} {mean_ttr:.4f}")

        lines.append("# HELP dnk_gemini_ttr_ema Exponential moving average of Type-Token Ratio")
        lines.append("# TYPE dnk_gemini_ttr_ema gauge")
        ema_ttr = tracker.ttr.ema_mean if tracker else 0.0
        lines.append(f"dnk_gemini_ttr_ema{{{labels}}} {ema_ttr:.4f}")

        # 5. JSON Validity Ratio
        lines.append("# HELP dnk_gemini_json_valid_ratio Ratio of outputs conforming to valid JSON syntax (0.0 to 1.0)")
        lines.append("# TYPE dnk_gemini_json_valid_ratio gauge")
        valid_ratio = cur_summary.json_valid_rate if cur_summary else (
            (tracker.valid_json_count / tracker.total_samples) if tracker and tracker.total_samples > 0 else 1.0
        )
        lines.append(f"dnk_gemini_json_valid_ratio{{{labels}}} {valid_ratio:.4f}")

        # 6. Overall Health Status
        lines.append("# HELP dnk_gemini_is_healthy 1 if window is healthy, 0 if drift alarms are active")
        lines.append("# TYPE dnk_gemini_is_healthy gauge")
        lines.append(f"dnk_gemini_is_healthy{{{labels}}} {is_healthy}")

        # 7. Total Samples Processed
        lines.append("# HELP dnk_gemini_samples_total Total count of outputs analyzed by drift monitor")
        lines.append("# TYPE dnk_gemini_samples_total counter")
        total_samples = max(self.samples_total, tracker.total_samples if tracker else 0)
        lines.append(f"dnk_gemini_samples_total{{{labels}}} {total_samples}")

        # 8. Active Alarms
        lines.append("# HELP dnk_gemini_drift_alarm_active 1 if specific drift alarm type is currently active, 0 otherwise")
        lines.append("# TYPE dnk_gemini_drift_alarm_active gauge")
        active_types = {a.metric.value for a in self.last_report.alarms} if self.last_report else set()
        for atype in ["length_shift", "entropy_collapse", "json_corruption"]:
            is_active = 1.0 if atype in active_types else 0.0
            lines.append(f'dnk_gemini_drift_alarm_active{{{labels},alarm_type="{atype}"}} {is_active}')

        # 9. Cumulative Drift Alarms
        lines.append("# HELP dnk_gemini_drift_alarms_total Cumulative count of drift alarms triggered")
        lines.append("# TYPE dnk_gemini_drift_alarms_total counter")
        if self.drift_alarms_total:
            for (atype, sev), count in sorted(self.drift_alarms_total.items()):
                lines.append(f'dnk_gemini_drift_alarms_total{{{labels},alarm_type="{atype}",severity="{sev}"}} {count}')
        else:
            lines.append(f'dnk_gemini_drift_alarms_total{{{labels},alarm_type="none",severity="none"}} 0')

        # 10. Cumulative Self-Healing Executions
        lines.append("# HELP dnk_gemini_self_healings_total Cumulative count of self-healing operations executed")
        lines.append("# TYPE dnk_gemini_self_healings_total counter")
        if self.self_healings_total:
            for (strat, st), count in sorted(self.self_healings_total.items()):
                lines.append(f'dnk_gemini_self_healings_total{{{labels},strategy="{strat}",status="{st}"}} {count}')
        else:
            lines.append(f'dnk_gemini_self_healings_total{{{labels},strategy="none",status="none"}} 0')

        # 11. Retries Total
        lines.append("# HELP dnk_gemini_retries_total Cumulative count of retry attempts executed during healing")
        lines.append("# TYPE dnk_gemini_retries_total counter")
        lines.append(f"dnk_gemini_retries_total{{{labels}}} {self.retries_total}")

        lines.append("")
        return "\n".join(lines)

    def export_visual_shell_telemetry(self) -> Dict[str, Any]:
        """Produces a structured JSON dictionary tailored for DNK Visual Shell and Grafana dashboards."""
        tracker = self.monitor.baseline_tracker if self.monitor else None
        cur_summary = None
        base_summary = None
        is_healthy = True
        alarms_list: List[Dict[str, Any]] = []

        if self.last_report:
            cur_summary = self.last_report.current_window
            base_summary = self.last_report.baseline
            is_healthy = self.last_report.is_healthy
            alarms_list = [
                {
                    "metric": a.metric.value,
                    "severity": a.severity.value,
                    "baseline_value": a.baseline_value,
                    "current_value": a.current_value,
                    "delta_or_z": a.delta_or_z,
                    "message": a.message,
                }
                for a in self.last_report.alarms
            ]
        elif self.monitor and self.monitor.current_window:
            cur_summary = self.monitor._summarize(self.monitor.current_window)
            if self.monitor.baseline_history:
                base_summary = self.monitor._summarize(self.monitor.baseline_history)
            elif tracker and tracker.total_samples > 0:
                base_summary = tracker.to_window_summary()

        status_str = "HEALTHY"
        if not is_healthy:
            status_str = "CRITICAL" if any(str(a.get("severity", "")).upper() == "CRITICAL" for a in alarms_list) else "WARNING"

        window_count = len(self.monitor.current_window) if self.monitor else 0
        total_samples = max(self.samples_total, tracker.total_samples if tracker else 0, window_count)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": self.model_name,
            "model_name": self.model_name,
            "status": status_str,
            "is_healthy": is_healthy,
            "summary": {
                "total_samples": total_samples,
                "window_samples": cur_summary.sample_count if cur_summary else window_count,
                "active_alarms_count": len(alarms_list),
                "total_alarms_count": sum(self.drift_alarms_total.values()),
                "total_healings_count": sum(self.self_healings_total.values()),
                "total_retries_count": self.retries_total,
            },
            "metrics": {
                "entropy": {
                    "current_mean": cur_summary.mean_entropy if cur_summary else 0.0,
                    "current_stdev": cur_summary.stdev_entropy if cur_summary else 0.0,
                    "ema": round(tracker.entropy.ema_mean, 4) if tracker else 0.0,
                    "baseline_mean": base_summary.mean_entropy if base_summary else None,
                    "baseline_stdev": base_summary.stdev_entropy if base_summary else None,
                },
                "char_length": {
                    "current_mean": cur_summary.mean_char_len if cur_summary else 0.0,
                    "current_stdev": cur_summary.stdev_char_len if cur_summary else 0.0,
                    "ema": round(tracker.char_len.ema_mean, 2) if tracker else 0.0,
                    "baseline_mean": base_summary.mean_char_len if base_summary else None,
                    "baseline_stdev": base_summary.stdev_char_len if base_summary else None,
                },
                "char_len": {
                    "current_mean": cur_summary.mean_char_len if cur_summary else 0.0,
                    "current_stdev": cur_summary.stdev_char_len if cur_summary else 0.0,
                    "ema": round(tracker.char_len.ema_mean, 2) if tracker else 0.0,
                    "baseline_mean": base_summary.mean_char_len if base_summary else None,
                    "baseline_stdev": base_summary.stdev_char_len if base_summary else None,
                },
                "word_count": {
                    "current_mean": cur_summary.mean_word_count if cur_summary else 0.0,
                    "ema": round(tracker.word_count.ema_mean, 2) if tracker else 0.0,
                    "baseline_mean": base_summary.mean_word_count if base_summary else None,
                },
                "ttr": {
                    "current_mean": cur_summary.mean_ttr if cur_summary else 0.0,
                    "ema": round(tracker.ttr.ema_mean, 4) if tracker else 0.0,
                    "baseline_mean": base_summary.mean_ttr if base_summary else None,
                },
                "json_valid_ratio": {
                    "current": cur_summary.json_valid_rate if cur_summary else 1.0,
                    "baseline": base_summary.json_valid_rate if base_summary else 1.0,
                },
            },
            "welford_stats": {
                "char_length": tracker.char_len.to_dict() if tracker else None,
                "word_count": tracker.word_count.to_dict() if tracker else None,
                "entropy": tracker.entropy.to_dict() if tracker else None,
                "ttr": tracker.ttr.to_dict() if tracker else None,
            },
            "welford_online": {
                "char_length": tracker.char_len.to_dict() if tracker else None,
                "word_count": tracker.word_count.to_dict() if tracker else None,
                "entropy": tracker.entropy.to_dict() if tracker else None,
                "ttr": tracker.ttr.to_dict() if tracker else None,
            },
            "active_alarms": alarms_list,
            "healing": {
                "total_healed": sum(1 for h in self.healing_history if h.get("healed")),
                "last_healed": self.last_healing_result.healed if self.last_healing_result else None,
                "strategies_used": {
                    strat: count for (strat, st), count in self.self_healings_total.items() if st == "success"
                },
                "cumulative_counts": {
                    f"{strat}_{st}": count for (strat, st), count in self.self_healings_total.items()
                },
                "recent_history": list(self.healing_history[-10:]),
            },
            "self_healing": {
                "cumulative_counts": {
                    f"{strat}_{st}": count for (strat, st), count in self.self_healings_total.items()
                },
                "recent_history": list(self.healing_history[-10:]),
            },
        }


# Global singleton instance for easy cross-module import
default_telemetry_exporter = GeminiTelemetryExporter()
gemini_telemetry_exporter = default_telemetry_exporter

__all__ = [
    "GeminiTelemetryExporter",
    "default_telemetry_exporter",
    "gemini_telemetry_exporter",
]
