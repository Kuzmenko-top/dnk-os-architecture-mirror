# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_completion_gate_hook.py"
# purpose: "Unit tests verifying Tier 2 CompletionGate Commit Guard and Fast-Fail Command Sanitization in hermes_pre_tool_hook.py."
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
    session_id = "test_completion_gate_session"
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


def test_completion_gate_blocks_commit_after_file_mutation():
    session_id = "test_completion_gate_session"
    # Step 1: Write/patch a file
    res_mutate = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "write_file",
        "tool_input": {"path": "apps/sample_app.py", "content": "# test"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_mutate.get("action") != "block"

    # Step 2: Attempt git commit without running tests -> must be blocked
    res_commit = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": "git commit -m 'feat: unverified change'"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_commit.get("action") == "block"
    assert "CompletionGate" in res_commit.get("message", "")
    assert "Anti-Phantom-Done" in res_commit.get("message", "")


def test_completion_gate_allows_commit_after_verification():
    session_id = "test_completion_gate_session"
    # Step 1: Write a file
    run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "write_file",
        "tool_input": {"path": "apps/sample_app.py", "content": "# test"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })

    # Step 2: Run verification (e.g. pytest)
    res_verify = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": "pytest tests/verification/"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_verify.get("action") != "block"

    # Step 3: Now git commit is permitted
    res_commit = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": "git commit -m 'feat: verified change'"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_commit.get("action") != "block"


def test_completion_gate_bypass_env_var():
    session_id = "test_completion_gate_session"
    # Step 1: Write a file
    run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "write_file",
        "tool_input": {"path": "apps/sample_app.py", "content": "# test"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })

    # Step 2: Commit with DNK_BYPASS_COMPLETION_GATE=1
    res_commit = run_hook(
        {
            "hook_event_name": "pre_tool_call",
            "tool_name": "terminal",
            "tool_input": {"command": "git commit -m 'wip emergency'"},
            "session_id": session_id,
            "cwd": str(HUB_ROOT),
        },
        env_override={"DNK_BYPASS_COMPLETION_GATE": "1"},
    )
    assert res_commit.get("action") != "block"


def test_completion_gate_allows_commit_without_mutations():
    session_id = "test_completion_gate_session"
    # Direct commit without preceding mutations in this session
    res_commit = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": "git commit -m 'chore: metadata sync'"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res_commit.get("action") != "block"


def test_fast_fail_sanitizer_gitleaks():
    session_id = "test_completion_gate_session"
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": "gitleaks detect"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") == "modify"
    sanitized_cmd = res["args"]["command"]
    assert '--log-opts="-n 5"' in sanitized_cmd
    assert "--redact" in sanitized_cmd


def test_fast_fail_sanitizer_act():
    session_id = "test_completion_gate_session"
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": "act --dry-run"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") == "modify"
    sanitized_cmd = res["args"]["command"]
    assert "actionlint" in sanitized_cmd


def test_python_inline_command_auto_bridge():
    session_id = "test_completion_gate_session"
    raw_cmd = 'python3 -c "import sys; print(1)" && pytest apps/api/tests/test_tracing.py -v'
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": raw_cmd},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") == "modify"
    sanitized = res["args"]["command"]
    assert "./.venv/bin/python -c" in sanitized or ".venv/bin/python -c" in sanitized
    assert "./.venv/bin/pytest" in sanitized or ".venv/bin/pytest" in sanitized
    assert "python3 -c" not in sanitized


def test_fast_fail_sanitizer_server_hang_watchdog():
    session_id = "test_completion_gate_session"
    raw_cmd = 'python3 -c "import uvicorn; uvicorn.Server(cfg).run()"'
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": raw_cmd},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") == "modify"
    sanitized = res["args"]["command"]

def test_tool_alias_resolution_in_hook():
    session_id = "test_completion_gate_session"
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "sh",
        "tool_input": {"command": "echo test"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") == "modify"
    assert res.get("tool_name") == "terminal"
