# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_self_healing_distiller.py"
# purpose: "Unit and Integration Tests for Self-Healing Distillation Loop & Skill Packager."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from apps.api.services.self_healing_distiller import (
    SelfHealingDistiller,
    ErrorSnapshot,
    SolutionProposal
)


@pytest.mark.asyncio
async def test_error_capture_and_hash():
    distiller = SelfHealingDistiller()
    try:
        raise ValueError("Invalid configuration for payment gateway")
    except Exception as e:
        snapshot = distiller.capture_error(e, context={"gateway": "stripe", "amount": 100})

    assert snapshot.error_type == "ValueError"
    assert "Invalid configuration" in snapshot.error_message
    assert len(snapshot.error_hash) == 16
    assert snapshot.context["gateway"] == "stripe"


@pytest.mark.asyncio
async def test_self_healing_distiller_resolution_and_packaging():
    distiller = SelfHealingDistiller(max_retry=3)
    error = KeyError("Missing user_token in session payload")
    
    result = await distiller.handle_error(error, context={"user_id": "usr-123"}, auto_package_skill=True)
    assert result.status == "resolved_by_llm"
    assert result.attempts_made == 1
    assert result.solution is not None
    assert result.skill_path is not None
    assert "keyerror" in result.skill_path.lower()

    # Second call should resolve from knowledge cache (Zero-Guessing)
    cached_result = await distiller.handle_error(error, context={"user_id": "usr-123"})
    assert cached_result.status == "resolved_from_cache"
    assert cached_result.attempts_made == 0


@pytest.mark.asyncio
async def test_circuit_breaker_and_human_review_fallback():
    class UnfixableDistiller(SelfHealingDistiller):
        async def validate_solution(self, proposal: SolutionProposal, snapshot: ErrorSnapshot) -> bool:
            return False  # Force all automated validations to fail

    distiller = UnfixableDistiller(max_retry=3)
    error = RuntimeError("Fatal hardware interrupt / corrupt memory page")
    
    result = await distiller.handle_error(error, context={"node": "worker-01"}, auto_package_skill=False)
    assert result.status == "human_review_required"
    assert result.attempts_made == 3
    assert result.human_review_payload is not None
    assert "Telegram / Slack Alert" in result.human_review_payload["notification_channel"]
    assert "RuntimeError" in result.human_review_payload["title"]
