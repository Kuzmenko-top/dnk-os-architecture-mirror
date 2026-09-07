# --- DNK-MRH-HEADER ---
# mrh_id: "tests/guards/test_habit_judge.py"
# purpose: "Unit tests for Tier 3 HabitJudge & EvidenceLedger anti-habit violation detection."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Auditor"
# --- END DNK-MRH-HEADER ---

import pytest
from core.guards.habit_judge import (
    EvidenceLedger,
    EvidenceType,
    HabitJudge,
)


def test_evidence_ledger_separation():
    ledger = EvidenceLedger()
    ledger.record_raw(source="terminal", content="pytest tests/ -> exit 0", metadata={"exit_code": 0})
    ledger.record_infer(source="assistant_speech", content="I believe the code is correct.")

    assert len(ledger.get_raw_entries()) == 1
    assert len(ledger.get_infer_entries()) == 1
    assert ledger.get_raw_entries()[0].entry_type == EvidenceType.RAW
    assert ledger.get_infer_entries()[0].entry_type == EvidenceType.INFER


def test_habit_judge_detects_phantom_done_when_no_raw_test_pass():
    ledger = EvidenceLedger()
    judge = HabitJudge(ledger=ledger)

    verdict = judge.audit(task_claim="All tests passed with 100% green status!")
    assert verdict.passed is False
    assert any("PHANTOM_DONE" in v for v in verdict.violations)


def test_habit_judge_passes_when_raw_test_evidence_exists():
    ledger = EvidenceLedger()
    ledger.record_raw(
        source="test_runner",
        content="pytest tests/guards/ -> 5 passed in 0.2s",
        metadata={"exit_code": 0},
    )
    judge = HabitJudge(ledger=ledger)

    verdict = judge.audit(task_claim="All tests passed with 100% green status!")
    assert verdict.passed is True
    assert verdict.score == 100.0
    assert "PASS" in verdict.summary


def test_habit_judge_detects_drive_by_refactor():
    ledger = EvidenceLedger()
    ledger.record_raw(source="test_runner", content="pytest passed", metadata={"exit_code": 0})
    judge = HabitJudge(ledger=ledger)

    verdict = judge.audit(
        task_claim="Implemented feature cleanly",
        target_files=["core/guards/habit_judge.py"],
        touched_files=["core/guards/habit_judge.py", "unrelated_secret_file.py"],
    )
    assert verdict.passed is False
    assert any("DRIVE_BY_REFACTOR" in v for v in verdict.violations)


def test_habit_judge_detects_narration_theatre():
    ledger = EvidenceLedger()
    # 6 inferential assertions without any raw tool action
    for i in range(6):
        ledger.record_infer(source="assistant", content=f"Step {i} was carefully reasoned through in thought.")
    judge = HabitJudge(ledger=ledger)

    verdict = judge.audit(task_claim="Analysis complete")
    assert verdict.passed is False
    assert any("NARRATION_THEATRE" in v for v in verdict.violations)
