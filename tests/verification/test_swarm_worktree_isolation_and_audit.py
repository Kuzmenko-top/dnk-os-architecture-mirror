# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_swarm_worktree_isolation_and_audit.py"
# purpose: "Verify Git Worktree Isolation, NDJSON Audit Trail, and Sangha Consensus Gate."
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
import shutil
import subprocess
from pathlib import Path
import pytest

from core.orchestrator.swarm_worktree import SwarmWorktreeManager
from core.orchestrator.swarm_coordinator import GerychSwarmCoordinator


@pytest.fixture
def temp_audit_env(tmp_path):
    hub_root = tmp_path / "mock_hub"
    hub_root.mkdir()
    # Initialize a mock git repo
    subprocess.run(["git", "init"], cwd=str(hub_root), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test Runner"], cwd=str(hub_root), check=True)
    subprocess.run(["git", "config", "user.email", "test@dnk-hub.ai"], cwd=str(hub_root), check=True)
    
    # Create initial commit
    readme = hub_root / "README.md"
    readme.write_text("# Mock Hub\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=str(hub_root), check=True)
    subprocess.run(["git", "commit", "-m", "chore: initial commit"], cwd=str(hub_root), check=True)
    
    # Create artifacts dir
    artifacts_dir = hub_root / "data" / "swarm_artifacts"
    artifacts_dir.mkdir(parents=True)
    
    yield hub_root


def test_ndjson_audit_event_logging(temp_audit_env):
    mgr = SwarmWorktreeManager(hub_root=temp_audit_env)
    
    event = mgr.record_audit_event(
        event="SWARM_TASK_DISPATCHED",
        agent="dnk_dev_fullstack",
        task_id="task_123",
        trace_id="tr_456",
        details={"action": "build_api", "target_files": ["apps/api/router.py"]},
    )
    
    assert event["event"] == "SWARM_TASK_DISPATCHED"
    assert mgr.audit_trail_path.exists()
    
    events = mgr.read_audit_events(task_id="task_123")
    assert len(events) == 1
    assert events[0]["agent"] == "dnk_dev_fullstack"
    assert events[0]["trace_id"] == "tr_456"
    assert events[0]["details"]["action"] == "build_api"


def test_sangha_consensus_evaluation(temp_audit_env):
    mgr = SwarmWorktreeManager(hub_root=temp_audit_env)
    
    # Case 1: Valid clean Python file
    valid_file = temp_audit_env / "valid.py"
    valid_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    
    approved, details = mgr.evaluate_sangha_consensus(
        worktree_path=temp_audit_env,
        agent="dnk_dev_fullstack",
        task_id="task_valid",
        changed_files=["valid.py"],
    )
    assert approved is True
    assert details["verdict"] == "APPROVED"
    assert len(details["violations"]) == 0

    # Case 2: Syntax error
    invalid_py = temp_audit_env / "bad_syntax.py"
    invalid_py.write_text("def bad_syntax(:\n", encoding="utf-8")
    
    approved, details = mgr.evaluate_sangha_consensus(
        worktree_path=temp_audit_env,
        agent="gerych_builder",
        task_id="task_bad_syntax",
        changed_files=["bad_syntax.py"],
    )
    assert approved is False
    assert details["verdict"] == "REJECTED"
    assert any("syntax error" in v.lower() for v in details["violations"])

    # Case 3: Absolute path violation (path hygiene failure)
    dirty_path_py = temp_audit_env / "dirty.py"
    bad_abs_path = "/Users" + "/kuzmenko.top/secret"
    dirty_path_py.write_text(f"PATH = '{bad_abs_path}'\n", encoding="utf-8")
    
    approved, details = mgr.evaluate_sangha_consensus(
        worktree_path=temp_audit_env,
        agent="dnk_dev_fullstack",
        task_id="task_dirty",
        changed_files=["dirty.py"],
    )
    assert approved is False
    assert details["verdict"] == "REJECTED"
    assert any("absolute path" in v.lower() for v in details["violations"])


def test_worktree_lifecycle_and_isolation(temp_audit_env):
    mgr = SwarmWorktreeManager(hub_root=temp_audit_env)
    task_id = "test_subagent_001"
    agent = "gerych_builder"
    
    # 1. Create worktree
    wt_path, branch = mgr.create_worktree(task_id=task_id, agent=agent)
    assert wt_path.exists()
    assert (wt_path / "README.md").exists()
    
    # 2. Modify file in worktree only
    new_doc = wt_path / "WORKTREE_DOC.md"
    new_doc.write_text("# Created in isolated worktree\n", encoding="utf-8")
    
    # Main repo must NOT have this file yet
    assert not (temp_audit_env / "WORKTREE_DOC.md").exists()
    
    # 3. Detect changes
    changed = mgr.detect_changed_files(wt_path)
    assert "WORKTREE_DOC.md" in changed
    
    # 4. Sangha consensus
    approved, _ = mgr.evaluate_sangha_consensus(
        worktree_path=wt_path,
        agent=agent,
        task_id=task_id,
        changed_files=changed,
    )
    assert approved is True
    
    # 5. Merge changes
    merged = mgr.merge_worktree_changes(
        worktree_path=wt_path,
        branch_name=branch,
        agent=agent,
        task_id=task_id,
    )
    assert merged is True
    
    # 6. Cleanup worktree
    cleaned = mgr.cleanup_worktree(
        worktree_path=wt_path,
        branch_name=branch,
    )
    assert cleaned is True
    assert not wt_path.exists()


def test_coordinator_integration_with_worktree_and_audit(temp_audit_env):
    coord = GerychSwarmCoordinator()
    coord.hub_root = temp_audit_env
    coord.worktree_manager = SwarmWorktreeManager(hub_root=temp_audit_env)
    
    # Test task dispatch audit
    disp = coord.dispatch_task(
        from_agent="gerych_prime",
        to_agent="dnk_dev_fullstack",
        payload={"action": "generate_router", "trace_id": "test_trace_01"},
    )
    assert disp["status"] == "dispatched"
    
    # Verify audit event written
    events = coord.worktree_manager.read_audit_events()
    assert any(e["event"] == "SWARM_TASK_DISPATCHED" and e["agent"] == "dnk_dev_fullstack" for e in events)
