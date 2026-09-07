# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-STD-0075"
# purpose: "Unit test suite for validating PatternAuditor script behavior."
# canonical_source: true
# alters_files: ["core/tests/test_pattern_auditor.py"]
# triggers_tasks: ["TF_PATTERN_002_AND_AUDITOR"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-08"
# --- END DNK-MRH-HEADER ---

import os
import sys
import pytest
from pathlib import Path

# Setup python path to find core/
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent # Resolve to DNK_HUB root
sys.path.insert(0, str(BASE_DIR))

from core.playbooks.scripts.pattern_auditor import PatternAuditor, REPORT_PATH

REGISTRY_PATH = "docs/tech/SPEC_02_Agentic_Patterns_Registry.md"
SCHEMA_PATH = "docs/schemas/agentic_pattern_schema.json"

def test_auditor_initialization():
    """Verify that PatternAuditor initializes successfully with default paths."""
    auditor = PatternAuditor(registry_path=REGISTRY_PATH, schema_path=SCHEMA_PATH)
    assert auditor.registry_path == REGISTRY_PATH
    assert auditor.schema_path == SCHEMA_PATH
    assert auditor.synthesizer is not None

def test_auditor_run_success():
    """Verify that the production pattern registry is completely compliant and passes audit with zero errors."""
    auditor = PatternAuditor(registry_path=REGISTRY_PATH, schema_path=SCHEMA_PATH)
    results = auditor.run_audit()
    
    assert results["schema_validity"] == "PASSED"
    assert results["deduplication"] == "PASSED"
    assert results["mrh_compliance"] == "PASSED"
    assert results["performance_check"] == "PASSED"
    assert len(results["errors"]) == 0, f"Expected 0 audit errors, got: {results['errors']}"

def test_auditor_generate_report(tmp_path):
    """Verify that generate_report successfully writes the markdown audit file."""
    auditor = PatternAuditor(registry_path=REGISTRY_PATH, schema_path=SCHEMA_PATH)
    results = auditor.run_audit()
    
    temp_report = tmp_path / "AUDIT_REPORT_TEST.md"
    auditor.generate_report(results, output_path=str(temp_report))
    
    assert temp_report.exists()
    content = temp_report.read_text(encoding="utf-8")
    assert "Звіт автоматичного аудиту реєстру патернів" in content
    assert "Schema Validity" in content
    assert "MRH Compliance" in content

def test_auditor_failure_on_duplicate_ids(tmp_path):
    """Verify that duplicate IDs trigger deduplication failure in the audit run."""
    temp_registry = tmp_path / "corrupt_registry.md"
    
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        registry_text = f.read()
        
    import re
    import json
    json_blocks = re.findall(r"```json\s*(.*?)\s*```", registry_text, re.DOTALL)
    assert len(json_blocks) > 0
    
    parsed = json.loads(json_blocks[0])
    # Duplicate the first pattern card
    duplicate_item = parsed[0].copy()
    parsed.append(duplicate_item)
    
    new_json_block = json.dumps(parsed, indent=2, ensure_ascii=False)
    corrupt_text = registry_text.replace(json_blocks[0], new_json_block)
    temp_registry.write_text(corrupt_text, encoding="utf-8")
    
    auditor = PatternAuditor(registry_path=str(temp_registry), schema_path=SCHEMA_PATH)
    results = auditor.run_audit()
    
    assert results["deduplication"] == "FAILED"
    assert any("Duplicate Pattern IDs found" in e for e in results["errors"])