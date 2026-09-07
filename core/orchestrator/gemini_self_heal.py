# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/gemini_self_heal.py"
# purpose: "Autonomous Auto-Heal & Fallback Loop linking GeminiDriftMonitor with retry & parameter adaptation."
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
import re
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from services.dnk_analytics.drift_monitor import (
    AlarmSeverity,
    DriftAlarm,
    DriftMetricKind,
    DriftReport,
    GeminiDriftMonitor,
    ResponseMetrics,
)

logger = logging.getLogger("dnk_gemini_self_heal")


class HealActionType(str, Enum):
    NO_ACTION = "no_action"
    LOCAL_JSON_HEAL = "local_json_heal"
    RESET_TEMPERATURE = "reset_temperature"
    REPEAT_PROMPT_WITH_ERROR = "repeat_prompt_with_error"
    LENGTH_CONSTRAIN_PROMPT = "length_constrain_prompt"
    FALLBACK_MODEL = "fallback_model"


@dataclass
class HealPlan:
    action_type: HealActionType
    suggested_params: Dict[str, Any] = field(default_factory=dict)
    retry_prompt_modifier: Optional[str] = None
    local_repaired_content: Optional[str] = None
    reason: str = ""
    alarms_handled: List[str] = field(default_factory=list)


@dataclass
class HealExecutionAttempt:
    attempt_number: int
    raw_output: str
    is_healthy: bool
    alarms: List[Dict[str, Any]] = field(default_factory=list)
    action_taken: str = ""
    params_used: Dict[str, Any] = field(default_factory=dict)
    latency_s: float = 0.0


