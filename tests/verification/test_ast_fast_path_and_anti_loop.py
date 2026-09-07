# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_ast_fast_path_and_anti_loop.py"
# purpose: "Unit tests for AST Fast-Path, Anti-Search-Loop, Unverified Churn, and MASE Hard Budget Guards"
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
from typing import Optional, Dict, Any
import pytest

from core.orchestrator.session_sentinel import (
    SessionSentinel,
    AnomalyCategory,
    AnomalySeverity
)

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = HUB_ROOT / "scripts" / "system" / "hermes_pre_tool_hook.py"


def run_hook(payload: dict) -> Dict[str, Any]:
    """Helper to run hermes_pre_tool_hook.py via subprocess and capture JSON output."""
    payload.setdefault("hook_event_name", "pre_tool_call")
    res = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(HUB_ROOT),
    )
    stdout = res.stdout.strip()
    if stdout:
        try:
            return json.loads(stdout)
        except Exception:
            pass
    return {}


@pytest.fixture(autouse=True)
def cleanup_trackers():
    """Ensure test session tracker files are removed before and after each test."""
    test_sessions = [
        "test-ast-search-01",
        "test-search-loop-02",
        "test-churn-loop-03",
        "test-mase-hard-stop-04",
    ]
    for s in test_sessions:
        p = Path(f"/tmp/hermes_loop_tracker_{s}.json")
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
    yield
    for s in test_sessions:
        p = Path(f"/tmp/hermes_loop_tracker_{s}.json")
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass


class TestASTFastPathAndAntiLoop:

    def test_search_files_symbol_definition_blocked_with_ast_fast_path(self):
        """Invariant 16: Symbol definition regex in search_files is blocked with dnk_resolve_symbol guidance."""
        session_id = "test-ast-search-01"

        payload = {
            "session_id": session_id,
            "tool_name": "search_files",
            "tool_input": {
                "pattern": "class TaskForestNode",
                "target": "content"
            }
        }
        res = run_hook(payload)
        assert res.get("action") == "block"
        assert "AST Fast-Path Guard" in res.get("message", "")
        assert "TaskForestNode" in res.get("message", "")
        assert "dnk_resolve_symbol" in res.get("message", "")

        # Test function definition regex
        payload2 = {
            "session_id": session_id,
            "tool_name": "search_files",
            "tool_input": {
                "pattern": "def sync_canvas_nodes",
                "target": "content"
            }
        }
        res2 = run_hook(payload2)
        assert res2.get("action") == "block"
        assert "sync_canvas_nodes" in res2.get("message", "")

        # Test typescript interface
        payload3 = {
            "session_id": session_id,
            "tool_name": "search_files",
            "tool_input": {
                "pattern": "export interface CanvasStoreState",
                "target": "content"
            }
        }
        res3 = run_hook(payload3)
        assert res3.get("action") == "block"
        assert "CanvasStoreState" in res3.get("message", "")

    def test_search_files_consecutive_loop_blocked(self):
        """Consecutive search_files calls >= 4 without mutation are blocked by Anti-Search-Loop Guard."""
        session_id = "test-search-loop-02"

        for i in range(3):
            payload = {
                "session_id": session_id,
                "tool_name": "search_files",
                "tool_input": {
                    "pattern": f"some_generic_token_{i}",
                    "target": "files"
                }
            }
            res = run_hook(payload)
            assert res.get("action") is None

        # 4th consecutive search should block
        payload_4 = {
            "session_id": session_id,
            "tool_name": "search_files",
            "tool_input": {
                "pattern": "another_token_4",
                "target": "files"
            }
        }
        res_4 = run_hook(payload_4)
        assert res_4.get("action") == "block"
        assert "Anti-Search-Loop Guard" in res_4.get("message", "")

    def test_unverified_rewrite_churn_blocked(self):
        """Modifying the same file consecutively without verification triggers Circuit Breaker."""
        session_id = "test-churn-loop-03"
        target_file = "apps/web/store/testStore.ts"

        for i in range(2):
            payload = {
                "session_id": session_id,
                "tool_name": "patch",
                "tool_input": {
                    "path": target_file,
                    "old_string": f"val_{i}",
                    "new_string": f"val_{i+1}"
                }
            }
            res = run_hook(payload)
            assert res.get("action") is None

        # 3rd modification to the same file without verification must block
        payload_3 = {
            "session_id": session_id,
            "tool_name": "patch",
            "tool_input": {
                "path": target_file,
                "old_string": "val_2",
                "new_string": "val_3"
            }
        }
        res_3 = run_hook(payload_3)
        assert res_3.get("action") == "block"
        assert "without testing" in res_3.get("message", "") or "Unverified Rewrite Churn" in res_3.get("message", "")

        # Running test verification resets the churn tracker
        verify_payload = {
            "session_id": session_id,
            "tool_name": "terminal",
            "tool_input": {
                "command": "./.venv/bin/pytest tests/core/test_dummy.py"
            }
        }
        res_v = run_hook(verify_payload)
        assert res_v.get("action") is None

        # Next patch on target_file is now allowed again
        res_after = run_hook(payload_3)
        assert res_after.get("action") is None

    def test_mase_hard_budget_stop_at_30_calls(self):
        """At turn count >= 30, non-verification tools are blocked while verification is allowed."""
        session_id = "test-mase-hard-stop-04"

        # Simulating non-verification call at turn 31
        non_verify_payload = {
            "session_id": session_id,
            "turn_call_count": 31,
            "tool_name": "patch",
            "tool_input": {
                "path": "core/some_file.py",
                "old_string": "a",
                "new_string": "b"
            }
        }
        res = run_hook(non_verify_payload)
        assert res.get("action") == "block"
        assert "MASE Hard Budget Guard" in res.get("message", "")

        # Verification command via terminal at turn 31 is permitted
        verify_payload = {
            "session_id": session_id,
            "turn_call_count": 31,
            "tool_name": "terminal",
            "tool_input": {
                "command": "bash scripts/verify_all.sh"
            }
        }
        res_v = run_hook(verify_payload)
        assert res_v.get("action") is None


