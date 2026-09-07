# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_adversarial_probes.py"
# purpose: "Unit and Integration Tests for Adversarial Probe Library, ASR Metrics & 3-Stage Gate."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from core.security.adversarial_probe_library import (
    AdversarialProbeLibrary,
    AdversarialEvaluationEngine,
    GateStage,
    AttackCategory
)


def test_probe_library_catalog_size():
    """Verify probe library contains at least 200+ specialized adversarial scenarios."""
    lib = AdversarialProbeLibrary()
    total = lib.total_count()
    assert total >= 200, f"Expected >= 200 probes, got {total}"


def test_probe_library_stage_distribution():
    """Verify all 3 gate stages are represented with appropriate probe counts."""
    lib = AdversarialProbeLibrary()
    stage1_probes = lib.get_probes(stage=GateStage.STAGE_1_PR)
    stage2_probes = lib.get_probes(stage=GateStage.STAGE_2_PRE_DEPLOY)
    stage3_probes = lib.get_probes(stage=GateStage.STAGE_3_PROD_DRIFT)

    assert len(stage1_probes) >= 80, f"Stage 1 has {len(stage1_probes)} probes"
    assert len(stage2_probes) >= 90, f"Stage 2 has {len(stage2_probes)} probes"
    assert len(stage3_probes) >= 30, f"Stage 3 has {len(stage3_probes)} probes"


def test_probe_library_categories():
    """Verify all critical vulnerability categories exist in the probe suite."""
    lib = AdversarialProbeLibrary()
    categories = [
        AttackCategory.TOKEN_LEAK,
        AttackCategory.PROMPT_INJECTION,
        AttackCategory.PATH_TRAVERSAL,
        AttackCategory.SSRF,
        AttackCategory.SQL_INJECTION,
        AttackCategory.ASYNC_DEADLOCK_REDOS,
        AttackCategory.CORS_CSRF,
        AttackCategory.MEMORY_POISONING,
        AttackCategory.CANARY_PROBE
    ]
    for cat in categories:
        probes = lib.get_probes(category=cat)
        assert len(probes) > 0, f"Missing probes for category {cat.value}"


def test_adversarial_evaluation_engine_pr_gate():
    """Verify evaluation engine enforces < 5% ASR on Stage 1 PR Gate."""
    engine = AdversarialEvaluationEngine()
    
    # Safe candidate code snippet
    safe_code = """
    # Safe production module
    import os
    def get_user_id(session_id: str) -> str:
        return session_id.strip()
    """
    
    result = engine.evaluate_text_defense(safe_code, stage=GateStage.STAGE_1_PR)
    assert result["gate_verdict"] == "PASSED"
    assert result["attack_success_rate_percent"] < 5.0
    assert result["blocked_count"] > 0


def test_adversarial_evaluation_engine_pre_deploy_gate():
    """Verify evaluation engine enforces < 5% ASR on Stage 2 Pre-Deploy Gate."""
    engine = AdversarialEvaluationEngine()
    
    # Safe production code with parameterized DB and timeout
    safe_service = """
    async def fetch_user(user_id: str, db_pool):
        query = "SELECT id, name FROM users WHERE id = $1"
        return await db_pool.fetchrow(query, user_id)
    """
    
    result = engine.evaluate_text_defense(safe_service, stage=GateStage.STAGE_2_PRE_DEPLOY)
    assert result["gate_verdict"] == "PASSED"
    assert result["attack_success_rate_percent"] < 5.0
