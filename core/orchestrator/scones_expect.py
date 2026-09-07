#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/scones_expect.py"
# purpose: "Declarative Expectations & Memory Hygiene Verifier (soup expect) for SCONES episodes & agent traces."
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
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import yaml

logger = logging.getLogger("dnk_scones_expect")


class RuleSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


@dataclass
class RuleEvaluation:
    rule_id: str
    rule_type: str
    passed: bool
    severity: RuleSeverity
    details: str


@dataclass
class ExpectationSuiteResult:
    passed: bool
    total_rules: int
    passed_rules: int
    failed_rules: int
    evaluations: List[RuleEvaluation]
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SconesExpect:
    """Declarative Assertion & Memory Hygiene Engine assimilated from 'soup expect'.
    Validates agent outputs, SCONES long-term memories, and tool traces against
    deterministic quality and hygiene invariants.
    """

    ABSOLUTE_PATH_PATTERNS = [
        re.compile(r"/(?:Users|home|root|private)/[^\s\'\"\`]+"),
        re.compile(r"^[A-Za-z]:\\[^\s\'\"\`]+"),  # Windows paths
    ]

    MRH_HEADER_PATTERN = re.compile(
        r"(?:#|<!--)\s*--- DNK-MRH-HEADER ---[\s\S]+?mrh_id:[\s\S]+?--- END DNK-MRH-HEADER ---(?:\s*-->)?",
        re.MULTILINE,
    )

    def __init__(self, suite_name: str = "default_hygiene"):
        self.suite_name = suite_name
        self.rules: List[Dict[str, Any]] = []

    def add_rule(
        self,
        rule_type: str,
        rule_id: Optional[str] = None,
        severity: RuleSeverity = RuleSeverity.CRITICAL,
        **params: Any,
    ) -> "SconesExpect":
        """Adds a rule to the expectation suite."""
        self.rules.append({
            "rule_id": rule_id or f"{rule_type}_{len(self.rules)+1}",
            "rule_type": rule_type,
            "severity": severity,
            "params": params,
        })
        return self

    def load_from_yaml(self, yaml_content_or_path: str) -> "SconesExpect":
        """Loads expectation rules from a YAML string or file path."""
        p = Path(yaml_content_or_path)
        if p.exists() and p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        else:
            data = yaml.safe_load(yaml_content_or_path)

        if not isinstance(data, dict):
            raise ValueError("YAML expectations must define a dictionary at root")

        self.suite_name = data.get("suite_name", self.suite_name)
        for item in data.get("rules", []):
            sev_str = item.get("severity", "CRITICAL").upper()
            sev = RuleSeverity.CRITICAL if sev_str == "CRITICAL" else RuleSeverity.WARNING
            self.add_rule(
                rule_type=item["type"],
                rule_id=item.get("id"),
                severity=sev,
                **item.get("params", {}),
            )
        return self

    def evaluate_artifact(self, content: str, filename: Optional[str] = None) -> ExpectationSuiteResult:
        """Evaluates source code or markdown artifact content against text-level expectations."""
        evals: List[RuleEvaluation] = []

        for rule in self.rules:
            r_type = rule["rule_type"]
            r_id = rule["rule_id"]
            sev = rule["severity"]
            params = rule["params"]

            if r_type == "no_absolute_paths":
                violations = []
                for pat in self.ABSOLUTE_PATH_PATTERNS:
                    found = pat.findall(content)
                    if found:
                        violations.extend(found)
                passed = len(violations) == 0
                details = "No absolute paths detected." if passed else f"Found absolute paths: {violations[:5]}"
                evals.append(RuleEvaluation(r_id, r_type, passed, sev, details))

            elif r_type == "require_mrh_header":
                passed = bool(self.MRH_HEADER_PATTERN.search(content))
                details = "MRH header present." if passed else "Missing mandatory DNK-MRH header."
                evals.append(RuleEvaluation(r_id, r_type, passed, sev, details))

            elif r_type == "forbid_terms":
                terms = params.get("terms", [])
                found_terms = [t for t in terms if t in content]
                passed = len(found_terms) == 0
                details = "No forbidden terms found." if passed else f"Forbidden terms detected: {found_terms}"
                evals.append(RuleEvaluation(r_id, r_type, passed, sev, details))

            elif r_type == "regex_match":
                pattern = params.get("pattern", "")
                passed = bool(re.search(pattern, content))
                details = f"Pattern '{pattern}' matched." if passed else f"Pattern '{pattern}' did not match."
                evals.append(RuleEvaluation(r_id, r_type, passed, sev, details))

        return self._build_result(evals)

    def evaluate_memory_episode(self, episode: Dict[str, Any]) -> ExpectationSuiteResult:
        """Evaluates a SCONES long-term memory episode or lesson dictionary."""
        evals: List[RuleEvaluation] = []

        for rule in self.rules:
            r_type = rule["rule_type"]
            r_id = rule["rule_id"]
            sev = rule["severity"]
            params = rule["params"]

            if r_type == "require_keys":
                keys = params.get("keys", [])
                missing = [k for k in keys if k not in episode]
                passed = len(missing) == 0
                details = "All required keys present." if passed else f"Missing required keys: {missing}"
                evals.append(RuleEvaluation(r_id, r_type, passed, sev, details))

            elif r_type == "no_absolute_paths":
                text_payload = json.dumps(episode)
                violations = []
                for pat in self.ABSOLUTE_PATH_PATTERNS:
                    found = pat.findall(text_payload)
                    if found:
                        violations.extend(found)
                passed = len(violations) == 0
                details = "No absolute paths in episode." if passed else f"Absolute paths detected: {violations[:5]}"
                evals.append(RuleEvaluation(r_id, r_type, passed, sev, details))

            elif r_type == "field_min_length":
                field_name = params.get("field", "content")
                min_len = params.get("min_length", 10)
                val = str(episode.get(field_name, ""))
                passed = len(val) >= min_len
                details = f"Field '{field_name}' length is {len(val)} (min {min_len})."
                evals.append(RuleEvaluation(r_id, r_type, passed, sev, details))

        return self._build_result(evals)

    def evaluate_trace(self, trace_events: List[Dict[str, Any]]) -> ExpectationSuiteResult:
        """Evaluates agent tool call sequence traces (e.g. SCONES query before code edit)."""
        evals: List[RuleEvaluation] = []

        tool_calls = [
            e.get("tool") or e.get("name")
            for e in trace_events
            if isinstance(e, dict) and (e.get("type") == "tool" or "tool" in e or "name" in e)
        ]

        for rule in self.rules:
            r_type = rule["rule_type"]
            r_id = rule["rule_id"]
            sev = rule["severity"]
            params = rule["params"]

            if r_type == "tool_called_before":
                first_tool = params.get("first")
                second_tool = params.get("second")

                idx_first = tool_calls.index(first_tool) if first_tool in tool_calls else -1
                idx_second = tool_calls.index(second_tool) if second_tool in tool_calls else -1

                if idx_second != -1 and idx_first == -1:
                    passed = False
                    details = f"Tool '{second_tool}' was called, but prerequisite '{first_tool}' was never called."
                elif idx_second != -1 and idx_first != -1 and idx_first > idx_second:
                    passed = False
                    details = f"Tool '{first_tool}' (pos {idx_first}) was called AFTER '{second_tool}' (pos {idx_second})."
                else:
                    passed = True
                    details = f"Tool sequence ordering invariant satisfied for '{first_tool}' -> '{second_tool}'."
                evals.append(RuleEvaluation(r_id, r_type, passed, sev, details))

            elif r_type == "tool_must_be_called":
                required = params.get("tool")
                passed = required in tool_calls
                details = f"Tool '{required}' was invoked." if passed else f"Tool '{required}' was NOT invoked."
                evals.append(RuleEvaluation(r_id, r_type, passed, sev, details))

        return self._build_result(evals)

    def _build_result(self, evals: List[RuleEvaluation]) -> ExpectationSuiteResult:
        critical_failed = [e for e in evals if not e.passed and e.severity == RuleSeverity.CRITICAL]
        passed = len(critical_failed) == 0
        passed_count = sum(1 for e in evals if e.passed)
        failed_count = sum(1 for e in evals if not e.passed)

        summary = (
            f"Expectation Suite '{self.suite_name}': {passed_count}/{len(evals)} rules passed. "
            f"{'SUCCESS' if passed else f'FAILURE ({len(critical_failed)} critical violations)'}."
        )

        return ExpectationSuiteResult(
            passed=passed,
            total_rules=len(evals),
            passed_rules=passed_count,
            failed_rules=failed_count,
            evaluations=evals,
            summary=summary,
        )
