# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_session_sentinel.py"
# purpose: "Verification test suite for Session Sentinel (Shadow Observer & Self-Healing Loop)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from pathlib import Path
from core.orchestrator.session_sentinel import (
    SessionSentinel,
    AnomalyCategory,
    AnomalySeverity,
    DetectedAnomaly,
    SessionAuditResult,
)
from services.dnk_node_tasks.persistence import NodeTaskPersistenceManager
from services.dnk_node_tasks.models import NodeType, ExecutionStage, NodeStatus


@pytest.fixture
def sentinel(tmp_path):
    return SessionSentinel(agent_name="gerych_builder", hub_root=tmp_path)


def test_anomaly_detection_auth_error(sentinel):
    session_data = {
        "session_id": "test_auth_401",
        "model": "gemini-3.8-flash",
        "started_at": 100.0,
        "ended_at": 110.0,
        "title": "Auth test",
        "messages": [
            (1, "user", "Execute slice 1", None, None, 101.0),
            (2, "tool", "HTTP 401: Expected OAuth 2 access token, login cookie or other valid credential", "model_call", None, 102.0),
        ]
    }
    anomalies = sentinel.detect_anomalies(session_data)
    assert len(anomalies) == 1
    assert anomalies[0].category == AnomalyCategory.AUTH_ERROR
    assert anomalies[0].severity == AnomalySeverity.CRITICAL
    assert "401" in anomalies[0].title


def test_anomaly_detection_model_reasoning_and_tokens(sentinel):
    session_data = {
        "session_id": "test_reasoning_exhaustion",
        "model": "gemini-3.8-flash",
        "started_at": 100.0,
        "ended_at": 115.0,
        "title": "Reasoning test",
        "messages": [
            (1, "user", "Execute slice 1", None, None, 101.0),
            (2, "assistant", "Error: 'NoneType' object has no attribute 'content'", None, None, 102.0),
        ]
    }
    anomalies = sentinel.detect_anomalies(session_data)
    assert len(anomalies) == 1
    assert anomalies[0].category == AnomalyCategory.MODEL_REASONING
    assert anomalies[0].severity == AnomalySeverity.HIGH
    assert "core/hermes_agent/agent/title_generator.py" in anomalies[0].target_files


def test_anomaly_detection_read_loop(sentinel):
    view_args = json.dumps({"AbsolutePath": "core/hermes_agent/agent/title_generator.py"})
    session_data = {
        "session_id": "test_loop",
        "model": "gemini-3.8-flash",
        "started_at": 100.0,
        "ended_at": 120.0,
        "title": "Loop test",
        "messages": [
            (1, "user", "Fix bug", None, None, 101.0),
            (2, "assistant", None, None, json.dumps([{"function": {"name": "view_file", "arguments": view_args}}]), 102.0),
            (3, "assistant", None, None, json.dumps([{"function": {"name": "view_file", "arguments": view_args}}]), 103.0),
            (4, "assistant", None, None, json.dumps([{"function": {"name": "view_file", "arguments": view_args}}]), 104.0),
            (5, "assistant", None, None, json.dumps([{"function": {"name": "view_file", "arguments": view_args}}]), 105.0),
        ]
    }
    anomalies = sentinel.detect_anomalies(session_data)
    loop_anomalies = [a for a in anomalies if a.category == AnomalyCategory.TOOL_LOOP]
    assert len(loop_anomalies) == 1
    assert "Read Loop" in loop_anomalies[0].title


def test_anomaly_detection_path_violation(sentinel):
    bad_prefix = "/User" + "s/kuzmenko.top/file.py"
    bad_args = json.dumps({"CommandLine": f"cat {bad_prefix}"})
    session_data = {
        "session_id": "test_path_violation",
        "model": "gemini-3.8-flash",
        "started_at": 100.0,
        "ended_at": 110.0,
        "title": "Path test",
        "messages": [
            (1, "user", "Run check", None, None, 101.0),
            (2, "assistant", None, None, json.dumps([{"function": {"name": "terminal", "arguments": bad_args}}]), 102.0),
        ]
    }
    anomalies = sentinel.detect_anomalies(session_data)
    path_anomalies = [a for a in anomalies if a.category == AnomalyCategory.PATH_VIOLATION]
    assert len(path_anomalies) == 1
    assert anomalies[0].category == AnomalyCategory.PATH_VIOLATION


