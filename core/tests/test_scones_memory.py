# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_scones_memory.py"
# purpose: "Unit tests for SCONES long-term memory engine, model router fallback, and compaction."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from core.scones_memory import SCONESMemoryEngine

STORAGE_PATH = "core/tests/scones_test_storage.json"

@pytest.fixture
def memory_engine():
    # Setup
    if os.path.exists(STORAGE_PATH):
        os.remove(STORAGE_PATH)
    engine = SCONESMemoryEngine(storage_path=STORAGE_PATH)
    yield engine
    # Teardown
    if os.path.exists(STORAGE_PATH):
        os.remove(STORAGE_PATH)

def test_scones_memory_storage(memory_engine):
    """Verify that SCONES adds, retrieves, and persists cognitive memories."""
    assert len(memory_engine.get_memories()) == 0
    
    # Add first memory
    memory_engine.add_memory("git-research", "Assimilated FastMCP templates", importance=1.8)
    assert len(memory_engine.get_memories()) == 1
    
    # Retrieve filtered
    filtered = memory_engine.get_memories("git-research")
    assert len(filtered) == 1
    assert filtered[0]["content"] == "Assimilated FastMCP templates"
    assert filtered[0]["importance"] == 1.8

    # Re-instantiate engine to verify file persistence
    new_engine = SCONESMemoryEngine(storage_path=STORAGE_PATH)
    assert len(new_engine.get_memories()) == 1
    assert new_engine.get_memories()[0]["topic"] == "git-research"

def test_scones_model_routing_fallback(memory_engine):
    """Verify model fallback routing via SelfHealingModelRouter."""
    # Healthy request
    res1 = memory_engine.route_model("gemini-3.5-flash")
    assert res1["status"] == "ok"
    assert res1["active_model"] == "gemini-3.5-flash"
    assert res1["active_provider"] == "vertex"

    # API Error request (trigger auto-healing)
    res2 = memory_engine.route_model("gemini-3.5-flash", error_code=429)
    assert res2["status"] == "healed"
    assert "mistralai/codestral-22b-instruct" in res2["active_model"]
    assert res2["active_provider"] == "nvidia_nim"
    assert "Auto-healed" in res2["reason"]

def test_scones_context_compactor(memory_engine):
    """Verify heavy text/log compaction works as expected."""
    heavy_logs = "System warning line\n" * 100
    compacted = memory_engine.compact_log_context(heavy_logs, max_lines=10)
    
    # Verify line truncation
    lines = compacted.splitlines()
    assert len(lines) == 13  # 10 lines + 2 spacing lines for TRUNCATED tag
    assert "[TRUNCATED 90 LINES TO PREVENT CONTEXT BLOAT]" in compacted
