# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_canvas_pattern_sync.py"
# purpose: "Unit tests for canvas engine pattern sync and loop-free DAG assertion."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.2"
# updated_at: "2026-08-08"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from core.canvas_engine import CanvasEngine
from core.playbooks.scripts.pattern_auditor import run_audit

REGISTRY_PATH = "docs/tech/SPEC_02_Agentic_Patterns_Registry.md"
REPORT_PATH = "docs/reports/PATTERN_AUDIT_REPORT.md"

def test_canvas_pattern_sync_and_dag():
    """Verify that sync_with_pattern_registry creates 8+ DocNodes/PatternNodes and has_cycle remains False."""
    engine = CanvasEngine()
    engine.sync_with_pattern_registry(registry_path=REGISTRY_PATH)

    # We expect 8+ nodes synced (the registry contains 9 patterns)
    assert len(engine.nodes) >= 8, f"Expected 8+ nodes, found {len(engine.nodes)}"
    
    # Assert type DocNode or PatternNode and state Done
    for node in engine.nodes.values():
        assert node.type in ["DocNode", "PatternNode"]
        assert node.state == "Done"

    # Assert loop-free / DAG condition
    assert engine.has_cycle() is False, "The canvas graph should be acyclic (DAG)."

def test_pattern_auditor_creates_report():
    """Verify that pattern auditor runs cleanly and creates the audit report."""
    if os.path.exists(REPORT_PATH):
        os.remove(REPORT_PATH)

    run_audit(registry_path=REGISTRY_PATH, report_path=REPORT_PATH)
    assert os.path.exists(REPORT_PATH), "PATTERN_AUDIT_REPORT.md should be created."

    # Read report to verify it is non-empty
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    # Align assertion with test_pattern_auditor.py (Ukrainian text)
    assert "Звіт автоматичного аудиту реєстру патернів" in content
    assert "Summary" in content
