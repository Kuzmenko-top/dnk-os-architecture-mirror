# --- DNK-MRH-HEADER ---
# mrh_id: "core/playbooks/tests/test_playbooks.py"
# purpose: "Unit tests verifying Playbook scripts execution."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import pytest
from core.playbooks.scripts.sanitize_context_bloat import sanitize_text
from core.playbooks.scripts.enforce_relative_paths import audit_relative_paths
from core.playbooks.scripts.run_system_health_audit import check_system_health


def test_sanitize_context_bloat():
    text = "line\n" * 100
    cleaned = sanitize_text(text, max_lines=10)
    assert "TRUNCATED" in cleaned
    assert len(cleaned.splitlines()) < 100


def test_enforce_relative_paths():
    violations = audit_relative_paths("DNK OS")
    assert violations == 0


def test_check_system_health():
    health = check_system_health()
    assert health is True


def test_fastmcp_gatekeeper():
    from core.playbooks.scripts.fastmcp_bridge_gatekeeper import FastMCPBridgeGatekeeper
    gk = FastMCPBridgeGatekeeper()
    res = gk.run_gatekeeper_check()
    assert res["status"] == "success"
    assert res["active_playbooks_count"] >= 1

