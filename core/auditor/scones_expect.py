#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/auditor/scones_expect.py"
# purpose: "Declarative expectation framework for SCONES memory episodes and agent execution traces, assimilated from Soup expect."
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
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, Union

logger = logging.getLogger("dnk_scones_expect")


@dataclass
class FieldViolation:
    field: str
    rule: str
    expected: Any
    actual: Any
    message: str


@dataclass
class ExpectationResult:
    record_id: Optional[str]
    is_valid: bool
    violations: List[FieldViolation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "is_valid": self.is_valid,
            "violations": [
                {
                    "field": v.field,
                    "rule": v.rule,
                    "expected": str(v.expected),
                    "actual": str(v.actual),
                    "message": v.message,
                }
                for v in self.violations
            ],
        }


@dataclass
class DatasetExpectationReport:
    total_records: int
    valid_records: int
    failed_records: int
    pass_rate: float
    is_approved: bool
    violations_by_field: Dict[str, int]
    violations_by_rule: Dict[str, int]
    results: List[ExpectationResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_records": self.total_records,
            "valid_records": self.valid_records,
            "failed_records": self.failed_records,
            "pass_rate": round(self.pass_rate, 4),
            "is_approved": self.is_approved,
            "violations_by_field": self.violations_by_field,
            "violations_by_rule": self.violations_by_rule,
        }


