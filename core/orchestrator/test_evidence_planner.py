#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/test_evidence_planner.py"
# purpose: "Unit and security tests for Evidence Planner & Epistemic Taxonomy."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.1.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import pytest
from core.orchestrator.evidence_planner import (
    EpistemicStatus,
    classify_statement,
    get_pytest_cmd,
    verify_evidence,
    generate_evidence_plan,
    execute_evidence_plan,
)


def test_get_pytest_cmd():
    cmd = get_pytest_cmd()
    assert isinstance(cmd, list)
    assert len(cmd) >= 1
    assert any("pytest" in arg for arg in cmd)


def test_classify_statement_epistemic():
    assert classify_statement("можливо, є витік пам'яті") == EpistemicStatus.HYPOTHESIS
    assert classify_statement("perhaps there is a bug") == EpistemicStatus.HYPOTHESIS
    assert classify_statement("підтверджено: наявний файл config.yaml") == EpistemicStatus.OBSERVED
    assert classify_statement("measured line count is 150") == EpistemicStatus.OBSERVED
    assert classify_statement("імплементувати новий модуль") == EpistemicStatus.INFERRED


def test_verify_evidence():
    probe_code0 = {"expected": "exit_code_0"}
    assert verify_evidence(probe_code0, "", 0) is True
    assert verify_evidence(probe_code0, "error", 1) is False

    probe_non_empty = {"expected": "NON_EMPTY"}
    assert verify_evidence(probe_non_empty, "some output", 0) is True
    assert verify_evidence(probe_non_empty, "   ", 0) is False

    probe_threshold = {"expected": "> 10"}
    assert verify_evidence(probe_threshold, "total 45 items", 0) is True
    assert verify_evidence(probe_threshold, "total 5 items", 0) is False
    assert verify_evidence(probe_threshold, "total 50 items", 1) is False

    probe_contains = {"expected": "contains:SUCCESS"}
    assert verify_evidence(probe_contains, "Build: SUCCESS finished", 0) is True
    assert verify_evidence(probe_contains, "Build: FAILED", 0) is False


def test_generate_evidence_plan_safety():
    plan = generate_evidence_plan("перевір тести та статус git", target_files=["pyproject.toml"])
    assert plan["total_claims"] >= 2
    for claim in plan["claims"]:
        assert "cmd_args" in claim
        assert isinstance(claim["cmd_args"], list)
        assert len(claim["cmd_args"]) > 0


def test_execute_evidence_plan():
    plan = {
        "task_prompt_summary": "safe execution test",
        "claims": [
            {
                "claim": "echo test passes",
                "epistemic_status": "OBSERVED",
                "cmd_args": ["python3", "-c", "print('TEST_OUTPUT_123')"],
                "expected": "contains:TEST_OUTPUT_123"
            },
            {
                "claim": "failure case detection",
                "epistemic_status": "HYPOTHESIS",
                "cmd_args": ["python3", "-c", "import sys; sys.exit(2)"],
                "expected": "exit_code_0"
            }
        ]
    }
    result = execute_evidence_plan(plan)
    assert result["total_probes"] == 2
    assert result["all_verified"] is False
    assert result["results"][0]["verified"] is True
    assert result["results"][1]["verified"] is False
