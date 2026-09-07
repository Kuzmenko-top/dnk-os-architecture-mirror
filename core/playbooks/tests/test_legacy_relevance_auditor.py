# --- DNK-MRH-HEADER ---
# mrh_id: "core/playbooks/tests/test_legacy_relevance_auditor.py"
# purpose: "Unit tests for LegacyRelevanceAuditor calculating Relevance Score and promoting gems."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-07"
# --- END DNK-MRH-HEADER ---

import os
import tempfile
import pytest
from core.playbooks.scripts.legacy_relevance_auditor import LegacyRelevanceAuditor


def test_legacy_relevance_auditor_scan():
    with tempfile.TemporaryDirectory() as tmp_legacy, tempfile.TemporaryDirectory() as tmp_mvp:
        # Create dummy legacy gem
        gem_file = os.path.join(tmp_legacy, "gem_orchestrator.py")
        with open(gem_file, "w", encoding="utf-8") as f:
            f.write("""# --- DNK-MRH-HEADER ---
# mrh_id: "gem_orchestrator.py"
# --- END DNK-MRH-HEADER ---
# FastMCP and TaskForest pattern
def run():
    pass
""")

        auditor = LegacyRelevanceAuditor(target_workspace=tmp_mvp)
        res = auditor.audit_directory(tmp_legacy)

        assert res["status"] == "success"
        assert res["total_files_audited"] == 1
        assert res["promoted_gems_count"] == 1
