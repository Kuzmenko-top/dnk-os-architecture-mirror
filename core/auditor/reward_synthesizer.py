#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/auditor/reward_synthesizer.py"
# purpose: "Deterministic Reward & Output Verifier Synthesizer with Perturbation Calibration, assimilated from Soup."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger("dnk_reward_synthesizer")


class VerifierKind(str, Enum):
    JSON_SCHEMA = "json_schema"
    TOOL_CALL = "tool_call"
    REGEX = "regex"
    NUMERIC = "numeric"


class UncalibratedVerifierError(Exception):
    """Raised when a synthesized verifier fails calibration against perturbed negative samples."""
    pass


@dataclass
class CalibrationReport:
    kind: VerifierKind
    positive_samples_tested: int
    negative_samples_tested: int
    positive_pass_rate: float
    negative_rejection_rate: float
    calibrated: bool
    details: List[str]


class RewardSynthesizer:
    """Synthesizes deterministic Python verification functions from gold specifications.
    Assimilated from MakazhanAlpamys/Soup reward.py architecture.
    Guarantees zero false positives on negative mutations via strict calibration.
    """

    @staticmethod
    def synthesize_json_schema_verifier(
        required_keys: List[str],
        expected_types: Optional[Dict[str, str]] = None,
        fn_name: str = "verify_output_json",
    ) -> str:
        """Emits a self-contained Python function that parses JSON and verifies keys and types."""
        type_checks_code = ""
        if expected_types:
            for k, t in expected_types.items():
                type_checks_code += f"""
    if "{k}" in data and not isinstance(data["{k}"], {t}):
        return False, "Field '{k}' has invalid type: expected {t}, got " + type(data["{k}"]).__name__"""

        code = f"""def {fn_name}(raw_text: str) -> tuple[bool, str]:
    import json
    import re
    # Extract JSON candidate from text (handles markdown fences)
    match = re.search(r"```(?:json)?\\s*([\\s\\S]*?)\\s*```", raw_text)
    candidate = match.group(1) if match else raw_text.strip()
    try:
        data = json.loads(candidate)
    except Exception as e:
        return False, f"JSON parse error: {{str(e)}}"
    if not isinstance(data, dict):
        return False, "Root JSON element must be an object/dict"
    required = {json.dumps(required_keys)}
    missing = [k for k in required if k not in data]
    if missing:
        return False, f"Missing required keys: {{missing}}"
{type_checks_code}
    return True, "Valid"
"""
        return code

    @staticmethod
    def synthesize_tool_call_verifier(
        expected_tool_name: str,
        required_params: List[str],
        fn_name: str = "verify_tool_call",
    ) -> str:
        """Emits a Python verifier for function-calling payloads."""
        code = f"""def {fn_name}(tool_payload: dict) -> tuple[bool, str]:
    if not isinstance(tool_payload, dict):
        return False, "Tool payload must be a dict"
    name = tool_payload.get("name")
    if name != "{expected_tool_name}":
        return False, f"Unexpected tool name '{{name}}', expected '{expected_tool_name}'"
    args = tool_payload.get("arguments", {{}})
    if not isinstance(args, dict):
        return False, "Arguments must be a dict"
    missing = [p for p in {json.dumps(required_params)} if p not in args]
    if missing:
        return False, f"Missing required argument parameters: {{missing}}"
    return True, "Valid tool call"
"""
        return code

    @staticmethod
    def synthesize_regex_verifier(
        pattern: str,
        description: str = "Regex pattern match",
        fn_name: str = "verify_regex_pattern",
    ) -> str:
        """Emits a Python verifier checking text against a regex pattern."""
        code = f"""def {fn_name}(text: str) -> tuple[bool, str]:
    import re
    pat = re.compile(r"{pattern}")
    if not pat.search(text):
        return False, "Pattern check failed: {description}"
    return True, "Valid"
"""
        return code

    @classmethod
    def calibrate_verifier(
        cls,
        verifier_code: str,
        fn_name: str,
        gold_positives: Sequence[Any],
        negative_mutations: Sequence[Any],
        kind: VerifierKind,
    ) -> CalibrationReport:
        """Calibrates the synthesized code against positives and perturbed negatives.
        If any gold positive fails OR any negative mutation passes, calibration fails.
        """
        # Execute generated code in isolated local namespace
        local_scope: Dict[str, Any] = {}
        exec(verifier_code, {}, local_scope)
        verifier_fn = local_scope.get(fn_name)
        if not callable(verifier_fn):
            raise ValueError(f"Function '{fn_name}' was not defined in generated code.")

        pos_passed = 0
        details: List[str] = []

        for i, sample in enumerate(gold_positives):
            valid, msg = verifier_fn(sample)
            if valid:
                pos_passed += 1
            else:
                details.append(f"Gold positive #{i} failed: {msg}")

        neg_rejected = 0
        for j, neg_sample in enumerate(negative_mutations):
            valid, msg = verifier_fn(neg_sample)
            if not valid:
                neg_rejected += 1
            else:
                details.append(f"Perturbed negative #{j} unexpectedly passed verifier!")

        pos_rate = pos_passed / len(gold_positives) if len(gold_positives) > 0 else 1.0
        neg_rate = neg_rejected / len(negative_mutations) if len(negative_mutations) > 0 else 1.0

        is_calibrated = (pos_rate == 1.0) and (neg_rate == 1.0)

        report = CalibrationReport(
            kind=kind,
            positive_samples_tested=len(gold_positives),
            negative_samples_tested=len(negative_mutations),
            positive_pass_rate=pos_rate,
            negative_rejection_rate=neg_rate,
            calibrated=is_calibrated,
            details=details,
        )

        if not is_calibrated:
            raise UncalibratedVerifierError(
                f"Verifier failed calibration for {kind.value}! Pos rate: {pos_rate:.2f}, Neg rejection rate: {neg_rate:.2f}. Details: {details[:3]}"
            )

        return report