class SconesExpectationValidator:
    """Declarative validator for SCONES memory episodes and LLM trace streams.
    Assimilated from MakazhanAlpamys/Soup expect command architecture.
    Provides strict schema, non-null, regex, range, and length validation.
    """

    def __init__(
        self,
        required_fields: Optional[Sequence[str]] = None,
        non_empty_fields: Optional[Sequence[str]] = None,
        type_rules: Optional[Dict[str, Any]] = None,
        regex_rules: Optional[Dict[str, str]] = None,
        range_rules: Optional[Dict[str, Dict[str, Union[int, float]]]] = None,
        length_rules: Optional[Dict[str, Dict[str, int]]] = None,
        allowed_values: Optional[Dict[str, Sequence[Any]]] = None,
        custom_predicates: Optional[Dict[str, Callable[[Any], bool]]] = None,
        no_hardcoded_user_paths: bool = False,
        min_pass_rate: float = 1.0,
    ) -> None:
        self.required_fields: List[str] = list(required_fields or [])
        self.non_empty_fields: List[str] = list(non_empty_fields or [])
        self.type_rules: Dict[str, Any] = {
            k: tuple(v) if isinstance(v, (list, tuple)) else v
            for k, v in (type_rules or {}).items()
        }
        self.regex_rules: Dict[str, re.Pattern] = {
            k: re.compile(v) for k, v in (regex_rules or {}).items()
        }
        self.range_rules: Dict[str, Dict[str, Union[int, float]]] = range_rules or {}
        self.length_rules: Dict[str, Dict[str, int]] = length_rules or {}
        self.allowed_values: Dict[str, Set[Any]] = {
            k: set(v) for k, v in (allowed_values or {}).items()
        }
        self.custom_predicates: Dict[str, Callable[[Any], bool]] = custom_predicates or {}
        self.no_hardcoded_user_paths = no_hardcoded_user_paths
        self.min_pass_rate = min_pass_rate

    @classmethod
    def create_scones_memory_validator(
        cls, min_pass_rate: float = 1.0, no_hardcoded_user_paths: bool = True
    ) -> "SconesExpectationValidator":
        """Pre-configured canonical validator for SCONES memory records."""
        return cls(
            required_fields=["topic", "content", "importance"],
            non_empty_fields=["topic", "content"],
            type_rules={
                "topic": str,
                "content": str,
                "importance": (int, float),
            },
            range_rules={
                "importance": {"min": 0.0, "max": 1.0},
            },
            length_rules={
                "topic": {"min": 3, "max": 200},
                "content": {"min": 5},
            },
            no_hardcoded_user_paths=no_hardcoded_user_paths,
            min_pass_rate=min_pass_rate,
        )

    def validate_record(self, record: Dict[str, Any], record_id_field: str = "id") -> ExpectationResult:
        """Validates a single record against configured expectation rules."""
        violations: List[FieldViolation] = []
        rec_id = str(record.get(record_id_field, "")) or None

        # 1. Required fields
        for field_name in self.required_fields:
            if field_name not in record:
                violations.append(
                    FieldViolation(
                        field=field_name,
                        rule="required_field",
                        expected=True,
                        actual=False,
                        message=f"Missing required field: '{field_name}'",
                    )
                )

        # 2. Non-empty fields
        for field_name in self.non_empty_fields:
            if field_name in record:
                val = record[field_name]
                if val is None or (isinstance(val, (str, list, dict, set, tuple)) and len(val) == 0):
                    violations.append(
                        FieldViolation(
                            field=field_name,
                            rule="non_empty",
                            expected="non-empty value",
                            actual=val,
                            message=f"Field '{field_name}' must not be empty or null",
                        )
                    )

        # 3. Type rules
        for field_name, exp_type in self.type_rules.items():
            if field_name in record and record[field_name] is not None:
                val = record[field_name]
                if not isinstance(val, exp_type):
                    expected_names = (
                        [t.__name__ for t in exp_type]
                        if isinstance(exp_type, (list, tuple))
                        else getattr(exp_type, "__name__", str(exp_type))
                    )
                    violations.append(
                        FieldViolation(
                            field=field_name,
                            rule="type_check",
                            expected=expected_names,
                            actual=type(val).__name__,
                            message=f"Field '{field_name}' expected type {expected_names}, got {type(val).__name__}",
                        )
                    )

        # 4. Regex rules
        for field_name, pattern in self.regex_rules.items():
            if field_name in record and isinstance(record[field_name], str):
                val = record[field_name]
                if not pattern.search(val):
                    violations.append(
                        FieldViolation(
                            field=field_name,
                            rule="regex_match",
                            expected=pattern.pattern,
                            actual=val,
                            message=f"Field '{field_name}' failed regex pattern: '{pattern.pattern}'",
                        )
                    )

        # 5. Range rules (numeric)
        for field_name, bounds in self.range_rules.items():
            if field_name in record and isinstance(record[field_name], (int, float)):
                val = record[field_name]
                min_v = bounds.get("min")
                max_v = bounds.get("max")
                if min_v is not None and val < min_v:
                    violations.append(
                        FieldViolation(
                            field=field_name,
                            rule="range_min",
                            expected=f">= {min_v}",
                            actual=val,
                            message=f"Field '{field_name}' value {val} is below minimum {min_v}",
                        )
                    )
                if max_v is not None and val > max_v:
                    violations.append(
                        FieldViolation(
                            field=field_name,
                            rule="range_max",
                            expected=f"<= {max_v}",
                            actual=val,
                            message=f"Field '{field_name}' value {val} is above maximum {max_v}",
                        )
                    )

        # 6. Length rules
        for field_name, bounds in self.length_rules.items():
            if field_name in record and hasattr(record[field_name], "__len__"):
                length = len(record[field_name])
                min_len = bounds.get("min")
                max_len = bounds.get("max")
                if min_len is not None and length < min_len:
                    violations.append(
                        FieldViolation(
                            field=field_name,
                            rule="length_min",
                            expected=f"len >= {min_len}",
                            actual=length,
                            message=f"Field '{field_name}' length {length} is less than minimum {min_len}",
                        )
                    )
                if max_len is not None and length > max_len:
                    violations.append(
                        FieldViolation(
                            field=field_name,
                            rule="length_max",
                            expected=f"len <= {max_len}",
                            actual=length,
                            message=f"Field '{field_name}' length {length} exceeds maximum {max_len}",
                        )
                    )

        # 7. Allowed values
        for field_name, allowed_set in self.allowed_values.items():
            if field_name in record:
                val = record[field_name]
                if val not in allowed_set:
                    violations.append(
                        FieldViolation(
                            field=field_name,
                            rule="allowed_values",
                            expected=list(allowed_set),
                            actual=val,
                            message=f"Field '{field_name}' value '{val}' not in allowed set: {allowed_set}",
                        )
                    )

        # 8. Custom predicates
        for field_name, predicate in self.custom_predicates.items():
            if field_name in record:
                val = record[field_name]
                try:
                    if not predicate(val):
                        violations.append(
                            FieldViolation(
                                field=field_name,
                                rule="custom_predicate",
                                expected=True,
                                actual=False,
                                message=f"Field '{field_name}' failed custom predicate validation",
                            )
                        )
                except Exception as ex:
                    violations.append(
                        FieldViolation(
                            field=field_name,
                            rule="custom_predicate",
                            expected="predicate returns true",
                            actual=str(ex),
                            message=f"Predicate raised exception on field '{field_name}': {ex}",
                        )
                    )

        # 9. Path hygiene check (Universal Relative Path Invariant)
        if self.no_hardcoded_user_paths:
            path_pat = re.compile(r'(?:/(?:Users|home|root)/|[A-Za-z]:[/\\])')
            for field_name in ("topic", "content"):
                if field_name in record and isinstance(record[field_name], str):
                    if path_pat.search(record[field_name]):
                        violations.append(
                            FieldViolation(
                                field=field_name,
                                rule="no_hardcoded_user_paths",
                                expected="relative path only",
                                actual=record[field_name][:60],
                                message=f"Field '{field_name}' contains forbidden absolute user path: '{record[field_name][:60]}...'",
                            )
                        )

        is_valid = len(violations) == 0
        return ExpectationResult(record_id=rec_id, is_valid=is_valid, violations=violations)

    def validate_dataset(
        self, records: Sequence[Dict[str, Any]], record_id_field: str = "id"
    ) -> DatasetExpectationReport:
        """Validates an entire dataset or trace stream, computing aggregation metrics."""
        if not records:
            return DatasetExpectationReport(
                total_records=0,
                valid_records=0,
                failed_records=0,
                pass_rate=1.0,
                is_approved=True,
                violations_by_field={},
                violations_by_rule={},
                results=[],
            )

        results: List[ExpectationResult] = []
        violations_by_field: Dict[str, int] = {}
        violations_by_rule: Dict[str, int] = {}
        valid_count = 0

        for r in records:
            res = self.validate_record(r, record_id_field=record_id_field)
            results.append(res)
            if res.is_valid:
                valid_count += 1
            else:
                for v in res.violations:
                    violations_by_field[v.field] = violations_by_field.get(v.field, 0) + 1
                    violations_by_rule[v.rule] = violations_by_rule.get(v.rule, 0) + 1

        total = len(records)
        failed = total - valid_count
        pass_rate = valid_count / total if total > 0 else 1.0
        is_approved = pass_rate >= self.min_pass_rate

        return DatasetExpectationReport(
            total_records=total,
            valid_records=valid_count,
            failed_records=failed,
            pass_rate=pass_rate,
            is_approved=is_approved,
            violations_by_field=violations_by_field,
            violations_by_rule=violations_by_rule,
            results=results,
        )
