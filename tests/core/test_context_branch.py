# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_context_branch.py"
# purpose: "Unit tests for ContextBranch data structures and task isolation helper."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import shutil
from pathlib import Path
import pytest
from core.orchestrator.git_context_controller import GitContextController
from core.orchestrator.context_branch import (
    ContextBranch,
    ContextCommit,
    ContextOperation,
    isolate_context_for_task,
)


@pytest.fixture(autouse=True)
def clean_branch_cache():
    """Ensure clean cache directory for each test run."""
    p = Path("cache/context_branches")
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
    yield
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)


def test_isolate_context_for_task():
    """Verify task context isolation creates a fresh branch and keeps main clean."""
    gcc = GitContextController()
    branch_id = isolate_context_for_task("refactor-123", gcc)

    assert branch_id.startswith("branch-")
    assert gcc.current_branch == branch_id

    # Verify isolation
    main_stats = gcc.get_branch_stats("main")
    branch_stats = gcc.get_branch_stats(branch_id)

    assert main_stats["message_count"] == 0  # Main is clean
    assert branch_stats["message_count"] == 0  # Branch starts fresh


def test_context_branch_dataclass():
    """Verify serialization, deserialization, and token estimation."""
    branch = ContextBranch(name="feature-x")
    branch.add_message({"role": "user", "content": "Hello world from test"})
    assert branch.message_count == 1
    assert branch.total_tokens > 0

    data = branch.to_dict()
    assert data["name"] == "feature-x"
    assert len(data["messages"]) == 1

    restored = ContextBranch.from_dict(data)
    assert restored.id == branch.id
    assert restored.name == branch.name
    assert restored.message_count == 1


def test_context_commit_dataclass():
    """Verify commit serialization and deserialization."""
    commit = ContextCommit(
        branch_id="branch-1",
        message="Initial checkpoint",
        summary="User added prompt",
    )
    assert commit.id is not None
    data = commit.to_dict()
    assert data["branch_id"] == "branch-1"
    assert data["message"] == "Initial checkpoint"

    restored = ContextCommit.from_dict(data)
    assert restored.id == commit.id
    assert restored.branch_id == "branch-1"
    assert restored.summary == "User added prompt"


def test_context_operations_constants():
    """Verify ContextOperation enum constants."""
    assert ContextOperation.COMMIT == "commit"
    assert ContextOperation.BRANCH == "branch"
    assert ContextOperation.MERGE == "merge"
    assert ContextOperation.DISCARD == "discard"
    assert ContextOperation.CHECKOUT == "checkout"
