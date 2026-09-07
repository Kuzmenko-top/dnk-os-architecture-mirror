#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_soup_phase2_modules.py"
# purpose: "Unit tests for Soup Phase 2 modules: DriftAlarm and SconesExpect."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from core.orchestrator.drift_alarm import (
    DriftAlarm,
    DriftVerdict,
    SampleMetric,
)
from core.orchestrator.scones_expect import (
    RuleSeverity,
    SconesExpect,
)


# ==========================================
# 1. DriftAlarm Tests (Soup Drift-Alarm Pattern)
# ==========================================

def test_drift_alarm_stable_distribution():
    alarm = DriftAlarm(component_name="test_gemini", drift_threshold=0.20, min_samples=5)

    # 10 baseline samples around 150 chars, 400ms latency
    for i in range(10):
        alarm.record_baseline(
            SampleMetric(
                output_length=140 + (i % 20),
                latency_ms=380.0 + (i * 5),
                tools_called=["read_file", "search_files"],
            )
        )

    # 10 current samples with identical distribution
    for i in range(10):
        alarm.record_current(
            SampleMetric(
                output_length=142 + (i % 18),
                latency_ms=385.0 + (i * 4),
                tools_called=["read_file", "search_files"],
            )
        )

    report = alarm.evaluate()
    assert report.verdict == DriftVerdict.STABLE
    assert report.alarm_triggered is False
    assert report.overall_drift_score < 0.20


def test_drift_alarm_detects_length_drift():
    alarm = DriftAlarm(component_name="test_gemini", drift_threshold=0.20, min_samples=5)

    # Baseline: concise answers (100-150 chars)
    for _ in range(10):
        alarm.record_baseline(SampleMetric(output_length=120, latency_ms=200.0, tools_called=["read_file"]))

    # Current: suddenly verbose / hallucinating answers (1500-2000 chars)
    for _ in range(10):
        alarm.record_current(SampleMetric(output_length=1800, latency_ms=1200.0, tools_called=["read_file"]))

    report = alarm.evaluate()
    assert report.verdict in (DriftVerdict.DRIFT_DETECTED, DriftVerdict.CRITICAL_ANOMALY)
    assert report.alarm_triggered is True
    # Output length metric must have flagged drift
    len_metric = next(m for m in report.metrics if m.metric_name == "output_length")
    assert len_metric.has_drift is True


def test_drift_alarm_detects_tool_distribution_drift():
    alarm = DriftAlarm(component_name="test_gemini", drift_threshold=0.20, min_samples=5)

    for _ in range(10):
        alarm.record_baseline(SampleMetric(output_length=200, latency_ms=300.0, tools_called=["code_resolve"]))

    # Drastic tool shift: agent stopped calling code_resolve and calls terminal directly
    for _ in range(10):
        alarm.record_current(SampleMetric(output_length=200, latency_ms=300.0, tools_called=["terminal"]))

    report = alarm.evaluate()
    tool_metric = next(m for m in report.metrics if m.metric_name == "tool_calling_distribution")
    assert tool_metric.has_drift is True
    assert report.alarm_triggered is True


def test_drift_alarm_save_and_load_baseline(tmp_path):
    alarm = DriftAlarm(component_name="gemini_pro")
    for i in range(5):
        alarm.record_baseline(SampleMetric(output_length=100 + i, latency_ms=250.0 + i))

    file_path = str(tmp_path / "baseline.json")
    alarm.save_baseline(file_path)

    new_alarm = DriftAlarm(component_name="gemini_pro")
    new_alarm.load_baseline(file_path)

    assert len(new_alarm.baseline_samples) == 5
    assert new_alarm.baseline_samples[0].output_length == 100


# ==========================================
# 2. SconesExpect Tests (Soup Expect Pattern)
# ==========================================

def test_scones_expect_detects_absolute_path_violation():
    suite = SconesExpect(suite_name="path_hygiene")
    suite.add_rule(rule_type="no_absolute_paths", rule_id="relative_paths_only")

    # Failing code with hardcoded user path
    bad_code = "f = open('" + "/Users" + "/someone/secret.txt', 'r')"
    res_bad = suite.evaluate_artifact(bad_code)
    assert res_bad.passed is False
    assert res_bad.failed_rules == 1

    # Passing code with relative path
    good_code = "f = open('./docs/notes/050.md', 'r')"
    res_good = suite.evaluate_artifact(good_code)
    assert res_good.passed is True


def test_scones_expect_mrh_header_check():
    suite = SconesExpect(suite_name="mrh_hygiene")
    suite.add_rule(rule_type="require_mrh_header", rule_id="mandatory_mrh")

    code_without_header = "def hello(): return 'world'"
    assert suite.evaluate_artifact(code_without_header).passed is False

    code_with_header = (
        "# --- DNK-MRH-HEADER ---\n"
        "# mrh_id: 'test_file.py'\n"
        "# --- END DNK-MRH-HEADER ---\n"
        "def hello(): return 'world'"
    )
    assert suite.evaluate_artifact(code_with_header).passed is True


def test_scones_expect_memory_episode_validation():
    suite = SconesExpect(suite_name="memory_hygiene")
    suite.add_rule(rule_type="require_keys", keys=["topic", "content", "importance"])
    suite.add_rule(rule_type="field_min_length", field="content", min_length=15)
    suite.add_rule(rule_type="no_absolute_paths")

    valid_episode = {
        "topic": "FastAPI ORM",
        "content": "Always use async SQLAlchemy sessions with relative paths in ./apps/api/",
        "importance": 0.9,
    }
    assert suite.evaluate_memory_episode(valid_episode).passed is True

    invalid_episode = {
        "topic": "FastAPI",
        "content": "Too short",  # < 15 chars
        # missing importance
    }
    res = suite.evaluate_memory_episode(invalid_episode)
    assert res.passed is False
    assert res.failed_rules >= 1


def test_scones_expect_tool_sequence_trace():
    suite = SconesExpect(suite_name="agent_workflow_rules")
    suite.add_rule(
        rule_type="tool_called_before",
        first="scones_get_memories",
        second="write_file",
    )

    # Valid trace: memory checked first, then write_file
    valid_trace = [
        {"type": "tool", "tool": "scones_get_memories"},
        {"type": "tool", "tool": "write_file"},
    ]
    assert suite.evaluate_trace(valid_trace).passed is True

    # Invalid trace: write_file called before reading memory
    invalid_trace = [
        {"type": "tool", "tool": "write_file"},
        {"type": "tool", "tool": "scones_get_memories"},
    ]
    assert suite.evaluate_trace(invalid_trace).passed is False


def test_scones_expect_yaml_config_loading():
    yaml_rules = """
    suite_name: "production_governance"
    rules:
      - id: "no_abs"
        type: "no_absolute_paths"
        severity: "CRITICAL"
      - id: "forbid_secrets"
        type: "forbid_terms"
        severity: "CRITICAL"
        params:
          terms: ["AKIA", "sk_live_", "PRIVATE KEY"]
    """
    suite = SconesExpect().load_from_yaml(yaml_rules)
    assert suite.suite_name == "production_governance"
    assert len(suite.rules) == 2

    clean_content = "def test(): return True"
    assert suite.evaluate_artifact(clean_content).passed is True

    leaky_content = "aws_key = 'AKIA' + 'IOSFODNN7EXAMPLE'"
    assert suite.evaluate_artifact(leaky_content).passed is False
