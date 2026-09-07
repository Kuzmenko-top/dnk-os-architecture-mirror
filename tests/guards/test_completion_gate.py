# --- DNK-MRH-HEADER ---
# mrh_id: "tests/guards/test_completion_gate.py"
# purpose: "Unit tests for Tier 2 CompletionGate (anti-phantom-done, fail-open, hedging disclosures)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Auditor"
# --- END DNK-MRH-HEADER ---

import pytest
from core.guards.completion_gate import CompletionGate, VerificationEvidence


def test_completion_gate_allows_when_no_success_claim():
    gate = CompletionGate()
    evidence = VerificationEvidence()
    verdict = gate.evaluate("I have written the file and will inspect it next.", evidence)
    assert verdict.allowed is True
    assert verdict.reason is None


def test_completion_gate_blocks_phantom_done_english():
    gate = CompletionGate()
    evidence = VerificationEvidence()
    verdict = gate.evaluate("All unit tests pass and the build is clean.", evidence)
    assert verdict.allowed is False
    assert verdict.reason is not None
    assert "anti-phantom-done" in verdict.reason.lower()


def test_completion_gate_blocks_phantom_done_ukrainian():
    gate = CompletionGate()
    evidence = VerificationEvidence()
    verdict = gate.evaluate("Всі тести успішно пройшли, задача завершена.", evidence)
    assert verdict.allowed is False
    assert verdict.reason is not None
    assert "anti-phantom-done" in verdict.reason.lower()


def test_completion_gate_allows_when_evidence_has_test_pass():
    gate = CompletionGate()
    evidence = VerificationEvidence(
        commands_executed=["pytest tests/test_core.py"],
        exit_codes=[0],
        test_passed=True,
    )
    verdict = gate.evaluate("All unit tests pass and verify_all.sh is clean.", evidence)
    assert verdict.allowed is True


def test_completion_gate_respects_hedging_disclaimer():
    gate = CompletionGate()
    evidence = VerificationEvidence()
    verdict = gate.evaluate("I have not run tests yet because the environment is configuring.", evidence)
    assert verdict.allowed is True