def test_anomaly_detection_budget_breach(sentinel):
    tcs = [{"function": {"name": "run_command", "arguments": "{}"}}]
    messages = [(1, "user", "Large job", None, None, 100.0)]
    for i in range(26):
        messages.append((i + 2, "assistant", None, None, json.dumps(tcs), 101.0 + i))

    session_data = {
        "session_id": "test_budget",
        "model": "gemini-3.8-flash",
        "started_at": 100.0,
        "ended_at": 200.0,
        "title": "Budget test",
        "messages": messages
    }
    anomalies = sentinel.detect_anomalies(session_data)
    budget_anomalies = [a for a in anomalies if a.category == AnomalyCategory.BUDGET_BREACH]
    assert len(budget_anomalies) == 1
    assert "26 > 25" in budget_anomalies[0].title


def test_clean_session_has_no_anomalies(sentinel):
    session_data = {
        "session_id": "clean_session",
        "model": "gemini-3.8-flash",
        "started_at": 100.0,
        "ended_at": 120.0,
        "title": "Clean run",
        "messages": [
            (1, "user", "Build feature", None, None, 101.0),
            (2, "assistant", None, None, json.dumps([{"function": {"name": "replace_file_content", "arguments": "{}"}}]), 102.0),
            (3, "tool", "Success: file updated", "replace_file_content", None, 103.0),
            (4, "assistant", None, None, json.dumps([{"function": {"name": "terminal", "arguments": json.dumps({"command": "pytest tests/test_feature.py"})}}]), 104.0),
            (5, "tool", "1 passed in 0.1s", "terminal", None, 105.0),
            (6, "assistant", "Task completed 100% Green!", None, None, 106.0),
        ]
    }
    audit = sentinel.analyze_trajectory(session_data)
    assert len(audit.anomalies) == 0
    assert audit.efficiency_pct == 100.0
    task_file = sentinel.synthesize_self_heal_task_spec(audit)
    assert task_file is None


def test_false_compliance_guard_anomaly_detected(sentinel):
    session_data = {
        "session_id": "false_compliance_session",
        "model": "gemini-3.8-flash",
        "started_at": 100.0,
        "ended_at": 120.0,
        "title": "Fake green run",
        "messages": [
            (1, "user", "Build feature", None, None, 101.0),
            (2, "assistant", None, None, json.dumps([{"function": {"name": "write_file", "arguments": "{}"}}]), 102.0),
            (3, "tool", "Wrote file", "write_file", None, 103.0),
            (4, "assistant", "All done, all tests passed 100% green without error!", None, None, 104.0),
        ]
    }
    anomalies = sentinel.detect_anomalies(session_data)
    false_comp = [a for a in anomalies if a.category == AnomalyCategory.FALSE_COMPLIANCE]
    assert len(false_comp) == 1
    assert "Without Verification" in false_comp[0].title


def test_semantic_error_loop_detected(sentinel):
    session_data = {
        "session_id": "error_loop_session",
        "model": "gemini-3.8-flash",
        "started_at": 100.0,
        "ended_at": 120.0,
        "title": "Error loop run",
        "messages": [
            (1, "user", "Fix error", None, None, 101.0),
            (2, "assistant", None, None, json.dumps([{"function": {"name": "terminal", "arguments": "python script.py"}}]), 102.0),
            (3, "tool", "Traceback: ModuleNotFoundError: No module named 'fake_module'", "terminal", None, 103.0),
            (4, "assistant", None, None, json.dumps([{"function": {"name": "terminal", "arguments": "python script.py"}}]), 104.0),
            (5, "tool", "Traceback: ModuleNotFoundError: No module named 'fake_module'", "terminal", None, 105.0),
        ]
    }
    anomalies = sentinel.detect_anomalies(session_data)
    err_loops = [a for a in anomalies if a.category == AnomalyCategory.ERROR_LOOP]
    assert len(err_loops) >= 1
    assert "ModuleNotFoundError" in err_loops[0].title
    assert "Without Distillation" in err_loops[0].title


def test_atomic_write_mitigation_writer(tmp_path):
    target = tmp_path / "sub" / "audit.json"
    content = json.dumps({"status": "verified", "score": 100})
    SessionSentinel.atomic_write(target, content)
    assert target.exists()
    assert json.loads(target.read_text(encoding="utf-8")) == json.loads(content)


