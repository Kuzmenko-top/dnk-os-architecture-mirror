# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Unit test suite for validating PatternSynthesizer module behavior."
# canonical_source: true
# alters_files: ["core/tests/test_pattern_synthesizer.py"]
# triggers_tasks: ["TF_CORE_PATTERN_SYNTHESIZER"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-08"
# --- END DNK-MRH-HEADER ---

import os
import json
import time
import pytest
from jsonschema import ValidationError
from core.pattern_synthesizer import PatternSynthesizer

REGISTRY_PATH = "docs/tech/SPEC_02_Agentic_Patterns_Registry.md"
SCHEMA_PATH = "docs/schemas/agentic_pattern_schema.json"

class MockSwarmOrchestrator:
    def __init__(self):
        self.skills = []

    def register_skill(self, skill):
        self.skills.append(skill)

@pytest.fixture
def temp_registry(tmp_path):
    # Ensure cleanup before test
    temp_file = tmp_path / "temp_patterns_registry.md"
    if os.path.exists(temp_file):
        os.remove(temp_file)
        
    # Pre-populate with current registry
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    temp_file.write_text(content, encoding="utf-8")
    
    yield str(temp_file)
    
    # Cleanup after test
    if os.path.exists(temp_file):
        os.remove(temp_file)

def test_synthesizer_initialization():
    """Verify synthesizer initializes and loads existing patterns and schema successfully."""
    synthesizer = PatternSynthesizer(registry_path=REGISTRY_PATH, schema_path=SCHEMA_PATH)
    assert len(synthesizer.patterns) >= 8, "Expected at least 8 patterns to be preloaded (7 Core + 1 AGNT)."
    assert synthesizer.schema is not None

def test_pattern_validation_success():
    """Verify validation passes for conformant pattern cards."""
    synthesizer = PatternSynthesizer(registry_path=REGISTRY_PATH, schema_path=SCHEMA_PATH)
    valid_pattern = {
        "id": "DNK-PAT-008",
        "name": "Test Pattern",
        "description": "A valid test pattern for unit testing.",
        "type": "Multi-Agent System",
        "roles": ["Tester"],
        "triggers": ["When tests run"],
        "validation_methods": ["pytest check"],
        "metadata": {
            "status": "Active",
            "version": "1.0.0"
        }
    }
    assert synthesizer.validate_pattern(valid_pattern) is True

def test_pattern_validation_failure():
    """Verify validation raises ValidationError for non-conformant pattern cards."""
    synthesizer = PatternSynthesizer(registry_path=REGISTRY_PATH, schema_path=SCHEMA_PATH)
    
    # Missing required field 'roles'
    invalid_pattern = {
        "id": "DNK-PAT-009",
        "name": "Invalid Pattern",
        "description": "Missing fields.",
        "type": "Multi-Agent System",
        "triggers": ["Always"],
        "validation_methods": ["None"]
    }
    with pytest.raises(ValidationError):
        synthesizer.validate_pattern(invalid_pattern)

def test_synthesize_pattern_success(temp_registry):
    """Test successful pattern creation and Markdown export using synthesize_pattern."""
    synthesizer = PatternSynthesizer(registry_path=temp_registry, schema_path=SCHEMA_PATH)
    initial_count = len(synthesizer.patterns)
    
    new_pat = synthesizer.synthesize_pattern(
        name="Adaptive Self-Healer Flow",
        description="Captures runtime errors and synthesizes repairs.",
        pattern_type="Optimization Loop",
        roles=["Repair Bot"],
        triggers=["Syntax Error"],
        validation_methods=["AST check"]
    )
    
    assert new_pat["id"] == "DNK-PAT-008"
    assert new_pat["name"] == "Adaptive Self-Healer Flow"
    assert len(synthesizer.patterns) == initial_count + 1
    
    # Reload and verify
    reloaded = PatternSynthesizer(registry_path=temp_registry, schema_path=SCHEMA_PATH)
    assert len(reloaded.patterns) == initial_count + 1
    assert any(p["id"] == "DNK-PAT-008" for p in reloaded.patterns)

