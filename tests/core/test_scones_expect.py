#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_scones_expect.py"
# purpose: "Comprehensive unit tests for SconesExpectationValidator (assimilated from Soup expect)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from core.auditor.scones_expect import (
    DatasetExpectationReport,
    ExpectationResult,
    FieldViolation,
    SconesExpectationValidator,
)


def test_scones_memory_validator_valid():
    validator = SconesExpectationValidator.create_scones_memory_validator()
    valid_record = {
        "id": "rec-001",
        "topic": "FastAPI async testclient",
        "content": "Use threading.local() for isolated test clients in stress tests.",
        "importance": 0.9,
    }
    result = validator.validate_record(valid_record)
    assert result.is_valid is True
    assert len(result.violations) == 0
    assert result.record_id == "rec-001"


def test_scones_memory_validator_missing_required():
    validator = SconesExpectationValidator.create_scones_memory_validator()
    bad_record = {
        "id": "rec-002",
        "topic": "Incomplete note",
        # missing "content" and "importance"
    }
    result = validator.validate_record(bad_record)
    assert result.is_valid is False
    violation_fields = [v.field for v in result.violations]
    assert "content" in violation_fields
    assert "importance" in violation_fields


def test_scones_memory_validator_empty_field():
    validator = SconesExpectationValidator.create_scones_memory_validator()
    bad_record = {
        "id": "rec-003",
        "topic": "Non-empty test",
        "content": "",  # empty string
        "importance": 0.5,
    }
    result = validator.validate_record(bad_record)
    assert result.is_valid is False
    assert any(v.rule == "non_empty" and v.field == "content" for v in result.violations)


def test_scones_memory_validator_range_violation():
    validator = SconesExpectationValidator.create_scones_memory_validator()
    bad_record = {
        "id": "rec-004",
        "topic": "Importance over max",
        "content": "Valid content string here.",
        "importance": 1.5,  # > 1.0
    }
    result = validator.validate_record(bad_record)
    assert result.is_valid is False
    assert any(v.rule == "range_max" and v.field == "importance" for v in result.violations)


def test_custom_validator_regex_and_allowed_values():
    validator = SconesExpectationValidator(
        regex_rules={"code": r"^[A-Z]{3}-\d{4}$"},
        allowed_values={"status": ["Active", "Archived"]},
        length_rules={"tags": {"min": 1, "max": 3}},
    )
    good = {
        "id": "item-1",
        "code": "DNK-0042",
        "status": "Active",
        "tags": ["core", "auditor"],
    }
    bad = {
        "id": "item-2",
        "code": "invalid_code",
        "status": "Unknown",
        "tags": [],  # len 0 < min 1
    }
    assert validator.validate_record(good).is_valid is True

    bad_res = validator.validate_record(bad)
    assert bad_res.is_valid is False
    rules_violated = {v.rule for v in bad_res.violations}
    assert "regex_match" in rules_violated
    assert "allowed_values" in rules_violated
    assert "length_min" in rules_violated


def test_custom_predicate_validation():
    validator = SconesExpectationValidator(
        custom_predicates={
            "score": lambda x: isinstance(x, (int, float)) and x % 2 == 0,
        }
    )
    assert validator.validate_record({"score": 4}).is_valid is True
    res_odd = validator.validate_record({"score": 3})
    assert res_odd.is_valid is False
    assert res_odd.violations[0].rule == "custom_predicate"


def test_dataset_validation_and_reporting():
    validator = SconesExpectationValidator.create_scones_memory_validator(min_pass_rate=0.7)
    records = [
        {"id": "1", "topic": "Topic A", "content": "Valid content 1", "importance": 0.8},
        {"id": "2", "topic": "Topic B", "content": "Valid content 2", "importance": 0.5},
        {"id": "3", "topic": "Bad", "content": "", "importance": 2.0},  # fails
    ]
    report = validator.validate_dataset(records)
    assert report.total_records == 3
    assert report.valid_records == 2
    assert report.failed_records == 1
    assert pytest.approx(report.pass_rate, 0.01) == 0.6667
    assert report.is_approved is False  # 0.6667 < min_pass_rate 0.70

    report_dict = report.to_dict()
    assert report_dict["total_records"] == 3
    assert "content" in report_dict["violations_by_field"]


def test_empty_dataset_validation():
    validator = SconesExpectationValidator()
    report = validator.validate_dataset([])
    assert report.total_records == 0
    assert report.pass_rate == 1.0
    assert report.is_approved is True