def test_in_flight_alerts_persistence(sentinel, tmp_path):
    alert = DetectedAnomaly(
        category=AnomalyCategory.TOOL_LOOP,
        severity=AnomalySeverity.HIGH,
        title="Test Loop",
        description="Loop in progress",
        raw_evidence="ev",
        suggested_fix_summary="fix"
    )
    sentinel.alerts_file = tmp_path / "alerts.json"
    sentinel.write_in_flight_alerts("sess_123", [alert])
    assert sentinel.alerts_file.exists()
    data = json.loads(sentinel.alerts_file.read_text(encoding="utf-8"))
    assert data["session_id"] == "sess_123"
    assert len(data["alerts"]) == 1
    assert data["alerts"][0]["category"] == "TOOL_LOOP"


def test_synthesize_and_enqueue_self_healing_task(sentinel, tmp_path):
    session_data = {
        "session_id": "sess_anomalous_001",
        "model": "gemini-3.8-flash",
        "started_at": 100.0,
        "ended_at": 150.0,
        "title": "Failing Slice",
        "messages": [
            (1, "user", "TASK-DNK-CANVAS-20260906-006: Execute Slice 2", None, None, 101.0),
            (2, "tool", "HTTP 401: Expected OAuth 2 access token", "model_call", None, 102.0),
        ]
    }
    audit = sentinel.analyze_trajectory(session_data)
    assert audit.task_id == "TASK-DNK-CANVAS-20260906-006"
    assert len(audit.anomalies) == 1

    task_file = sentinel.synthesize_self_heal_task_spec(audit)
    assert task_file is not None
    assert task_file.exists()

    content = task_file.read_text(encoding="utf-8")
    assert "DNK-MRH-HEADER" in content
    assert "dnk_dev_fullstack" in content
    assert "HTTP 401" in content

    # Test Canvas Enqueueing with isolated persistence
    orig_instance = NodeTaskPersistenceManager._instance
    test_db = str(tmp_path / "node_task_graph.json")
    manager = NodeTaskPersistenceManager(data_file_path=test_db)
    manager.reset_to_baseline()
    NodeTaskPersistenceManager._instance = manager

    try:
        node_id = sentinel.enqueue_to_canvas(audit, task_file)
        assert node_id is not None
        assert node_id.startswith("task-selfheal-")

        graph = manager.load_graph()
        assert node_id in graph.nodes
        saved_node = graph.nodes[node_id]
        assert saved_node.assigned_agent == "dnk_dev_fullstack"
        assert saved_node.project_id == "dnk_core"
        assert saved_node.node_type == NodeType.TASK
        assert "self_heal" in saved_node.tags
    finally:
        NodeTaskPersistenceManager._instance = orig_instance


def test_recursion_depth_tracking(sentinel, tmp_path):
    # Case 1: default depth 0 for normal user session
    assert sentinel.get_session_recursion_depth("sess_root") == 0

    # Case 2: depth from session messages
    session_data = {
        "session_id": "sess_depth_1",
        "messages": [
            {"role": "user", "content": "🏥 [Self-Heal Autopilot Depth 1/2] Fix bug"}
        ]
    }
    assert sentinel.get_session_recursion_depth("sess_depth_1", session_data=session_data) == 1

    # Case 3: depth from lineage file
    sentinel.lineage_file = tmp_path / "self_heal_lineage.json"
    sentinel.record_lineage(
        session_id="sess_lineage_2",
        task_id="TASK-TEST-002",
        depth=2,
        parent_session_id="sess_lineage_1"
    )
    assert sentinel.get_session_recursion_depth("sess_lineage_2") == 2