def test_synthesize_pattern_duplicate_rejection(temp_registry):
    """Test that creating a pattern with a case-insensitive duplicate name is rejected."""
    synthesizer = PatternSynthesizer(registry_path=temp_registry, schema_path=SCHEMA_PATH)
    
    # Orchestrator-Workers is already defined in the registry
    with pytest.raises(ValueError, match="already exists"):
        synthesizer.synthesize_pattern(
            name="Orchestrator-Workers (Оркестратор - Воркери)",
            description="Duplicate name testing.",
            pattern_type="Multi-Agent System",
            roles=["Any"],
            triggers=["Any"],
            validation_methods=["Any"]
        )

def test_synthesize_pattern_empty_validation(temp_registry):
    """Test validation of empty strings and lists."""
    synthesizer = PatternSynthesizer(registry_path=temp_registry, schema_path=SCHEMA_PATH)
    
    # Empty name
    with pytest.raises(ValueError, match="name cannot be empty"):
        synthesizer.synthesize_pattern(
            name="  ",
            description="Some desc",
            pattern_type="Optimization Loop",
            roles=["Role"],
            triggers=["Trigger"],
            validation_methods=["Method"]
        )
        
    # Empty roles
    with pytest.raises(ValueError, match="Roles list or elements cannot be empty"):
        synthesizer.synthesize_pattern(
            name="Valid Name",
            description="Some desc",
            pattern_type="Optimization Loop",
            roles=[],
            triggers=["Trigger"],
            validation_methods=["Method"]
        )
        
    # Empty element in roles
    with pytest.raises(ValueError, match="Roles list or elements cannot be empty"):
        synthesizer.synthesize_pattern(
            name="Valid Name",
            description="Some desc",
            pattern_type="Optimization Loop",
            roles=["Role", ""],
            triggers=["Trigger"],
            validation_methods=["Method"]
        )

def test_register_in_orchestrator(temp_registry):
    """Test that register_in_orchestrator registers the pattern correctly as a skill."""
    synthesizer = PatternSynthesizer(registry_path=temp_registry, schema_path=SCHEMA_PATH)
    orchestrator = MockSwarmOrchestrator()
    
    pattern = {
        "id": "DNK-PAT-008",
        "name": "Adaptive Self-Healer Flow",
        "description": "Captures runtime errors and synthesizes repairs.",
        "type": "Optimization Loop",
        "roles": ["Repair Bot"],
        "triggers": ["Syntax Error"],
        "validation_methods": ["AST check"]
    }
    
    synthesizer.register_in_orchestrator(orchestrator, pattern)
    assert len(orchestrator.skills) == 1
    assert orchestrator.skills[0] == pattern

def test_add_pattern_with_prefixes(temp_registry):
    """Verify that add_pattern supports both DNK-PAT and DNK-AGNT generation and auto-increments properly."""
    synthesizer = PatternSynthesizer(registry_path=temp_registry, schema_path=SCHEMA_PATH)
    
    # 1. Add DNK-PAT card (should get DNK-PAT-008)
    pat_card = synthesizer.add_pattern(
        name="Self-Healing Code Execution",
        description="Automatically captures runtime errors and heals scripts.",
        pattern_type="Optimization Loop",
        roles=["Self-Healer"],
        triggers=["Script exit code > 0"],
        validation_methods=["Liveness tests"],
        prefix="DNK-PAT"
    )
    assert pat_card["id"] == "DNK-PAT-008"

    # 2. Add DNK-AGNT card (should get DNK-AGNT-002, since DNK-AGNT-001 is already preloaded)
    agnt_card = synthesizer.add_pattern(
        name="Dynamic Context Compression Engine",
        description="Lossless compression of long dialogue context.",
        pattern_type="Task Enrichment",
        roles=["Compressor"],
        triggers=["Context window warnings"],
        validation_methods=["Token count audits"],
        prefix="DNK-AGNT"
    )
    assert agnt_card["id"] == "DNK-AGNT-003"

def test_search_patterns_performance_and_accuracy():
    """Verify search_patterns returns correct matches and executes well under the 0.05s target."""
    synthesizer = PatternSynthesizer(registry_path=REGISTRY_PATH, schema_path=SCHEMA_PATH)
    
    start_time = time.perf_counter()
    matches = synthesizer.search_patterns("Orchestrator")
    duration = time.perf_counter() - start_time
    
    assert duration < 0.05, f"Search took too long: {duration:.5f}s (target < 0.05s)"
    assert len(matches) > 0, "Expected matches for keyword 'Orchestrator'"
    assert any(m["id"] == "DNK-PAT-001" for m in matches)
