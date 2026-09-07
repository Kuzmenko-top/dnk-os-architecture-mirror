# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_task_engine_sync.py"
# purpose: "Verify live PostgreSQL synchronization and state fallbacks in TaskEngine."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from core.task_engine import TaskEngine

def test_task_engine_local_operations():
    engine = TaskEngine()
    
    # Verify local task addition
    task = engine.add_task("T_TEST_1", "Test task description", task_type="story", phase="P1", status="todo")
    assert task["id"] == "T_TEST_1"
    assert task["status"] == "todo"

    # Verify local status update
    assert engine.update_status("T_TEST_1", "done") is True
    assert engine.update_status("NON_EXISTENT_LOCAL", "done") is False


def test_task_engine_database_fallback(monkeypatch):
    """
    Verifies that TaskEngine falls back gracefully to local memory when
    the PostgreSQL connection is unavailable or errors out.
    """
    # Force a non-existent port to simulate connection failure
    monkeypatch.setenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:9999/invalid_db")
    
    engine = TaskEngine()
    engine.add_task("112233", "Fake DB Task", status="todo")

    # Sync should run without crashing
    engine.sync_with_db()
    
    # Status update of numerical task ID should fail on DB but succeed locally
    assert engine.update_status("112233", "done") is True
    assert engine._tasks["112233"]["status"] == "done"


def test_task_engine_database_sync_integration():
    """
    If local postgres is running, check that sync_with_db fetches tasks.
    """
    engine = TaskEngine()
    # Simply verify no exception is thrown during sync
    engine.sync_with_db("00_CORE")
    
    victory_map = engine.get_victory_map("00_CORE")
    assert "total_tasks" in victory_map
    assert "victory_percentage" in victory_map
