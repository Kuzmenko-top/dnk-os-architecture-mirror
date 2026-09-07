# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_github_mcp_fast_path.py"
# purpose: "Comprehensive test suite for GitHub MCP & CI/CD Fast-Path, Pre-PR Quality Gate, and Sentinel Telemetry."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.orchestrator.github_fast_path import (
    fast_create_or_update_pr,
    get_github_auth_token,
    make_github_api_request,
    resolve_repo_slug,
    verify_evidence_ready,
)
from core.orchestrator.session_sentinel import (
    AnomalyCategory,
    AnomalySeverity,
    SessionSentinel,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_get_github_auth_token_env():
    with patch.dict(os.environ, {"GH_TOKEN": "test_gh_token_123"}, clear=False):
        assert get_github_auth_token() == "test_gh_token_123"

    with patch.dict(os.environ, {"GH_TOKEN": "", "GITHUB_TOKEN": "test_github_token_456"}, clear=False):
        assert get_github_auth_token() == "test_github_token_456"


def test_resolve_repo_slug():
    with patch.dict(os.environ, {"GITHUB_REPOSITORY": "CustomOrg/CustomRepo"}, clear=False):
        assert resolve_repo_slug() == "CustomOrg/CustomRepo"

    # Default fallback
    with patch.dict(os.environ, {"GITHUB_REPOSITORY": ""}, clear=False):
        slug = resolve_repo_slug()
        assert "/" in slug


def test_verify_evidence_ready_missing():
    # A non-existent task ID
    ready, msg, data = verify_evidence_ready("non_existent_task_99999")
    assert not ready
    assert "not found" in msg


def test_verify_evidence_ready_with_mock(tmp_path):
    audit_dir = tmp_path / "docs" / "audit"
    audit_dir.mkdir(parents=True)
    ev_file = audit_dir / "task-test-01-evidence.json"
    ev_file.write_text(json.dumps({
        "task_id": "task-test-01",
        "status": "Completed",
        "title": "Test Task",
        "quality_gate": {"all_passed": True}
    }))

    with patch("core.orchestrator.github_fast_path.REPO_ROOT", tmp_path):
        ready, msg, data = verify_evidence_ready("task-test-01")
        assert ready
        assert "Verified evidence found" in msg


def test_fast_create_or_update_pr_blocks_without_evidence():
    res = fast_create_or_update_pr(
        task_id="unverified_task_123",
        title="Unverified PR",
        summary="Testing unverified block",
        branch="feature/unverified",
        enforce_evidence_gate=True,
    )
    assert res.get("status") == "blocked"
    assert "Pre-PR Quality Gate Failed" in res.get("error", "")


def test_fast_create_or_update_pr_creates_new(monkeypatch, tmp_path):
    # Mock token and requests
    monkeypatch.setattr("core.orchestrator.github_fast_path.get_github_auth_token", lambda: "mock_tok")
    monkeypatch.setattr("core.orchestrator.github_fast_path.resolve_repo_slug", lambda: "Owner/Repo")
    monkeypatch.setattr(
        "core.orchestrator.github_fast_path.fast_get_pull_request",
        lambda head, repo_slug=None, token=None: None,
    )

    mock_create_res = {
        "html_url": "https://github.com/Owner/Repo/pull/42",
        "number": 42,
        "title": "feat(test): test title",
    }
    monkeypatch.setattr(
        "core.orchestrator.github_fast_path.make_github_api_request",
        lambda endpoint, method, data, repo_slug, token: mock_create_res,
    )

    res = fast_create_or_update_pr(
        task_id="task-042",
        title="feat(test): test title",
        summary="Fast-path PR creation test",
        branch="feature/fast-pr",
        enforce_evidence_gate=False,
    )
    assert res.get("status") == "created"
    assert res.get("pr_number") == 42
    assert res.get("pr_url") == "https://github.com/Owner/Repo/pull/42"


def test_fast_create_or_update_pr_updates_existing(monkeypatch):
    monkeypatch.setattr("core.orchestrator.github_fast_path.get_github_auth_token", lambda: "mock_tok")
    monkeypatch.setattr("core.orchestrator.github_fast_path.resolve_repo_slug", lambda: "Owner/Repo")
    monkeypatch.setattr(
        "core.orchestrator.github_fast_path.fast_get_pull_request",
        lambda head, repo_slug=None, token=None: {
            "html_url": "https://github.com/Owner/Repo/pull/10",
            "number": 10,
            "title": "feat(old): old title",
        },
    )

    mock_update_res = {
        "html_url": "https://github.com/Owner/Repo/pull/10",
        "number": 10,
        "title": "feat(updated): updated title",
    }
    monkeypatch.setattr(
        "core.orchestrator.github_fast_path.make_github_api_request",
        lambda endpoint, method, data, repo_slug, token: mock_update_res,
    )

    res = fast_create_or_update_pr(
        task_id="task-010",
        title="feat(updated): updated title",
        summary="Updating existing PR",
        branch="feature/fast-pr",
        enforce_evidence_gate=False,
    )
    assert res.get("status") == "updated"
    assert res.get("pr_number") == 10


def test_hermes_pre_tool_hook_blocks_unverified_pr():
    hook_script = REPO_ROOT / "scripts" / "system" / "hermes_pre_tool_hook.py"
    payload = {
        "hook_event_name": "pre_tool_call",
        "session_id": "test_pr_gate_001",
        "tool_name": "terminal",
        "tool_input": {"command": "gh pr create --title 'Test PR' --body 'Test'"},
        "turn_call_count": 1,
    }

    env = os.environ.copy()
    env["DNK_BYPASS_PR_GATE"] = "0"
    env["DNK_BYPASS_COMPLETION_GATE"] = "0"

    proc = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
    )
    res = json.loads(proc.stdout)
    assert res.get("action") == "block"
    assert "Pre-PR Gate" in res.get("message", "")


