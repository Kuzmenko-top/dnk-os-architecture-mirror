# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_gemini_self_heal.py"
# purpose: "Unit and integration tests for GeminiSelfHealer auto-heal and fallback loop."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
from typing import Any, Dict

from core.orchestrator.gemini_self_heal import (
    GeminiSelfHealer,
    HealActionType,
)
from services.dnk_analytics.drift_monitor import (
    AlarmSeverity,
    DriftAlarm,
    DriftMetricKind,
    DriftReport,
    GeminiDriftMonitor,
    WindowSummary,
)


def _make_dummy_summary() -> WindowSummary:
    return WindowSummary(
        sample_count=5,
        mean_char_len=100.0,
        stdev_char_len=10.0,
        mean_word_count=15.0,
        mean_entropy=4.2,
        stdev_entropy=0.2,
        mean_ttr=0.8,
        json_valid_rate=1.0,
    )


def test_repair_json_string_direct_valid():
    healer = GeminiSelfHealer()
    success, parsed, text = healer.repair_json_string('{"status": "ok", "count": 10}')
    assert success is True
    assert parsed == {"status": "ok", "count": 10}
    assert text == '{"status": "ok", "count": 10}'


def test_repair_json_string_markdown_fences():
    healer = GeminiSelfHealer()
    raw = """Here is your output:
```json
{
  "key": "value",
  "num": 42
}
```
Hope this helps!"""
    success, parsed, text = healer.repair_json_string(raw)
    assert success is True
    assert parsed is not None
    assert parsed["key"] == "value"
    assert parsed["num"] == 42


def test_repair_json_string_trailing_commas_and_literals():
    healer = GeminiSelfHealer()
    raw = '{"active": True, "data": [1, 2, ], "missing": None, }'
    success, parsed, text = healer.repair_json_string(raw)
    assert success is True
    assert parsed == {"active": True, "data": [1, 2], "missing": None}


def test_repair_json_string_unquoted_keys():
    healer = GeminiSelfHealer()
    raw = '{ name: "alpha", code: 200 }'
    success, parsed, text = healer.repair_json_string(raw)
    assert success is True
    assert parsed == {"name": "alpha", "code": 200}


def test_diagnose_json_corruption_triggers_local_repair():
    healer = GeminiSelfHealer(auto_local_repair=True)
    report = DriftReport(
        is_healthy=False,
        alarms=[
            DriftAlarm(
                metric=DriftMetricKind.JSON_CORRUPTION,
                severity=AlarmSeverity.CRITICAL,
                baseline_value=1.0,
                current_value=0.0,
                delta_or_z=1.0,
                message="JSON parse failed",
            )
        ],
        baseline=_make_dummy_summary(),
        current_window=_make_dummy_summary(),
    )
    plan = healer.diagnose(
        report=report,
        current_params={"temperature": 0.7},
        attempt=1,
        raw_text='```json\n{"healed": true}\n```',
    )
    assert plan.action_type == HealActionType.LOCAL_JSON_HEAL
    assert plan.local_repaired_content == '{"healed": true}'


def test_diagnose_entropy_collapse_resets_temperature():
    healer = GeminiSelfHealer(safe_temperature=0.1)
    report = DriftReport(
        is_healthy=False,
        alarms=[
            DriftAlarm(
                metric=DriftMetricKind.ENTROPY_COLLAPSE,
                severity=AlarmSeverity.CRITICAL,
                baseline_value=4.5,
                current_value=1.2,
                delta_or_z=0.73,
                message="Entropy collapsed",
            )
        ],
        baseline=_make_dummy_summary(),
        current_window=_make_dummy_summary(),
    )
    plan = healer.diagnose(
        report=report,
        current_params={"temperature": 0.8},
        attempt=1,
        raw_text="the the the the the",
    )
    assert plan.action_type == HealActionType.RESET_TEMPERATURE
    assert plan.suggested_params["temperature"] == 0.1
    assert "Repetitive loops detected" in (plan.retry_prompt_modifier or "")


def test_diagnose_length_shift_constrains_prompt():
    healer = GeminiSelfHealer()
    report = DriftReport(
        is_healthy=False,
        alarms=[
            DriftAlarm(
                metric=DriftMetricKind.LENGTH_SHIFT,
                severity=AlarmSeverity.CRITICAL,
                baseline_value=100.0,
                current_value=1200.0,
                delta_or_z=4.2,
                message="Massive output length explosion",
            )
        ],
        baseline=_make_dummy_summary(),
        current_window=_make_dummy_summary(),
    )
    plan = healer.diagnose(
        report=report,
        current_params={"temperature": 0.7},
        attempt=1,
        raw_text="A" * 1200,
    )
    assert plan.action_type == HealActionType.LENGTH_CONSTRAIN_PROMPT
    assert "Limit response strictly" in (plan.retry_prompt_modifier or "")


