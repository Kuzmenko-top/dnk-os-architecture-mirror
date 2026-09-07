#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "tests/services/test_drift_monitor.py"
# purpose: "Comprehensive unit tests for GeminiDriftMonitor (assimilated from Soup drift-alarm)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from services.dnk_analytics.drift_monitor import (
    AlarmSeverity,
    DriftAlarm,
    DriftMetricKind,
    GeminiDriftMonitor,
    OnlineBaselineTracker,
    OnlineMetricAccumulator,
    ResponseMetrics,
)


def test_calculate_metrics():
    text = "The quick brown fox jumps over the lazy dog. The quick brown fox."
    metrics = GeminiDriftMonitor.calculate_metrics(text)
    assert metrics.char_len == len(text)
    assert metrics.word_count == 13
    assert metrics.shannon_entropy > 2.0
    assert 0.0 < metrics.type_token_ratio < 1.0
    assert metrics.is_valid_json is True


def test_calculate_metrics_empty():
    metrics = GeminiDriftMonitor.calculate_metrics("")
    assert metrics.char_len == 0
    assert metrics.word_count == 0
    assert metrics.shannon_entropy == 0.0
    assert metrics.type_token_ratio == 0.0


def test_json_validity_detection():
    good_json = '{"status": "ok", "count": 42}'
    bad_json = '{"status": "ok", "count": 42'  # unclosed

    m_good = GeminiDriftMonitor.calculate_metrics(good_json)
    m_bad = GeminiDriftMonitor.calculate_metrics(bad_json)

    assert m_good.is_valid_json is True
    assert m_bad.is_valid_json is False


def test_drift_monitor_healthy_window():
    monitor = GeminiDriftMonitor()
    baseline_samples = [
        "This is an exemplary response explaining the system architecture in clear terms.",
        "Here is the second baseline sample demonstrating good vocabulary and structure.",
        "Third baseline sample providing rich technical details and clear explanations.",
    ]
    monitor.set_baseline(baseline_samples)

    # Window of similar characteristics
    monitor.record_response("Fourth sample explaining another technical feature with rich words.")
    monitor.record_response("Fifth sample demonstrating clear architectural structure and terms.")

    report = monitor.evaluate_drift()
    assert report.is_healthy is True
    assert len(report.alarms) == 0
    report_dict = report.to_dict()
    assert report_dict["is_healthy"] is True
    assert report_dict["alarm_count"] == 0


def test_entropy_collapse_alarm():
    monitor = GeminiDriftMonitor(entropy_drop_warning=0.20, entropy_drop_critical=0.35)
    baseline_samples = [
        "Natural language output with high variety of terms, expressions, and vocabulary.",
        "Another distinct sentence exploring diverse themes, algorithms, and concepts.",
        "Technical documentation describing complex orchestrator behaviors and modules.",
    ]
    monitor.set_baseline(baseline_samples)

    # Simulate loop/repetition collapse
    repetitive_text = "error error error error error error error error error error error error"
    monitor.record_response(repetitive_text)
    monitor.record_response(repetitive_text)

    report = monitor.evaluate_drift()
    assert any(a.metric == DriftMetricKind.ENTROPY_COLLAPSE for a in report.alarms)
    alarm = next(a for a in report.alarms if a.metric == DriftMetricKind.ENTROPY_COLLAPSE)
    assert alarm.severity in (AlarmSeverity.WARNING, AlarmSeverity.CRITICAL)


def test_json_corruption_alarm():
    monitor = GeminiDriftMonitor(json_failure_rate_critical=0.20)
    baseline_samples = [
        '{"status": "success", "result": 1}',
        '{"status": "success", "result": 2}',
    ]
    monitor.set_baseline(baseline_samples)

    # Feed corrupted JSONs
    monitor.record_response('{"status": broken json')
    monitor.record_response('{"bad": missing closing')

    report = monitor.evaluate_drift()
    assert report.is_healthy is False
    assert any(a.metric == DriftMetricKind.JSON_CORRUPTION for a in report.alarms)


