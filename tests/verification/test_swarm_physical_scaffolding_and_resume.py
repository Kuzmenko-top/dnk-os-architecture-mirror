# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_swarm_physical_scaffolding_and_resume.py"
# purpose: "Verify physical file scaffolding by Swarm Workers and In-Flight Compaction Resume in task_triage.py."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import os
from pathlib import Path
import pytest

from core.orchestrator.swarm_coordinator import swarm_coordinator
from core.orchestrator.task_triage import dnk_triage_task

HUB_ROOT = Path(__file__).resolve().parent.parent.parent


def test_swarm_coordinator_physical_scaffolding(tmp_path):
    """Verifies that fullstack, librarian, and shopify workers physically scaffold files."""
    test_py = "tests/fixtures/scaffold_test_module.py"
    test_md = "tests/fixtures/scaffold_test_doc.md"
    test_liquid = "tests/fixtures/scaffold_test_view.liquid"

    py_path = HUB_ROOT / test_py
    md_path = HUB_ROOT / test_md
    liquid_path = HUB_ROOT / test_liquid

    # Clean before
    for p in (py_path, md_path, liquid_path):
        if p.exists():
            p.unlink()

    tasks = [
        {
            "agent": "dnk_dev_fullstack",
            "action": "scaffold_api",
            "payload": {"target_files": [test_py]},
        },
        {
            "agent": "herich_librarian",
            "action": "scaffold_docs",
            "payload": {"target_files": [test_md]},
        },
        {
            "agent": "dnk_shopify",
            "action": "scaffold_liquid",
            "payload": {"target_files": [test_liquid]},
        },
    ]

    try:
        res = swarm_coordinator.dispatch_parallel(tasks)
        assert res["status"] == "parallel_batch_completed"
        assert len(res["completed_tasks"]) == 3
        assert "trace_id" in res and res["trace_id"]
        assert all("trace_id" in t and t["trace_id"] for t in res["completed_tasks"])

        # Verify physical existence on disk
        assert py_path.exists(), "Python file was not scaffolded on disk!"
        py_content = py_path.read_text(encoding="utf-8")
        assert "DNK-MRH-HEADER" in py_content
        assert "dnk_dev_fullstack" in py_content

        assert md_path.exists(), "Markdown doc was not scaffolded on disk!"
        md_content = md_path.read_text(encoding="utf-8")
        assert "DNK-MRH-HEADER" in md_content
        assert "herich_librarian" in md_content

        assert liquid_path.exists(), "Liquid template was not scaffolded on disk!"
        liquid_content = liquid_path.read_text(encoding="utf-8")
        assert "DNK-MRH-HEADER" in liquid_content
        assert "dnk_shopify" in liquid_content

    finally:
        # Cleanup
        for p in (py_path, md_path, liquid_path):
            if p.exists():
                p.unlink()


def test_task_triage_in_flight_resume_detection():
    """Verifies that dnk_triage_task returns RESUME_IN_FLIGHT when declared [NEW] files exist."""
    # Existing files in repo
    prompt_in_flight = """
    # 🎯 СЛАЙС 12.3: Monitoring & Alerting
    ## 📁 ЦІЛЬОВІ ФАЙЛИ
    - [NEW] apps/api/monitoring/health_check.py
    - [NEW] apps/api/monitoring/metrics.py
    - [NEW] apps/api/monitoring/alerts.py
    - [NEW] docs/monitoring/ALERTING.md
    """
    res = dnk_triage_task(prompt_in_flight)
    assert res.mode == "RESUME_IN_FLIGHT"
    assert res.complexity_score == 1
    assert "In-Flight Task Resumption" in res.rationale
    assert "Do NOT re-dispatch swarm" in res.mandatory_directive


def test_task_triage_compaction_marker_detection():
    """Verifies that [CONTEXT COMPACTION marker routes to RESUME_IN_FLIGHT."""
    prompt_compacted = """
    [CONTEXT COMPACTION — REFERENCE ONLY] Earlier turns were compacted into the summary below.
    # 🎯 СЛАЙС 12.3: Monitoring & Alerting
    ## 📁 ЦІЛЬОВІ ФАЙЛИ
    - [NEW] apps/api/monitoring/health_check.py
    """
    res = dnk_triage_task(prompt_compacted)
    assert res.mode == "RESUME_IN_FLIGHT"
    assert res.complexity_score == 1


def test_swarm_coordinator_auto_target_files_extraction():
    """Verifies that swarm_coordinator extracts target files from spec/description if target_files is empty."""
    test_py = "tests/fixtures/auto_extracted_test.py"
    test_md = "tests/fixtures/auto_extracted_doc.md"

    py_path = HUB_ROOT / test_py
    md_path = HUB_ROOT / test_md

    for p in (py_path, md_path):
        if p.exists():
            p.unlink()

    tasks = [
        {
            "agent": "dnk_dev_fullstack",
            "action": "scaffold_api",
            "payload": {"spec": f"Please create {test_py} with FastAPI route"},
        },
        {
            "agent": "herich_librarian",
            "action": "scaffold_docs",
            "payload": {"description": f"Generate documentation at {test_md} per standard"},
        },
    ]

    try:
        res = swarm_coordinator.dispatch_parallel(tasks)
        assert res["status"] == "parallel_batch_completed"
        assert py_path.exists(), "Auto-extracted Python file was not scaffolded!"
        assert md_path.exists(), "Auto-extracted Markdown doc was not scaffolded!"
    finally:
        for p in (py_path, md_path):
            if p.exists():
                p.unlink()

