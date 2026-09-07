# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_sentinel_circuit_breaker.py"
# purpose: "Unit tests verifying Sentinel Circuit Breaker and self-healing bypass in hermes_pre_tool_hook.py."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import json
import os
import subprocess
import sys
import time
from pathlib import Path
import pytest

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = HUB_ROOT / "scripts" / "system" / "hermes_pre_tool_hook.py"
ALERTS_FILE = HUB_ROOT / "data" / "sentinel_alerts.json"


def run_hook(event: dict, env_override: dict | None = None) -> dict:
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


@pytest.fixture
def setup_sentinel_alert():
    ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if ALERTS_FILE.exists():
        backup = ALERTS_FILE.read_text(encoding="utf-8")

    alert_payload = {
        "timestamp": time.time(),
        "alerts": [
            {
                "category": "TOOL_LOOP",
                "severity": "HIGH",
                "title": "Repetitive Tool Execution Loop",
                "description": "Agent repeated identical read_file 5 times",
                "suggested_fix": "Use dnk_query_error_solutions or proceed with code edits directly"
            }
        ]
    }
    ALERTS_FILE.write_text(json.dumps(alert_payload), encoding="utf-8")

    yield

    if backup is not None:
        ALERTS_FILE.write_text(backup, encoding="utf-8")
    else:
        if ALERTS_FILE.exists():
            ALERTS_FILE.unlink()


def test_sentinel_circuit_breaker_blocks_normal_tool(setup_sentinel_alert):
    session_id = "test_sentinel_cb_session"
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": "echo test_normal"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") == "block"
    assert "Sentinel Circuit Breaker" in res.get("message", "")
    assert "TOOL_LOOP" in res.get("message", "")


def test_sentinel_circuit_breaker_allows_self_healing_tool(setup_sentinel_alert):
    session_id = "test_sentinel_cb_session"
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "dnk_query_error_solutions",
        "tool_input": {"error_text": "TypeError in test"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") != "block"


def test_sentinel_circuit_breaker_allows_verification_command(setup_sentinel_alert):
    session_id = "test_sentinel_cb_session"
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": "bash scripts/verify_all.sh"},
        "session_id": session_id,
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") != "block"


def test_sentinel_circuit_breaker_bypass_env(setup_sentinel_alert):
    session_id = "test_sentinel_cb_session"
    res = run_hook(
        {
            "hook_event_name": "pre_tool_call",
            "tool_name": "terminal",
            "tool_input": {"command": "echo test_bypassed"},
            "session_id": session_id,
            "cwd": str(HUB_ROOT),
        },
        env_override={"DNK_BYPASS_SENTINEL": "1"}
    )
    assert res.get("action") != "block"


def test_gerych_sh_syntax_check():
    proc = subprocess.run(
        ["bash", "-n", "scripts/system/gerych.sh"],
        capture_output=True,
        text=True,
        cwd=str(HUB_ROOT)
    )
    assert proc.returncode == 0, f"Syntax error in gerych.sh: {proc.stderr}"
