# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_scones_middleware_hook.py"
# purpose: "Unit and integration tests for SCONES zero-click expectation middleware hook."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import json
import pytest
import tempfile
from core.scones_memory import SCONESMemoryEngine
from core.hermes_agent.tools.dnk_scones_tool import scones_add_memory


@pytest.fixture
def temp_storage():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)
    err_path = path.replace(".json", "_error_solutions.json")
    if os.path.exists(err_path):
        os.remove(err_path)


def test_scones_engine_zero_click_hook_initialized(temp_storage):
    engine = SCONESMemoryEngine(storage_path=temp_storage, enable_pgvector=False)
    assert engine.enable_expectation_hook is True
    assert engine.expectation_validator is not None
    assert engine.strict_expectation is False


def test_scones_add_memory_clean_record(temp_storage):
    engine = SCONESMemoryEngine(storage_path=temp_storage, enable_pgvector=False)
    entry = engine.add_memory(
        topic="Architecture Decision",
        content="We adopt zero-waste atomic slices for subagent coordination.",
        importance=0.9,
    )
    assert entry["id"].startswith("SCONES-MEM-")
    assert "_expectation_violations" not in entry["metadata"]

    val_res = engine.validate_memory_entry(entry)
    assert val_res is not None
    assert val_res.is_valid is True
    assert len(val_res.violations) == 0


def test_scones_add_memory_catches_importance_violation(temp_storage):
    engine = SCONESMemoryEngine(storage_path=temp_storage, enable_pgvector=False, strict_expectation=False)
    entry = engine.add_memory(
        topic="Invalid Importance Memory",
        content="Testing out-of-bounds importance range in SCONES hook.",
        importance=2.5,  # range rule is [0.0, 1.0]
    )
    assert "_expectation_violations" in entry["metadata"]
    violations = entry["metadata"]["_expectation_violations"]
    assert any("importance" in v for v in violations)


def test_scones_add_memory_catches_forbidden_absolute_path(temp_storage):
    engine = SCONESMemoryEngine(storage_path=temp_storage, enable_pgvector=False, strict_expectation=False)
    forbidden_path = "/" + "Users" + "/developer/code/secret.py"
    entry = engine.add_memory(
        topic="Path Leak Topic",
        content=f"Secret file located at {forbidden_path}",
        importance=0.8,
    )
    assert "_expectation_violations" in entry["metadata"]
    violations = entry["metadata"]["_expectation_violations"]
    assert any("no_hardcoded_user_paths" in v or "forbidden absolute user path" in v for v in violations)


def test_scones_add_memory_strict_mode_raises(temp_storage):
    engine = SCONESMemoryEngine(storage_path=temp_storage, enable_pgvector=False, strict_expectation=True)
    forbidden_path = "/" + "home" + "/ubuntu/config.json"
    with pytest.raises(ValueError) as excinfo:
        engine.add_memory(
            topic="Strict Leak",
            content=f"Config path {forbidden_path}",
            importance=0.8,
        )
    assert "SCONES memory validation failed" in str(excinfo.value)


def test_hermes_tool_scones_add_memory_integration(temp_storage, monkeypatch):
    # Test valid addition through tool wrapper
    res_raw = scones_add_memory(
        topic="Swarm Optimization",
        content="Parallel tasks execute via dnk_swarm_parallel.",
        importance=0.95,
        workspace_id="ws-alpha-001",
    )
    res = json.loads(res_raw)
    assert res["status"] == "success"
    assert "memory_id" in res