def test_diagnose_fallback_model_after_max_retries():
    healer = GeminiSelfHealer(fallback_model="nvidia_nim/codestral", max_retries=2)
    report = DriftReport(
        is_healthy=False,
        alarms=[
            DriftAlarm(
                metric=DriftMetricKind.JSON_CORRUPTION,
                severity=AlarmSeverity.CRITICAL,
                baseline_value=1.0,
                current_value=0.0,
                delta_or_z=1.0,
                message="Persistent JSON syntax failure",
            )
        ],
        baseline=_make_dummy_summary(),
        current_window=_make_dummy_summary(),
    )
    plan = healer.diagnose(
        report=report,
        current_params={"model": "gemini-flash", "temperature": 0.5},
        attempt=2,
        raw_text="Unfixable garbage text !@#$",
    )
    assert plan.action_type == HealActionType.FALLBACK_MODEL
    assert plan.suggested_params["model"] == "nvidia_nim/codestral"


def test_execute_with_healing_healthy_first_try():
    healer = GeminiSelfHealer()

    def mock_call(params: Dict[str, Any]) -> str:
        return "This is a diverse, high quality and informative response for the user with good vocabulary."

    result = healer.execute_with_healing(mock_call, {"prompt": "Tell me something"}, expect_json=False)
    assert result.success is True
    assert result.total_attempts == 1
    assert result.healed is False
    assert len(result.attempts) == 1
    assert result.attempts[0].is_healthy is True


def test_execute_with_healing_local_repair():
    healer = GeminiSelfHealer()

    def mock_call(params: Dict[str, Any]) -> str:
        return '```json\n{\n  "status": "ready",\n  "tasks": [1, 2, ],\n}\n```'

    result = healer.execute_with_healing(mock_call, {"prompt": "Get status"}, expect_json=True)
    assert result.success is True
    assert result.healed is True
    assert result.parsed_json == {"status": "ready", "tasks": [1, 2]}
    assert result.total_attempts == 1


def test_execute_with_healing_entropy_collapse_retry():
    healer = GeminiSelfHealer()
    calls = []

    def mock_call(params: Dict[str, Any]) -> str:
        calls.append(dict(params))
        if len(calls) == 1:
            # First attempt: repetitive loop
            return "the " * 50
        # Second attempt: after temperature reset & prompt modifier
        assert params.get("temperature") == healer.safe_temperature
        return "Now providing a clean and structured response without token repetition."

    result = healer.execute_with_healing(
        mock_call,
        {"prompt": "Generate text", "temperature": 0.8},
        expect_json=False,
    )
    assert result.success is True
    assert result.healed is True
    assert result.total_attempts == 2
    assert len(calls) == 2


def test_execute_with_healing_broken_json_retry_until_fixed():
    healer = GeminiSelfHealer(auto_local_repair=False)
    calls = []

    def mock_call(params: Dict[str, Any]) -> str:
        calls.append(dict(params))
        if len(calls) == 1:
            # Completely unparseable text
            return "Sure! Here is the data: I am an AI and cannot format it properly."
        # Second attempt: follows the error correction
        return '{"result": "success", "items_processed": 5}'

    result = healer.execute_with_healing(
        mock_call,
        {"prompt": "Return JSON", "temperature": 0.7},
        expect_json=True,
    )
    assert result.success is True
    assert result.healed is True
    assert result.total_attempts == 2
    assert result.parsed_json == {"result": "success", "items_processed": 5}


def test_execute_with_healing_online_baseline_mode():
    monitor = GeminiDriftMonitor()
    # Baseline via O(1) streaming updates
    for sample in [
        "Structured normal output alpha with variety.",
        "Structured normal output beta with variety.",
        "Structured normal output gamma with variety.",
    ]:
        monitor.update_baseline_online(sample)

    healer = GeminiSelfHealer(monitor=monitor, use_online_baseline=True)
    calls = []

    def mock_call(params: Dict[str, Any]) -> str:
        calls.append(dict(params))
        if len(calls) == 1:
            return "stuck " * 40  # Repetition triggers collapse against online baseline
        return "Structured normal output delta with variety."

    result = healer.execute_with_healing(
        mock_call,
        {"prompt": "Generate response", "temperature": 0.8},
        expect_json=False,
    )
    assert result.success is True
    assert result.healed is True
    assert result.total_attempts == 2
    assert monitor.baseline_tracker.total_samples == 3
    assert len(monitor.baseline_history) == 0

