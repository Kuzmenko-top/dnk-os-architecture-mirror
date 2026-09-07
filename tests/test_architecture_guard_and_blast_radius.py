#!/usr/bin/env python3
# --- DNK-MRH-HEADER ---
# mrh_id: "tests_test_architecture_guard_and_blast_radius"
# purpose: "Verify deterministic blast radius analysis and architecture cycle guard"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import subprocess
import sys
from pathlib import Path

from scripts.system.architecture_and_cycle_guard import (
    check_layer_isolation,
    check_project_view_modularity,
    check_provider_import_cycles,
    check_updater_import_cycles,
    find_import_cycles_in_dir,
    run_all_checks,
)
from scripts.system.blast_radius_analyzer import analyze_blast_radius


def test_architecture_guard_invariants():
    """Ensure all core architectural guards report 100% compliance."""
    iso_ok, iso_errs = check_layer_isolation()
    assert iso_ok, f"Layer isolation failed: {iso_errs}"

    prov_ok, prov_errs = check_provider_import_cycles()
    assert prov_ok, f"Provider cycles detected: {prov_errs}"

    upd_ok, upd_errs = check_updater_import_cycles()
    assert upd_ok, f"Updater cycles detected: {upd_errs}"

    pv_ok, pv_errs = check_project_view_modularity()
    assert pv_ok, f"ProjectView modularity failed: {pv_errs}"

    assert run_all_checks() is True


def test_cycle_detector_catches_synthetic_cycles(tmp_path: Path):
    """Verify that find_import_cycles_in_dir accurately identifies cycles."""
    # Create a synthetic cycle: a -> b -> c -> a
    (tmp_path / "a.ts").write_text("import { b } from './b';", encoding="utf-8")
    (tmp_path / "b.ts").write_text("import { c } from './c';", encoding="utf-8")
    (tmp_path / "c.ts").write_text("import { a } from './a';", encoding="utf-8")
    (tmp_path / "d.ts").write_text("import { b } from './b';", encoding="utf-8")

    cycles = find_import_cycles_in_dir(tmp_path)
    assert len(cycles) > 0
    cycle_nodes = set(cycles[0])
    assert {"a", "b", "c"}.issubset(cycle_nodes)


def test_blast_radius_analysis_web():
    """Verify blast radius analyzer identifies web impact and triggers typecheck."""
    report = analyze_blast_radius(["apps/web/components/ProjectList.tsx"])
    assert "frontend_web" in report.affected_domains
    assert report.requires_frontend_typecheck is True
    assert "tests/test_web_layer_isolation.py" in report.required_pytests


def test_blast_radius_analysis_visual_shell():
    """Verify blast radius analyzer identifies visual_shell impact and project-view tests."""
    report = analyze_blast_radius(["visual_shell/open_design/apps/web/src/components/ProjectView.tsx"])
    assert "visual_shell" in report.affected_domains
    assert report.requires_architecture_cycle_guard is True
    assert "tests/test_project_view_decomposition.py" in report.required_pytests
    assert "tests/components/ProjectView.questionFormKey.test.ts" in report.required_vitests


def test_blast_radius_analysis_low_risk_docs():
    """Verify docs changes have LOW risk and no heavy test requirements."""
    report = analyze_blast_radius(["docs/notes/test_note.md"])
    assert report.risk_level == "LOW"
    assert report.requires_frontend_typecheck is False
    assert report.requires_architecture_cycle_guard is False