class TestSessionSentinelASTAndLoopDetection:

    def test_sentinel_detects_missing_ast_fast_path(self):
        """Sentinel flags TOOL_LOOP when search_files >= 3 is used without dnk_resolve_symbol."""
        sentinel = SessionSentinel()

        session_data = {
            "session_id": "test-sentinel-ast-01",
            "messages": [
                (1, "user", "Find classes", None, None, 100.0),
                (2, "assistant", None, None, json.dumps([{"function": {"name": "search_files", "arguments": '{"pattern": "NodeTask"}'}}]), 101.0),
                (3, "assistant", None, None, json.dumps([{"function": {"name": "search_files", "arguments": '{"pattern": "CanvasNode"}'}}]), 102.0),
                (4, "assistant", None, None, json.dumps([{"function": {"name": "search_files", "arguments": '{"pattern": "TaskDNA"}'}}]), 103.0),
            ]
        }

        anomalies = sentinel.detect_anomalies(session_data)
        ast_anomalies = [
            a for a in anomalies
            if a.category == AnomalyCategory.TOOL_LOOP and "Missing AST Fast-Path" in a.title
        ]
        assert len(ast_anomalies) == 1
        assert "dnk_resolve_symbol" in ast_anomalies[0].suggested_fix_summary

    def test_sentinel_does_not_flag_ast_anomaly_when_symbol_resolved(self):
        """Sentinel does not flag AST anomaly if dnk_resolve_symbol was invoked."""
        sentinel = SessionSentinel()

        session_data = {
            "session_id": "test-sentinel-ast-02",
            "messages": [
                (1, "user", "Find classes", None, None, 100.0),
                (2, "assistant", None, None, json.dumps([{"function": {"name": "dnk_resolve_symbol", "arguments": '{"symbol": "NodeTask"}'}}]), 101.0),
                (3, "assistant", None, None, json.dumps([{"function": {"name": "search_files", "arguments": '{"pattern": "NodeTask"}'}}]), 102.0),
                (4, "assistant", None, None, json.dumps([{"function": {"name": "search_files", "arguments": '{"pattern": "CanvasNode"}'}}]), 103.0),
                (5, "assistant", None, None, json.dumps([{"function": {"name": "search_files", "arguments": '{"pattern": "TaskDNA"}'}}]), 104.0),
            ]
        }

        anomalies = sentinel.detect_anomalies(session_data)
        ast_anomalies = [
            a for a in anomalies
            if a.category == AnomalyCategory.TOOL_LOOP and "Missing AST Fast-Path" in a.title
        ]
        assert len(ast_anomalies) == 0

    def test_sentinel_detects_unverified_file_churn(self):
        """Sentinel flags TOOL_LOOP when the same file is modified >= 3 times without verification."""
        sentinel = SessionSentinel()

        session_data = {
            "session_id": "test-sentinel-churn-03",
            "messages": [
                (1, "user", "Refactor store", None, None, 100.0),
                (2, "assistant", None, None, json.dumps([{"function": {"name": "patch", "arguments": json.dumps({"path": "apps/web/store/nodeTasksStore.ts"})}}]), 101.0),
                (3, "assistant", None, None, json.dumps([{"function": {"name": "patch", "arguments": json.dumps({"path": "apps/web/store/nodeTasksStore.ts"})}}]), 102.0),
                (4, "assistant", None, None, json.dumps([{"function": {"name": "patch", "arguments": json.dumps({"path": "apps/web/store/nodeTasksStore.ts"})}}]), 103.0),
            ]
        }

        anomalies = sentinel.detect_anomalies(session_data)
        churn_anomalies = [
            a for a in anomalies
            if a.category == AnomalyCategory.TOOL_LOOP and "Unverified File Modification Churn" in a.title
        ]
        assert len(churn_anomalies) == 1
        assert "nodeTasksStore.ts" in churn_anomalies[0].title
