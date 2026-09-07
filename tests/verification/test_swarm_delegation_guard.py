# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_swarm_delegation_guard.py"
# purpose: "Verify Section 8 Swarm Delegation Guard & Anti-Solo Enforcement (Strict Dispatch Law) in hermes_pre_tool_hook.py."
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
    session_id = "test_swarm_guard_session"
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


def test_triage_solo_mode_allows_direct_execution():
    session_id = "test_swarm_guard_session"
    # Step 1: Call dnk_triage_task with lightweight solo task
    res_triage = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "dnk_triage_task",
        "tool_input": {"goal_or_prompt": "Fix typo in README.md"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_triage.get("action") != "block"

    # Step 2: Gerych writes or patches file directly (allowed in SOLO mode)
    res_read = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "read_file",
        "tool_input": {"path": "README.md"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_read.get("action") != "block"


def test_triage_swarm_parallel_blocks_immediate_solo_mutation():
    session_id = "test_swarm_guard_session"
    complex_prompt = """
    ### СЛАЙС 1: Бекенд API
    Create apps/api/routers/canvas_v3_ws.py and core/obsidian/export_canvas.py

    ### СЛАЙС 2: Фронтенд UI
    Create apps/web/components/canvas/ObsidianSyncBar.tsx and apps/web/store/canvasStore.ts

    ### СЛАЙС 3: E2E Валідація
    Run scripts/verify_all.sh and verify canvas integration
    """
    # Step 1: Call triage
    res_triage = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "dnk_triage_task",
        "tool_input": {"goal_or_prompt": complex_prompt},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_triage.get("action") != "block"

    # Step 2: Gerych attempts immediate direct file mutation solo
    res_mutation = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "write_file",
        "tool_input": {"path": "core/obsidian/export_canvas.py", "content": "# test"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_mutation.get("action") == "block"
    assert "SWARM_PARALLEL" in res_mutation.get("message", "")
    assert "STRICT DISPATCH LAW" in res_mutation.get("message", "")


def test_triage_swarm_parallel_blocks_solo_read_drift():
    session_id = "test_swarm_guard_session"
    complex_prompt = """
    ### СЛАЙС 1: Бекенд API
    Create apps/api/routers/canvas_v3_ws.py and core/obsidian/export_canvas.py

    ### СЛАЙС 2: Фронтенд UI
    Create apps/web/components/canvas/ObsidianSyncBar.tsx and apps/web/store/canvasStore.ts

    ### СЛАЙС 3: E2E Валідація
    Run scripts/verify_all.sh and verify canvas integration
    """
    # Step 1: Call triage
    run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "dnk_triage_task",
        "tool_input": {"goal_or_prompt": complex_prompt},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })

    # Allowed reads (<=3)
    for i in range(3):
        res = run_hook({
            "hook_event_name": "pre_tool_call",
            "tool_name": "read_file",
            "tool_input": {"path": f"file_{i}.txt"},
            "session_id": session_id,
            "cwd": str(HUB_ROOT),
        })
        assert res.get("action") != "block", f"Read {i+1} should have been allowed"

    # 4th read call exceeds threshold without dispatching swarm -> BLOCK
    res_4th = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "read_file",
        "tool_input": {"path": "file_4.txt"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_4th.get("action") == "block"
    assert "consecutive solo actions" in res_4th.get("message", "") or "consecutive solo exploratory actions" in res_4th.get("message", "")
    assert "dnk_swarm_parallel" in res_4th.get("message", "")


def test_swarm_dispatch_clears_guard():
    session_id = "test_swarm_guard_session"
    complex_prompt = """
    ### СЛАЙС 1: Бекенд API
    Create apps/api/routers/canvas_v3_ws.py

    ### СЛАЙС 2: Фронтенд UI
    Create apps/web/components/canvas/ObsidianSyncBar.tsx
    """
    # Step 1: Triage
    run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "dnk_triage_task",
        "tool_input": {"goal_or_prompt": complex_prompt},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })

    # Step 2: Dispatch swarm parallel
    res_dispatch = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "dnk_swarm_parallel",
        "tool_input": {"tasks_json": json.dumps([{"agent": "dnk_dev_fullstack", "action": "build"}])},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_dispatch.get("action") != "block"

    # Step 3: Now subsequent verification or follow-up mutation is unblocked
    res_followup = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "write_file",
        "tool_input": {"path": "docs/evidence/test_report.md", "content": "# Report"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_followup.get("action") != "block"


def test_bypass_swarm_env_variable():
    session_id = "test_swarm_guard_session"
    complex_prompt = """
    ### СЛАЙС 1: Бекенд API
    Create apps/api/routers/canvas_v3_ws.py

    ### СЛАЙС 2: Фронтенд UI
    Create apps/web/components/canvas/ObsidianSyncBar.tsx
    """
    # Step 1: Triage
    run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "dnk_triage_task",
        "tool_input": {"goal_or_prompt": complex_prompt},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })

    # Step 2: Mutation with DNK_BYPASS_SWARM=1
    res_bypassed = run_hook(
        {
            "hook_event_name": "pre_tool_call",
            "tool_name": "write_file",
            "tool_input": {"path": "core/solo_override.py", "content": "# Solo override"},
            "session_id": session_id,
            "cwd": str(HUB_ROOT),
        },
        env_override={"DNK_BYPASS_SWARM": "1"}
    )
    assert res_bypassed.get("action") != "block"
