#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_soup_assimilated_modules.py"
# purpose: "Unit tests for Soup-assimilated modules: PromptShipGate, RewardSynthesizer, ToolSchemaOptimizer."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from core.orchestrator.prompt_ship_gate import (
    PromptShipGate,
    GateVerdict,
)
from core.auditor.reward_synthesizer import (
    RewardSynthesizer,
    VerifierKind,
    UncalibratedVerifierError,
)
from core.orchestrator.tool_optimizer import ToolSchemaOptimizer


# ==========================================
# 1. PromptShipGate (Dual-Leg Regression Gate) Tests
# ==========================================

def test_prompt_ship_gate_approved_when_target_wins_and_guards_pass(tmp_path):
    gate = PromptShipGate(
        target_component="skills/shopify_theme_ast",
        task_improvement_threshold=0.05,
        allowed_guard_regression=0.0,
    )
    target_metrics = {"ast_parsing_accuracy": (0.80, 0.90)}
    guard_metrics = {
        "json_schema_validity": (1.0, 1.0),
        "tool_calling_fidelity": (0.95, 0.95),
        "relative_path_hygiene": (1.0, 1.0),
    }

    evidence = gate.evaluate(target_metrics, guard_metrics)
    assert evidence.verdict == GateVerdict.SHIP
    assert evidence.leg1.won is True
    assert evidence.leg2.passed is True

    # Check evidence saving and rendering
    evidence_file = str(tmp_path / "evidence.json")
    saved_path = gate.save_evidence(evidence, evidence_file)
    assert saved_path == evidence_file

    comment = gate.render_markdown_comment(evidence)
    assert "SHIP VERDICT: APPROVED" in comment
    assert "ast_parsing_accuracy" in comment


def test_prompt_ship_gate_rejected_when_target_fails_leg1():
    gate = PromptShipGate(
        target_component="SOUL.md",
        task_improvement_threshold=0.05,
        allowed_guard_regression=0.0,
    )
    # Target improvement is only +0.01 (< 0.05)
    target_metrics = {"reasoning_depth": (0.85, 0.86)}
    guard_metrics = {"json_schema_validity": (1.0, 1.0)}

    evidence = gate.evaluate(target_metrics, guard_metrics)
    assert evidence.verdict == GateVerdict.DONT_SHIP
    assert evidence.leg1.won is False
    assert evidence.leg2.passed is True
    assert any("Leg 1 Failure" in r for r in evidence.reasons)


def test_prompt_ship_gate_rejected_when_guard_regresses_leg2():
    gate = PromptShipGate(
        target_component="skills/dnk-swarm-orchestration",
        task_improvement_threshold=0.05,
        allowed_guard_regression=0.0,
    )
    # Leg 1 wins big (+0.15), but Leg 2 regresses on path hygiene!
    target_metrics = {"swarm_dispatch_speed": (0.70, 0.85)}
    guard_metrics = {
        "json_schema_validity": (1.0, 1.0),
        "relative_path_hygiene": (1.0, 0.90),  # REGRESSION!
    }

    evidence = gate.evaluate(target_metrics, guard_metrics)
    assert evidence.verdict == GateVerdict.DONT_SHIP
    assert evidence.leg1.won is True
    assert evidence.leg2.passed is False
    assert len(evidence.leg2.regressions) > 0


# ==========================================
# 2. RewardSynthesizer (Deterministic Verifiers) Tests
# ==========================================

def test_reward_synthesizer_json_schema_success():
    code = RewardSynthesizer.synthesize_json_schema_verifier(
        required_keys=["status", "data"],
        expected_types={"status": "str", "data": "dict"},
        fn_name="verify_api_response",
    )

    gold_positives = [
        '{"status": "ok", "data": {"id": 123}}',
        '```json\n{"status": "success", "data": {}}\n```',
    ]
    negative_mutations = [
        '{"status": "ok"}',  # missing data
        '{"status": 123, "data": {}}',  # wrong status type
        'not a json string',
        '[{"status": "ok", "data": {}}]',  # list instead of dict
    ]

    report = RewardSynthesizer.calibrate_verifier(
        verifier_code=code,
        fn_name="verify_api_response",
        gold_positives=gold_positives,
        negative_mutations=negative_mutations,
        kind=VerifierKind.JSON_SCHEMA,
    )

    assert report.calibrated is True
    assert report.positive_pass_rate == 1.0
    assert report.negative_rejection_rate == 1.0