def test_length_shift_alarm():
    monitor = GeminiDriftMonitor(length_z_warning=2.0, length_z_critical=3.0)
    baseline_samples = [
        "Short text A",
        "Short text B",
        "Short text C",
        "Short text D",
    ]
    monitor.set_baseline(baseline_samples)

    # Massive length explosion
    huge_text = "Word " * 500
    monitor.record_response(huge_text)

    report = monitor.evaluate_drift()
    assert any(a.metric == DriftMetricKind.LENGTH_SHIFT for a in report.alarms)


def test_online_metric_accumulator_welford_accuracy():
    import statistics

    values = [10.5, 23.2, 17.8, 42.0, 15.1, 8.4, 99.1, 33.3]
    acc = OnlineMetricAccumulator()
    for v in values:
        acc.update(v)

    assert acc.count == len(values)
    assert pytest.approx(acc.mean, rel=1e-5) == statistics.mean(values)
    assert pytest.approx(acc.variance, rel=1e-5) == statistics.variance(values)
    assert pytest.approx(acc.stdev, rel=1e-5) == statistics.stdev(values)


def test_online_metric_accumulator_ema():
    acc = OnlineMetricAccumulator(ema_alpha=0.5)
    acc.update(10.0)
    assert acc.ema_mean == 10.0
    assert acc.ema_stdev == 0.0

    acc.update(20.0)
    # ema_mean = 10.0 + 0.5 * (20 - 10) = 15.0
    assert pytest.approx(acc.ema_mean, rel=1e-5) == 15.0
    assert acc.ema_stdev > 0.0

    d = acc.to_dict()
    assert d["count"] == 2
    assert "ema_mean" in d
    assert "ema_stdev" in d


def test_online_baseline_tracker():
    tracker = OnlineBaselineTracker(ema_alpha=0.1)
    samples = [
        GeminiDriftMonitor.calculate_metrics("Short clean response 1"),
        GeminiDriftMonitor.calculate_metrics("Short clean response 2"),
        GeminiDriftMonitor.calculate_metrics('{"status": "ok", "code": 200}'),
    ]
    for s in samples:
        tracker.update(s)

    assert tracker.total_samples == 3
    summary = tracker.to_window_summary(use_ema=False)
    assert summary.sample_count == 3
    assert summary.mean_char_len > 0
    assert summary.mean_entropy > 0

    summary_ema = tracker.to_window_summary(use_ema=True)
    assert summary_ema.sample_count == 3

    tracker.reset()
    assert tracker.total_samples == 0
    empty_summary = tracker.to_window_summary()
    assert empty_summary.sample_count == 0


def test_drift_monitor_online_welford_baseline_drift():
    monitor = GeminiDriftMonitor()
    # Baseline via online streaming (O(1) memory, no baseline_history list growth)
    baseline_samples = [
        "This is a high quality response with distinct diverse vocabulary A.",
        "This is a high quality response with distinct diverse vocabulary B.",
        "This is a high quality response with distinct diverse vocabulary C.",
    ]
    for sample in baseline_samples:
        monitor.update_baseline_online(sample)

    assert len(monitor.baseline_history) == 0
    assert monitor.baseline_tracker.total_samples == 3

    # Window with repetitive collapse
    monitor.record_response("repeat repeat repeat repeat repeat repeat repeat")
    monitor.record_response("repeat repeat repeat repeat repeat repeat repeat")

    # Evaluate drift against online streaming baseline
    report = monitor.evaluate_drift(use_online_baseline=True)
    assert report.is_healthy is False
    assert any(a.metric == DriftMetricKind.ENTROPY_COLLAPSE for a in report.alarms)
    assert report.baseline is not None
    assert report.baseline.sample_count == 3


def test_drift_monitor_clear_baseline():
    monitor = GeminiDriftMonitor()
    monitor.set_baseline(["Sample A", "Sample B"])
    assert len(monitor.baseline_history) == 2
    assert monitor.baseline_tracker.total_samples == 2

    monitor.clear_baseline()
    assert len(monitor.baseline_history) == 0
    assert monitor.baseline_tracker.total_samples == 0

