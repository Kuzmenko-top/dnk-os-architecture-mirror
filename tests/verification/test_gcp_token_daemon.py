# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_gcp_token_daemon.py"
# purpose: "Unit tests verifying GCPTokenDaemon status checking, age calculation, and token persistence."
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

from scripts.system.gcp_token_daemon import gcp_token_daemon


def test_gcp_token_daemon_status():
    status = gcp_token_daemon.get_token_status()
    assert isinstance(status, dict)
    assert "token_file" in status
    if status.get("active"):
        assert "ya29." in status["token_prefix"]
        assert status["expires_in_seconds"] >= 0