def test_reward_synthesizer_tool_call_calibration():
    code = RewardSynthesizer.synthesize_tool_call_verifier(
        expected_tool_name="dnk_assimilate_repo",
        required_params=["repo_url"],
        fn_name="verify_assimilate_call",
    )

    gold_positives = [
        {"name": "dnk_assimilate_repo", "arguments": {"repo_url": "foo/bar"}},
        {"name": "dnk_assimilate_repo", "arguments": {"repo_url": "baz", "extra": 1}},
    ]
    negative_mutations = [
        {"name": "wrong_tool", "arguments": {"repo_url": "foo/bar"}},
        {"name": "dnk_assimilate_repo", "arguments": {}},  # missing repo_url
        "invalid payload type",
    ]

    report = RewardSynthesizer.calibrate_verifier(
        verifier_code=code,
        fn_name="verify_assimilate_call",
        gold_positives=gold_positives,
        negative_mutations=negative_mutations,
        kind=VerifierKind.TOOL_CALL,
    )
    assert report.calibrated is True


def test_reward_synthesizer_refuses_uncalibrated_verifier():
    # Intentionally broken verifier that accepts anything
    broken_code = """def broken_check(x): return True, 'ok'"""
    with pytest.raises(UncalibratedVerifierError):
        RewardSynthesizer.calibrate_verifier(
            verifier_code=broken_code,
            fn_name="broken_check",
            gold_positives=["positive"],
            negative_mutations=["should_fail"],
            kind=VerifierKind.REGEX,
        )


# ==========================================
# 3. ToolSchemaOptimizer (compile-tools Pattern) Tests
# ==========================================

def test_tool_schema_optimizer_detects_defects_and_heals():
    optimizer = ToolSchemaOptimizer()
    sample_tools = [
        {
            "name": "calc",
            "description": "calc",  # too short (< 15 chars)
            "parameters": {
                "type": "object",
                "properties": {
                    "num": {"description": "data"},  # vague description + missing type
                },
                "required": ["num"],
            },
        },
        {
            "name": "calc",  # duplicate name
            "description": "Calculates advanced numerical transformations and equations.",
            "parameters": {"type": "object", "properties": {}},
        },
    ]

    result = optimizer.audit_and_optimize(sample_tools, auto_heal=True)
    assert result.original_tools_count == 2
    defects = result.defects_found
    assert len(defects) >= 3
    assert any(d.defect_type == "duplicate_name" for d in defects)
    assert any(d.defect_type == "missing_type" for d in defects)
    assert any(d.defect_type == "vague_description" for d in defects)

    # Check auto-heal results
    healed_calc = result.optimized_tools[0]
    assert len(healed_calc["description"]) >= 15
    assert healed_calc["parameters"]["properties"]["num"]["type"] == "string"


def test_tool_schema_optimizer_detects_description_overlap():
    optimizer = ToolSchemaOptimizer()
    overlapping_tools = [
        {
            "name": "search_docs_v1",
            "description": "Searches documentation knowledge base for relevant architectural guidelines and specs.",
            "parameters": {"type": "object", "properties": {}},
        },
        {
            "name": "search_docs_v2",
            "description": "Searches documentation knowledge base for relevant architectural guidelines and specs.",
            "parameters": {"type": "object", "properties": {}},
        },
    ]

    result = optimizer.audit_and_optimize(overlapping_tools, auto_heal=False)
    overlaps = [d for d in result.defects_found if d.defect_type == "overlap"]
    assert len(overlaps) == 1
    assert "search_docs_v1 <-> search_docs_v2" in overlaps[0].tool_name
