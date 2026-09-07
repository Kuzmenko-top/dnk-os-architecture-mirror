# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_read_loop_guard.py"
# purpose: "Unit tests verifying Anti-Read-Loop Tax Guard and unmutated re-read blocking in hermes_pre_tool_hook.py."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import json
import os
import subprocess
import sys
from pathlib import Path
import pytest

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = HUB_ROOT / "scripts" / "system" / "hermes_pre_tool_hook.py"


def run_hook(event: dict, env_override: dict = None) -> dict:
    env = os.environ.copy()
    if env_override:
        env.update(env_override)
    proc = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        cwd=str(HUB_ROOT),
        env=env,
    )
    raw = proc.stdout.strip()
    return json.loads(raw) if raw else {}


@pytest.fixture(autouse=True)
def cleanup_tracker():
    session_id = "test_read_loop_session"
    tracker_file = Path(f"/tmp/hermes_loop_tracker_{session_id}.json")
    if tracker_file.exists():
        try:
            tracker_file.unlink()
        except Exception:
            pass
    yield
    if tracker_file.exists():
        try:
            tracker_file.unlink()
        except Exception:
            pass


def test_read_loop_blocks_unmutated_repeated_reads(tmp_path):
    session_id = "test_read_loop_session"
    test_file = tmp_path / "sample_module.py"
    test_file.write_text("print('hello')\n")
    rel_path = str(test_file)

    # 1st read: allowed
    res1 = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "read_file",
        "tool_input": {"path": rel_path},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res1.get("action") != "block"

    # 2nd read: allowed
    res2 = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "read_file",
        "tool_input": {"path": rel_path},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res2.get("action") != "block"

    # 3rd read on unmutated file: must be blocked!
    res3 = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "read_file",
        "tool_input": {"path": rel_path},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res3.get("action") == "block"
    assert "Anti-Read-Loop Tax Guard" in res3.get("message", "")


def test_read_loop_unblocked_after_mutation(tmp_path):
    session_id = "test_read_loop_session"
    test_file = tmp_path / "sample_module.py"
    test_file.write_text("print('hello')\n")
    rel_path = str(test_file)

    # Read twice
    for _ in range(2):
        run_hook({
            "hook_event_name": "pre_tool_call",
            "tool_name": "read_file",
            "tool_input": {"path": rel_path},
            "session_id": session_id,
            "cwd": str(HUB_ROOT),
        })

    # Mutate the file with write_file
    res_mut = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "write_file",
        "tool_input": {"path": rel_path, "content": "print('updated')\n"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_mut.get("action") != "block"

    # Now read again (subsequent read after mutation is permitted)
    res_after = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "read_file",
        "tool_input": {"path": rel_path},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_after.get("action") != "block"
