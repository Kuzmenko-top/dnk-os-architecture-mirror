# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_obsidian_vault_path_hygiene.py"
# purpose: "Verify Obsidian Vault path sanitization, docs/notes relative symlink, and vault: virtual prefix protocol."
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
import uuid
from pathlib import Path
import pytest

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = HUB_ROOT / "scripts" / "system" / "hermes_pre_tool_hook.py"


def run_hook(event: dict) -> dict:
    proc = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(event),
        text=True,
        capture_output=True,
        cwd=str(HUB_ROOT),
    )
    raw = proc.stdout.strip()
    return json.loads(raw) if raw else {}


def test_docs_notes_symlink_exists_and_resolves():
    notes_link = HUB_ROOT / "docs" / "notes"
    assert notes_link.exists() or notes_link.is_symlink()
    resolved = notes_link.resolve()
    assert "DNK_HUB My Notes" in str(resolved) or "docs/notes" in str(resolved) or notes_link.is_dir()


def test_hook_sanitizes_vault_virtual_prefix():
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "read_file",
        "tool_input": {"path": "vault:000 DNK HUB Index.md"},
        "session_id": f"test_vault_hygiene_{uuid.uuid4().hex[:8]}",
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") == "modify"
    new_path = res.get("args", {}).get("path", "")
    assert new_path == "docs/notes/000 DNK HUB Index.md"


def test_hook_sanitizes_absolute_obsidian_path_leak():
    abs_path = f"{Path.home()}/Documents/DNK_HUB My Notes/DNK_HUB My Notes/012 Agentic Habits.md"
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "read_file",
        "tool_input": {"path": abs_path},
        "session_id": f"test_vault_hygiene_{uuid.uuid4().hex[:8]}",
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") == "modify"
    new_path = res.get("args", {}).get("path", "")
    assert new_path == "docs/notes/012 Agentic Habits.md"
    assert str(Path.home()) not in new_path


def test_hook_sanitizes_terminal_command_obsidian_path():
    abs_cmd = f'cat "{Path.home()}/Documents/DNK_HUB My Notes/DNK_HUB My Notes/000 DNK HUB Index.md"'
    res = run_hook({
        "hook_event_name": "pre_tool_call",
        "tool_name": "terminal",
        "tool_input": {"command": abs_cmd},
        "session_id": "test_vault_hygiene_3",
        "cwd": str(HUB_ROOT),
    })
    assert res.get("action") == "modify"
    new_cmd = res.get("args", {}).get("command", "")
    assert "./docs/notes/000 DNK HUB Index.md" in new_cmd
    assert str(Path.home()) not in new_cmd


def test_validate_vault_path_with_vault_prefix():
    from core.obsidian.export_canvas import validate_vault_path, get_canonical_vault_root
    
    canonical_root = get_canonical_vault_root()
    validated = validate_vault_path("vault:TaskForest")
    assert validated == (canonical_root / "TaskForest").resolve()