def test_hermes_pre_tool_hook_blocks_mcp_unverified_pr():
    hook_script = REPO_ROOT / "scripts" / "system" / "hermes_pre_tool_hook.py"
    payload = {
        "hook_event_name": "pre_tool_call",
        "session_id": "test_pr_gate_002",
        "tool_name": "mcp__github__create_pull_request",
        "tool_input": {"title": "Test PR", "body": "Test"},
        "turn_call_count": 1,
    }

    env = os.environ.copy()
    env["DNK_BYPASS_PR_GATE"] = "0"
    env["DNK_BYPASS_COMPLETION_GATE"] = "0"

    proc = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
    )
    res = json.loads(proc.stdout)
    assert res.get("action") == "block"
    assert "Pre-PR Gate" in res.get("message", "")


def test_hermes_pre_tool_hook_allows_pr_with_bypass():
    hook_script = REPO_ROOT / "scripts" / "system" / "hermes_pre_tool_hook.py"
    payload = {
        "hook_event_name": "pre_tool_call",
        "session_id": "test_pr_gate_003",
        "tool_name": "terminal",
        "tool_input": {"command": "gh pr create --title 'Test PR' --body 'Test'"},
        "turn_call_count": 1,
    }

    env = os.environ.copy()
    env["DNK_BYPASS_PR_GATE"] = "1"

    proc = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
    )
    res = json.loads(proc.stdout)
    # Hook should allow tool execution (empty dict or no block)
    assert res.get("action") != "block"


def test_session_sentinel_detects_unverified_pr_violation():
    sentinel = SessionSentinel()
    session_data = {
        "messages": [
            ("1", "user", "Create PR for our changes", None, None, 1.0),
            (
                "2",
                "assistant",
                "Creating PR now",
                None,
                json.dumps([
                    {
                        "function": {
                            "name": "terminal",
                            "arguments": json.dumps({"command": "gh pr create --title 'Feature' --body 'Details'"})
                        }
                    }
                ]),
                2.0
            ),
        ]
    }
    anomalies = sentinel.detect_anomalies(session_data)
    ci_cd_anomalies = [a for a in anomalies if a.category == AnomalyCategory.CI_CD_VIOLATION]
    assert len(ci_cd_anomalies) >= 1
    assert "CI/CD Quality Gate Breach" in ci_cd_anomalies[0].title
