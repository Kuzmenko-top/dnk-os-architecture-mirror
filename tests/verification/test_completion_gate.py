# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_completion_gate.py"
# purpose: "Unit tests for Tier 2 CompletionGate (Phantom Done & Green-Washing prevention)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import pytest
from core.guards.completion_gate import CompletionGate, VerificationEvidence


def test_completion_gate_allows_normal_message():
    gate = CompletionGate()
    verdict = gate.evaluate("I have refactored the router function in apps/api/main.py.")
    assert verdict.allowed is True
    assert verdict.reason is None


def test_completion_gate_blocks_unverified_claim_en():
    gate = CompletionGate()
    verdict = gate.evaluate("The fix is complete and all unit tests pass.")
    assert verdict.allowed is False
    assert "BLOCKED by CompletionGate" in verdict.reason
    assert "all unit tests pass" in verdict.detected_claim


def test_completion_gate_blocks_unverified_claim_ua():
    gate = CompletionGate()
    verdict = gate.evaluate("Задачу виконано, всі тести успішно пройшли.")
    assert verdict.allowed is False
    assert "BLOCKED by CompletionGate" in verdict.reason
    assert "всі тести успішно пройшли" in verdict.detected_claim


def test_completion_gate_allows_claim_with_real_evidence():
    gate = CompletionGate()
    evidence = VerificationEvidence(
        commands_executed=["pytest tests/verification/test_obsidian_vault_path_hygiene.py"],
        exit_codes=[0],
        test_passed=True,
    )
    verdict = gate.evaluate("All tests pass cleanly now.", evidence=evidence)
    assert verdict.allowed is True
    assert verdict.detected_claim == "All tests pass"


def test_completion_gate_allows_honest_hedging():
    gate = CompletionGate()
    # Honest disclosure: has not run tests -> Allowed (Reward Disclosure)
    verdict = gate.evaluate("I updated the configuration, but have not run tests yet.")
    assert verdict.allowed is True

    verdict_ua = gate.evaluate("Код оновлено, проте я не тестував його через відсутність середовища.")
    assert verdict_ua.allowed is True


def test_completion_gate_fail_open_recursion_guard():
    gate = CompletionGate()
    evidence = VerificationEvidence(
        commands_executed=[],
        exit_codes=[],
        test_passed=False,
        stop_hook_active=True,  # Recursion guard active
    )
    verdict = gate.evaluate("All tests pass", evidence=evidence)
    assert verdict.allowed is True
