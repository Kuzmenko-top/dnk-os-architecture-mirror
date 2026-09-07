# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Automated test suite to verify the Agentic Pattern Registry and JSON schema validation."
# canonical_source: true
# alters_files: ["core/tests/test_agentic_patterns.py"]
# triggers_tasks: ["TF_REGISTRY_PATTERN_001_ENRICHMENT"]
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-08"
# --- END DNK-MRH-HEADER ---

import os
import json
import re
import pytest
from jsonschema import validate, ValidationError

REGISTRY_PATH = "docs/tech/SPEC_02_Agentic_Patterns_Registry.md"
SCHEMA_PATH = "docs/schemas/agentic_pattern_schema.json"
TEST_PATH = "core/tests/test_agentic_patterns.py"

def test_mrh_header_presence():
    """Verify that all 3 files contain the standard DNK-STD-0075 MRH header."""
    
    # 1. Test Markdown Registry file
    assert os.path.exists(REGISTRY_PATH), f"Registry file not found at {REGISTRY_PATH}"
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry_content = f.read()
    
    assert "DNK-MRH-HEADER" in registry_content
    assert 'mrh_id: "DNK-STD-0075"' in registry_content
    assert "--- END DNK-MRH-HEADER ---" in registry_content

    # 2. Test Test file itself
    assert os.path.exists(TEST_PATH), f"Test file not found at {TEST_PATH}"
    with open(TEST_PATH, "r", encoding="utf-8") as f:
        test_content = f.read()
    
    assert "DNK-MRH-HEADER" in test_content
    assert 'mrh_id: "DNK-STD-0075"' in test_content
    assert "--- END DNK-MRH-HEADER ---" in test_content

    # 3. Test JSON Schema file
    assert os.path.exists(SCHEMA_PATH), f"Schema file not found at {SCHEMA_PATH}"
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_data = json.load(f)
    
    assert "_mrh_header" in schema_data, "JSON Schema should contain '_mrh_header' block."
    header = schema_data["_mrh_header"]
    assert header.get("mrh_id") == "DNK-STD-0075", "Schema mrh_id must be 'DNK-STD-0075'"
    assert header.get("status") == "Active", "Schema header status must be 'Active'"

def test_registry_contains_seven_patterns():
    """Ensure the markdown registry describes 7 patterns and the enriched agent card."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check core patterns
    for i in range(1, 8):
        pattern_id = f"DNK-PAT-00{i}"
        assert pattern_id in content, f"Registry is missing {pattern_id}"
        
    # Check enrichment pattern
    assert "DNK-AGNT-001" in content, "Registry is missing DNK-AGNT-001"

def test_json_block_extraction_and_schema_validation():
    """Extract patterns from JSON code block in registry and validate them using schema."""
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find JSON blocks inside registry
    json_blocks = re.findall(r"```json\s*(.*?)\s*```", content, re.DOTALL)
    assert len(json_blocks) > 0, "No JSON block found in markdown registry."
    
    # Parse patterns
    patterns_data = None
    for block in json_blocks:
        try:
            parsed = json.loads(block)
            if isinstance(parsed, list) and len(parsed) > 0 and "id" in parsed[0]:
                patterns_data = parsed
                break
        except json.JSONDecodeError:
            continue
            
    assert patterns_data is not None, "Failed to locate or parse the patterns JSON array inside the registry."
    assert len(patterns_data) == 9, f"Expected 8 pattern cards in JSON array (7 Core + 1 Enrichment), got {len(patterns_data)}"
    
    # Load schema
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
        
    # Remove _mrh_header from schema since it's metadata for the schema file itself
    schema_clean = schema.copy()
    if "_mrh_header" in schema_clean:
        del schema_clean["_mrh_header"]
        
    # Validate each pattern card against schema
    for pattern in patterns_data:
        try:
            validate(instance=pattern, schema=schema_clean)
        except ValidationError as exc:
            pytest.fail(f"Pattern {pattern.get('id', 'Unknown')} failed schema validation: {exc.message}")