@dataclass
class HealExecutionResult:
    success: bool
    final_output: str
    parsed_json: Optional[Any] = None
    total_attempts: int = 1
    healed: bool = False
    healing_actions: List[str] = field(default_factory=list)
    attempts: List[HealExecutionAttempt] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GeminiSelfHealer:
    """Autonomous Auto-Heal & Fallback Controller.
    Links GeminiDriftMonitor with prompt repair, local JSON heuristics,
    temperature reset, and multi-tier model fallback.
    """

    def __init__(
        self,
        monitor: Optional[GeminiDriftMonitor] = None,
        fallback_model: str = "nvidia_nim/mistralai/codestral-22b-instruct-v0.1",
        default_temperature: float = 0.7,
        safe_temperature: float = 0.1,
        max_retries: int = 2,
        auto_local_repair: bool = True,
        use_online_baseline: bool = False,
        use_ema: bool = False,
        telemetry_exporter: Optional[Any] = None,
    ) -> None:
        self.monitor = monitor or GeminiDriftMonitor()
        self.fallback_model = fallback_model
        self.default_temperature = default_temperature
        self.safe_temperature = safe_temperature
        self.max_retries = max_retries
        self.auto_local_repair = auto_local_repair
        self.use_online_baseline = use_online_baseline
        self.use_ema = use_ema
        self.telemetry_exporter = telemetry_exporter

    def repair_json_string(self, raw_text: str) -> Tuple[bool, Optional[Any], Optional[str]]:
        """Fast zero-cost local heuristic JSON repair.
        Eliminates unnecessary round-trips for common LLM formatting artifacts:
        - Markdown codeblock wrapper (```json ... ```)
        - Trailing commas before } or ]
        - Python boolean/None constants (True, False, None)
        - Outer whitespace and commentary
        """
        if not raw_text or not raw_text.strip():
            return False, None, None

        cleaned = raw_text.strip()

        # 1. Direct parse test
        try:
            parsed = json.loads(cleaned)
            return True, parsed, cleaned
        except Exception:
            pass

        # 2. Extract from markdown code fences
        codeblock_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
        candidate = codeblock_match.group(1).strip() if codeblock_match else cleaned

        # 3. Try to locate outermost JSON bracket { ... } or [ ... ]
        first_brace = candidate.find("{")
        first_bracket = candidate.find("[")
        start_idx = -1
        end_idx = -1

        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            last_brace = candidate.rfind("}")
            if last_brace != -1 and last_brace > first_brace:
                start_idx = first_brace
                end_idx = last_brace + 1
        elif first_bracket != -1:
            last_bracket = candidate.rfind("]")
            if last_bracket != -1 and last_bracket > first_bracket:
                start_idx = first_bracket
                end_idx = last_bracket + 1

        if start_idx != -1 and end_idx != -1:
            candidate = candidate[start_idx:end_idx].strip()

        # 4. Standard heuristic sanitizations
        # Replace python literals
        candidate = re.sub(r"\bTrue\b", "true", candidate)
        candidate = re.sub(r"\bFalse\b", "false", candidate)
        candidate = re.sub(r"\bNone\b", "null", candidate)

        # Remove trailing commas before } or ]
        candidate = re.sub(r",\s*([\}\]])", r"\1", candidate)

        # Try parsing sanitized candidate
        try:
            parsed = json.loads(candidate)
            return True, parsed, candidate
        except Exception:
            pass

        # 5. Fix unquoted alphanumeric keys: { name: "val" } -> { "name": "val" }
        fixed_keys = re.sub(r'([{\[,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', candidate)
        try:
            parsed = json.loads(fixed_keys)
            return True, parsed, fixed_keys
        except Exception:
            pass

        return False, None, None

    def diagnose(
        self,
        report: DriftReport,
        current_params: Dict[str, Any],
        attempt: int,
        raw_text: str = "",
        expect_json: bool = False,
    ) -> HealPlan:
        """Diagnoses drift alarms and generates an adaptive healing plan."""
        alarm_types = [a.metric for a in report.alarms]
        alarm_messages = [f"{a.metric.value}: {a.message}" for a in report.alarms]

        # Scenario 1: JSON corruption or expected JSON that failed
        if DriftMetricKind.JSON_CORRUPTION in alarm_types or expect_json:
            if self.auto_local_repair and raw_text:
                repaired, parsed, cleaned_text = self.repair_json_string(raw_text)
                if repaired and cleaned_text:
                    return HealPlan(
                        action_type=HealActionType.LOCAL_JSON_HEAL,
                        local_repaired_content=cleaned_text,
                        reason="Successfully repaired broken JSON syntax locally using zero-cost heuristics.",
                        alarms_handled=[DriftMetricKind.JSON_CORRUPTION.value],
                    )

            # Local repair could not fix it; must retry with prompt modifier
            if attempt >= self.max_retries:
                return HealPlan(
                    action_type=HealActionType.FALLBACK_MODEL,
                    suggested_params={**current_params, "model": self.fallback_model, "temperature": self.safe_temperature},
                    retry_prompt_modifier="\n\nCRITICAL: Your previous response contained invalid JSON syntax. Return ONLY valid, parseable JSON strictly complying with RFC 8259 without markdown fences.",
                    reason=f"Exhausted JSON heal retries ({attempt}); escalating to fallback model {self.fallback_model}.",
                    alarms_handled=alarm_messages,
                )

            return HealPlan(
                action_type=HealActionType.REPEAT_PROMPT_WITH_ERROR,
                suggested_params={**current_params, "temperature": max(0.0, current_params.get("temperature", self.default_temperature) - 0.2)},
                retry_prompt_modifier="\n\nCORRECTION: The previous response was NOT valid JSON. Output strictly valid JSON without preamble, commentary, or markdown backticks.",
                reason="JSON syntax corrupted. Triggering repeat prompt with strict syntax constraint.",
                alarms_handled=[DriftMetricKind.JSON_CORRUPTION.value],
            )

        # Scenario 2: Entropy collapse (repetitive loop / degenerate generation)
        if DriftMetricKind.ENTROPY_COLLAPSE in alarm_types:
            new_temp = self.safe_temperature
            suggested = {**current_params, "temperature": new_temp}
            return HealPlan(
                action_type=HealActionType.RESET_TEMPERATURE,
                suggested_params=suggested,
                retry_prompt_modifier="\n\nNOTICE: Repetitive loops detected. Be concise, direct, and avoid repeating phrases or tokens.",
                reason=f"Entropy collapse detected (repetitive loop). Resetting temperature to {new_temp}.",
                alarms_handled=[DriftMetricKind.ENTROPY_COLLAPSE.value],
            )

        # Scenario 3: Length shift (extreme truncation or runaway generation)
        if DriftMetricKind.LENGTH_SHIFT in alarm_types:
            critical_alarms = [a for a in report.alarms if a.metric == DriftMetricKind.LENGTH_SHIFT and a.severity == AlarmSeverity.CRITICAL]
            if critical_alarms:
                return HealPlan(
                    action_type=HealActionType.LENGTH_CONSTRAIN_PROMPT,
                    suggested_params={**current_params, "temperature": self.safe_temperature},
                    retry_prompt_modifier="\n\nCONSTRAINT: Limit response strictly to essential findings. Maximum 300 words.",
                    reason="Critical length shift detected. Imposing length constraints and stabilizing temperature.",
                    alarms_handled=[DriftMetricKind.LENGTH_SHIFT.value],
                )

        # Scenario 4: Escalation to fallback model if max retries exceeded and still unhealthy
        if attempt >= self.max_retries and not report.is_healthy:
            return HealPlan(
                action_type=HealActionType.FALLBACK_MODEL,
                suggested_params={**current_params, "model": self.fallback_model, "temperature": self.safe_temperature},
                reason=f"Max retries reached with ongoing drift alarms. Switching to fallback model {self.fallback_model}.",
                alarms_handled=alarm_messages,
            )

        return HealPlan(
            action_type=HealActionType.NO_ACTION,
            suggested_params=current_params,
            reason="Output is within statistical tolerances.",
        )

    def _finish_result(self, result: HealExecutionResult) -> HealExecutionResult:
        if self.telemetry_exporter is not None:
            try:
                self.telemetry_exporter.record_healing_result(result)
            except Exception as exc:
                logger.debug("Failed recording healing telemetry: %s", exc)
        return result

    def execute_with_healing(
        self,
        call_fn: Callable[[Dict[str, Any]], str],
        initial_params: Dict[str, Any],
        expect_json: bool = False,
        max_retries: Optional[int] = None,
    ) -> HealExecutionResult:
        """Executes LLM call with autonomous drift monitoring and self-healing loop."""
        retries_limit = max_retries if max_retries is not None else self.max_retries
        current_params = dict(initial_params)
        attempts_history: List[HealExecutionAttempt] = []
        healing_actions_taken: List[str] = []

        last_output = ""
        attempt = 1

        while attempt <= retries_limit + 1:
            t_start = time.time()
            try:
                raw_output = call_fn(current_params)
            except Exception as exc:
                logger.warning("LLM call threw exception during attempt %d: %s", attempt, exc)
                raw_output = ""

            latency_s = time.time() - t_start
            last_output = raw_output

            # Statistical and structural evaluation
            metrics = self.monitor.calculate_metrics(raw_output)
            self.monitor.record_response(raw_output)
            report = self.monitor.evaluate_drift(
                use_online_baseline=self.use_online_baseline,
                use_ema=self.use_ema,
            )
            if self.telemetry_exporter is not None and report is not None:
                try:
                    self.telemetry_exporter.record_drift_report(report)
                except Exception as exc:
                    logger.debug("Failed recording drift report telemetry: %s", exc)

            # Determine if output satisfies JSON expectations
            if expect_json:
                try:
                    json.loads(raw_output.strip())
                    is_valid_json = True
                except Exception:
                    is_valid_json = False
            else:
                is_valid_json = metrics.is_valid_json

            needs_json_heal = expect_json and not is_valid_json

            # Synthesize entropy collapse alarm if severe loop repetition even without baseline
            if metrics.shannon_entropy < 1.5 and len(raw_output) > 30 and not any(a.metric == DriftMetricKind.ENTROPY_COLLAPSE for a in report.alarms):
                report.alarms.append(
                    DriftAlarm(
                        metric=DriftMetricKind.ENTROPY_COLLAPSE,
                        severity=AlarmSeverity.CRITICAL,
                        baseline_value=3.5,
                        current_value=metrics.shannon_entropy,
                        delta_or_z=0.6,
                        message=f"Absolute entropy collapse: entropy={metrics.shannon_entropy:.2f} bits under 1.5 threshold",
                    )
                )
                report.is_healthy = False

            if needs_json_heal and not any(a.metric == DriftMetricKind.JSON_CORRUPTION for a in report.alarms):
                report.alarms.append(
                    DriftAlarm(
                        metric=DriftMetricKind.JSON_CORRUPTION,
                        severity=AlarmSeverity.CRITICAL,
                        baseline_value=1.0,
                        current_value=0.0,
                        delta_or_z=1.0,
                        message="Output failed JSON parsing expectation",
                    )
                )
                report.is_healthy = False

            is_healthy = report.is_healthy and not needs_json_heal

            attempt_record = HealExecutionAttempt(
                attempt_number=attempt,
                raw_output=raw_output,
                is_healthy=is_healthy,
                alarms=[
                    {
                        "metric": a.metric.value,
                        "severity": a.severity.value,
                        "message": a.message,
                    }
                    for a in report.alarms
                ],
                params_used=dict(current_params),
                latency_s=latency_s,
            )

            # If healthy, we succeed immediately!
            if is_healthy:
                attempt_record.action_taken = "accepted_healthy"
                attempts_history.append(attempt_record)
                parsed = None
                if expect_json and is_valid_json:
                    try:
                        parsed = json.loads(raw_output)
                    except Exception:
                        pass

                return self._finish_result(HealExecutionResult(
                    success=True,
                    final_output=raw_output,
                    parsed_json=parsed,
                    total_attempts=attempt,
                    healed=len(healing_actions_taken) > 0,
                    healing_actions=healing_actions_taken,
                    attempts=attempts_history,
                ))

            # Output is unhealthy or corrupted -> diagnose and self-heal
            plan = self.diagnose(
                report=report,
                current_params=current_params,
                attempt=attempt,
                raw_text=raw_output,
                expect_json=expect_json,
            )

            attempt_record.action_taken = plan.action_type.value
            attempts_history.append(attempt_record)
            healing_actions_taken.append(f"Attempt {attempt}: {plan.action_type.value} ({plan.reason})")

            # Check for instant local zero-cost repair
            if plan.action_type == HealActionType.LOCAL_JSON_HEAL and plan.local_repaired_content:
                repaired_text = plan.local_repaired_content
                try:
                    parsed = json.loads(repaired_text)
                    return self._finish_result(HealExecutionResult(
                        success=True,
                        final_output=repaired_text,
                        parsed_json=parsed,
                        total_attempts=attempt,
                        healed=True,
                        healing_actions=healing_actions_taken,
                        attempts=attempts_history,
                    ))
                except Exception:
                    pass

            # If no more retries allowed, break out
            if attempt > retries_limit:
                break

            # Pop the rejected unhealthy attempt from the monitor's current_window
            # so it does not skew the window statistics for the retry attempt
            if self.monitor.current_window:
                self.monitor.current_window.pop()

            # Apply adapted parameters and prompt modifiers for next attempt
            current_params = dict(plan.suggested_params)
            if plan.retry_prompt_modifier:
                prompt_key = "prompt" if "prompt" in current_params else "content" if "content" in current_params else "message"
                existing_prompt = current_params.get(prompt_key, "")
                current_params[prompt_key] = f"{existing_prompt}{plan.retry_prompt_modifier}"

            attempt += 1

        # Fallback exhausted: return best-effort result
        parsed = None
        if expect_json:
            _, parsed, _ = self.repair_json_string(last_output)

        return self._finish_result(HealExecutionResult(
            success=False,
            final_output=last_output,
            parsed_json=parsed,
            total_attempts=len(attempts_history),
            healed=False,
            healing_actions=healing_actions_taken,
            attempts=attempts_history,
            error_message="Drift self-healing loop exhausted retries without reaching statistical stability.",
        ))
