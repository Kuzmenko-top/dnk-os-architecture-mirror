# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_adaptive_prompt.py"
# purpose: "Unit tests for adaptive system prompt pruning and complexity tier classification."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import pytest
from core.orchestrator.adaptive_prompt import (
    AdaptivePromptBuilder,
    ComplexityLevel,
    PromptTier,
    TaskSpec,
    build_adaptive_prompt,
    classify_prompt_tier,
    estimate_prompt_tokens,
    get_prompt_token_savings,
)


def test_classify_prompt_tier_simple():
    tier = classify_prompt_tier(complexity_score=2, mode="SOLO", domains_count=1)
    assert tier == PromptTier.SIMPLE

    # With default domains_count
    tier_def = classify_prompt_tier(complexity_score=1, mode="SOLO")
    assert tier_def == PromptTier.SIMPLE

    # Resume in flight
    tier_resume = classify_prompt_tier(complexity_score=1, mode="RESUME_IN_FLIGHT")
    assert tier_resume == PromptTier.SIMPLE


def test_classify_prompt_tier_medium():
    tier = classify_prompt_tier(complexity_score=6, mode="SOLO", domains_count=2)
    assert tier == PromptTier.MEDIUM

    tier_seq = classify_prompt_tier(complexity_score=5, mode="SWARM_SEQUENTIAL", domains_count=2)
    assert tier_seq == PromptTier.MEDIUM


def test_classify_prompt_tier_complex():
    tier = classify_prompt_tier(complexity_score=12, mode="SWARM_PARALLEL", domains_count=3)
    assert tier == PromptTier.COMPLEX


def test_adaptive_prompt_builder_levels():
    builder = AdaptivePromptBuilder()

    # Simple spec
    simple_spec = TaskSpec(target_files=1, estimated_steps=3, description="Fix typo")
    assert builder.estimate_complexity(simple_spec) == ComplexityLevel.SIMPLE
    prompt_simple = builder.build_prompt(simple_spec)
    assert "Fix typo" in prompt_simple
    assert "Execute task efficiently" in prompt_simple

    # Medium spec
    medium_spec = TaskSpec(target_files=4, estimated_steps=10, description="Add new API router")
    assert builder.estimate_complexity(medium_spec) == ComplexityLevel.MEDIUM
    prompt_medium = builder.build_prompt(medium_spec)
    assert "Add new API router" in prompt_medium

    # Complex spec
    complex_spec = TaskSpec(target_files=8, estimated_steps=25, description="Full brand launch")
    assert builder.estimate_complexity(complex_spec) == ComplexityLevel.COMPLEX
    prompt_complex = builder.build_prompt(complex_spec)
    assert "Full brand launch" in prompt_complex


def test_build_adaptive_prompt_with_catalog():
    catalog = "### Compact Catalog: terminal, read_file"
    prompt = build_adaptive_prompt(
        tier=PromptTier.SIMPLE,
        task_goal="Quick bugfix",
        custom_tool_catalog=catalog,
    )
    assert "Quick bugfix" in prompt
    assert catalog in prompt


def test_prompt_token_savings_metric():
    prompt = build_adaptive_prompt(tier=PromptTier.SIMPLE, task_goal="Simple fix")
    tokens = estimate_prompt_tokens(prompt)
    savings = get_prompt_token_savings(prompt)

    # Baseline is 15,000 tokens
    assert savings["baseline_tokens"] == 15000
    assert savings["prompt_tokens"] == tokens
    # Simple prompt should be well below 2,000 tokens (>80% savings)
    assert savings["savings_pct"] >= 80.0
