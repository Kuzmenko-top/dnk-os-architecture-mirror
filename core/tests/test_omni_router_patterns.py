# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Automated test suite to verify the OmniRouter pattern injection integration."
# canonical_source: true
# alters_files: ["core/tests/test_omni_router_patterns.py"]
# triggers_tasks: ["TF_OMNI_ROUTER_PATTERN_INJECTION"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-08"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from core.omni_router import OmniRouter

def test_omni_router_injection_success():
    """Verify that omni_router automatically injects matching patterns into dispatch dictionary."""
    router = OmniRouter()
    assert router.synthesizer is not None, "OmniRouter failed to initialize PatternSynthesizer."

    # Dispatch task matching 'Orchestrator'
    result = router.dispatch("Design an Orchestrator and worker setup")
    assert result["status"] == "dispatched"
    assert "injected_patterns" in result
    
    injected = result["injected_patterns"]
    assert len(injected) > 0, "Expected at least one pattern matching 'Orchestrator' to be injected."
    assert any(p["id"] == "DNK-PAT-001" for p in injected), "Expected Orchestrator-Workers (DNK-PAT-001) in injected patterns."

def test_omni_router_injection_no_match():
    """Verify that dispatch proceeds normally and injected_patterns is empty when no matching patterns are found."""
    router = OmniRouter()
    
    # Non-matching task goal
    result = router.dispatch("Make a cup of hot coffee with milk")
    assert result["status"] == "dispatched"
    assert "injected_patterns" in result
    assert len(result["injected_patterns"]) == 0, "Expected zero injected patterns for non-matching goal."

def test_omni_router_non_blocking_on_missing_registry(tmp_path):
    """Verify that OmniRouter remains fully functional and non-blocking even if the patterns registry is completely missing."""
    # Point synthesizer to a non-existent path
    fake_registry = tmp_path / "missing_registry.md"
    schema_path = "docs/schemas/agentic_pattern_schema.json"
    
    from core.pattern_synthesizer import PatternSynthesizer
    
    # Initialize a new router and override synthesizer with fake path
    router = OmniRouter()
    router.synthesizer = PatternSynthesizer(registry_path=str(fake_registry), schema_path=schema_path)
    
    # Dispatch should not raise any errors, just return empty injected_patterns
    result = router.dispatch("Orchestrator workers task")
    assert result["status"] == "dispatched"
    assert len(result["injected_patterns"]) == 0
