# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_git_context_controller.py"
# purpose: "Unit tests for GitContextController: creation, isolation, discard, merge, and commit persistence."
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


@pytest.fixture(autouse=True)
def clean_branch_cache():
    """Ensure clean cache directory for each test run."""
    p = Path("cache/context_branches")
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
    yield
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)


def test_create_branch():
    """Verify branch creation with proper ID prefix and registry tracking."""
    gcc = GitContextController()
    branch_id = gcc.create_branch("experiment-1")
    assert branch_id.startswith("branch-")
    assert branch_id in gcc.branches


def test_discard_failed_branch():
    """Verify failed speculative execution branch can be discarded completely."""
    gcc = GitContextController()
    branch_id = gcc.create_branch("failed-experiment")

    # Add messages (simulate speculative exploration)
    for i in range(100):
        gcc.add_message({"role": "user", "content": f"Message {i}"})

    branch_stats = gcc.get_branch_stats(branch_id)
    assert branch_stats["message_count"] == 100

    # Discard failed branch
    gcc.discard_branch(branch_id)
    assert branch_id not in gcc.branches


def test_merge_successful_branch():
    """Verify successful branch squashes into summary and merges into main."""
    gcc = GitContextController()
    branch_id = gcc.create_branch("successful-experiment")

    # Add messages
    gcc.add_message({"role": "user", "content": "Refactored module X"})
    gcc.add_message({"role": "assistant", "content": "Tests pass, verified"})

    # Merge successful branch
    commit_id = gcc.merge_branch(branch_id, success=True)
    assert commit_id is not None
    assert commit_id in gcc.commits

    # Main context has summary of experiment
    main_stats = gcc.get_branch_stats("main")
    assert main_stats["message_count"] > 0


def test_branch_isolation():
    """Verify messages across branches remain strictly isolated."""
    gcc = GitContextController()
    branch1 = gcc.create_branch("experiment-1")
    branch2 = gcc.create_branch("experiment-2")

    # Add messages to branch1
    gcc.checkout(branch1)
    gcc.add_message({"role": "user", "content": "Branch 1 message"})

    # Add messages to branch2
    gcc.checkout(branch2)
    gcc.add_message({"role": "user", "content": "Branch 2 message"})

    # Verify isolation
    assert "Branch 1 message" in [m["content"] for m in gcc.branches[branch1].messages]
    assert "Branch 2 message" in [m["content"] for m in gcc.branches[branch2].messages]
    assert "Branch 1 message" not in [m["content"] for m in gcc.branches[branch2].messages]
    assert "Branch 2 message" not in [m["content"] for m in gcc.branches[branch1].messages]


def test_commit_and_load():
    """Verify branch and commit state persistence and reload."""
    gcc = GitContextController()
    branch_id = gcc.create_branch("test-branch")

    # Add messages
    gcc.add_message({"role": "user", "content": "Message 1"})
    gcc.add_message({"role": "assistant", "content": "Message 2"})

    # Commit
    commit_id = gcc.commit_branch(branch_id, "Test commit")
    assert commit_id in gcc.commits

    # Reload from disk
    gcc2 = GitContextController()
    assert branch_id in gcc2.branches
    assert commit_id in gcc2.commits
