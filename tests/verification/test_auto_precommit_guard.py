# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_auto_precommit_guard.py"
# purpose: "Automated test suite verifying the AutoPreCommitGuard quality execution, checks aggregation, and timing."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import sys
from pathlib import Path

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

from scripts.system.auto_precommit_guard import (
    auto_guard,
    GuardCheckResult,
)


from unittest.mock import patch, MagicMock


def test_auto_precommit_guard_run():
    with patch("subprocess.run") as mock_run:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "5902 files compiled successfully"
        mock_proc.stderr = ""
        mock_run.return_value = mock_proc

        res = auto_guard.run_guard()
        assert isinstance(res, GuardCheckResult)
        assert res.passed is True
        assert res.total_checks >= 4
        assert res.passed_checks == res.total_checks
        assert "preflight_sanitizer" in res.check_results
        assert "fast_syntax_check" in res.check_results
        assert "path_hygiene" in res.check_results
        assert "regression_tests" in res.check_results
        assert len(res.errors) == 0