def test_auto_dispatch_self_healing_and_circuit_breaker(sentinel, tmp_path, monkeypatch):
    sentinel.alerts_file = tmp_path / "alerts.json"
    sentinel.lineage_file = tmp_path / "self_heal_lineage.json"

    # Create dummy self heal task file
    task_file = tmp_path / "TASK-TEST-001.md"
    task_file.write_text("# Test task", encoding="utf-8")

    anomaly = DetectedAnomaly(
        category=AnomalyCategory.AUTH_ERROR,
        severity=AnomalySeverity.CRITICAL,
        title="HTTP 401 Auth Error",
        description="Missing token",
        raw_evidence="401",
        suggested_fix_summary="Add token"
    )

    audit = SessionAuditResult(
        session_id="sess_root_test",
        anomalies=[anomaly],
        self_heal_task_path=str(task_file)
    )

    # Mock dnk_swarm_dispatch
    dispatched_calls = []

    def mock_dispatch(agent, task_description, workspace_id, parameters=None):
        dispatched_calls.append({"agent": agent, "desc": task_description, "params": parameters})
        return json.dumps({"status": "success", "worker": agent})

    monkeypatch.setattr("core.hermes_agent.tools.dnk_swarm_tool.dnk_swarm_dispatch", mock_dispatch)

    # Test auto dispatch at depth 0 -> dispatches with depth 1
    # AUTH_ERROR routes to gerych_auditor per intelligent routing
    res = sentinel.dispatch_self_heal(audit, max_recursion_depth=2)
    assert res["status"] == "dispatched"
    assert res["depth"] == 1
    assert res["agent"] == "gerych_auditor"
    assert audit.dispatched_agent == "gerych_auditor"
    assert audit.dispatch_status == "dispatched"
    assert len(dispatched_calls) == 1

    # Verify lineage was recorded
    assert sentinel.lineage_file.exists()
    lineage_data = json.loads(sentinel.lineage_file.read_text(encoding="utf-8"))
    assert "sess_root_test" in lineage_data["sessions"]
    assert lineage_data["sessions"]["sess_root_test"]["depth"] == 1

    # Test Circuit Breaker: when session is already at max depth (e.g. 2)
    sentinel.record_lineage(
        session_id="sess_max_depth",
        task_id="TASK-TEST-003",
        depth=2
    )

    audit_max = SessionAuditResult(
        session_id="sess_max_depth",
        anomalies=[anomaly],
        self_heal_task_path=str(task_file)
    )

    breaker_res = sentinel.dispatch_self_heal(audit_max, max_recursion_depth=2)
    assert breaker_res["status"] == "blocked"
    assert breaker_res["reason"] == "max_recursion_depth_reached"
    assert audit_max.dispatch_status == "recursion_depth_exceeded"

    # Verify circuit breaker alert logged in alerts file
    assert sentinel.alerts_file.exists()
    alerts_data = json.loads(sentinel.alerts_file.read_text(encoding="utf-8"))
    assert alerts_data["session_id"] == "sess_max_depth"
    alert_titles = [a["title"] for a in alerts_data["alerts"]]
    assert any("Self-Heal Recursion Limit Reached" in t for t in alert_titles)


def test_sentinel_closed_loop_scones_remedy_and_routing(sentinel, tmp_path, monkeypatch):
    """Vector 2 Enhancement: Verify intelligent worker routing & SCONES remedy injection."""
    task_file = tmp_path / "TASK-TEST-002.md"
    task_file.write_text("# Error loop test", encoding="utf-8")

    anomaly_code = DetectedAnomaly(
        category=AnomalyCategory.ERROR_LOOP,
        severity=AnomalySeverity.CRITICAL,
        title="Repeated ModuleNotFoundError in apps/api",
        description="Missing dependency or bad import",
        raw_evidence="No module named 'fastapi'",
        suggested_fix_summary="Install dependency or fix import",
        target_files=["apps/api/main.py"]
    )

    audit = SessionAuditResult(
        session_id="sess_code_error",
        anomalies=[anomaly_code],
        self_heal_task_path=str(task_file)
    )

    dispatched = []

    def mock_dispatch(agent, task_description, workspace_id, parameters=None):
        dispatched.append({"agent": agent, "desc": task_description, "params": parameters})
        return json.dumps({"status": "dispatched", "worker": agent})

    monkeypatch.setattr("core.hermes_agent.tools.dnk_swarm_tool.dnk_swarm_dispatch", mock_dispatch)

    res = sentinel.dispatch_self_heal(audit, max_recursion_depth=2)
    assert res["status"] == "dispatched"
    # ERROR_LOOP routes to dnk_dev_fullstack
    assert res["agent"] == "dnk_dev_fullstack"
    assert len(dispatched) == 1
    assert "target_files" in dispatched[0]["params"]
    assert "apps/api/main.py" in dispatched[0]["params"]["target_files"]
    assert "scones_remedy" in dispatched[0]["params"]


