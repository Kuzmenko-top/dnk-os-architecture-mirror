# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_memory_transplant.py"
# purpose: "Unit tests for Gerych's MemoryManager and SCONESMemoryProvider integration in MVP"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import os
import json
import pytest
from core.memory.memory_manager import MemoryManager
from core.memory.scones_provider import SCONESMemoryProvider

TEST_STORAGE_PATH = "core/tests/scones_transplant_test.json"

@pytest.fixture
def memory_setup():
    # Teardown any pre-existing test files
    if os.path.exists(TEST_STORAGE_PATH):
        os.remove(TEST_STORAGE_PATH)
        
    # Setup manager & provider
    manager = MemoryManager()
    provider = SCONESMemoryProvider()
    manager.add_provider(provider)
    
    # Initialize
    manager.initialize_all(
        session_id="test_transplant_session",
        hermes_home=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        platform="cli"
    )
    
    # For testing, override provider engine storage path explicitly
    provider._engine.storage_path = TEST_STORAGE_PATH
    provider._engine.memories = []
    provider._engine.save_memories()
    
    yield manager, provider
    
    # Teardown
    if os.path.exists(TEST_STORAGE_PATH):
        os.remove(TEST_STORAGE_PATH)

def test_memory_manager_dispatch(memory_setup):
    """Verify that MemoryManager correctly delegates tool calls to the SCONES provider."""
    manager, provider = memory_setup
    
    # Add a memory using the manager's tool call handler
    add_args = {
        "topic": "system-architecture",
        "content": "Hexagonal ports and adapters standard established for multi-agent synchronization.",
        "importance": 1.5
    }
    add_res_str = manager.handle_tool_call("scones_add_memory", add_args)
    add_res = json.loads(add_res_str)
    
    assert add_res["success"] is True
    assert add_res["memory"]["topic"] == "system-architecture"
    
    # Retrieve memories
    get_args = {"topic": "system-architecture"}
    get_res_str = manager.handle_tool_call("scones_get_memories", get_args)
    get_res = json.loads(get_res_str)
    
    assert get_res["success"] is True
    assert len(get_res["memories"]) == 1
    assert get_res["memories"][0]["content"] == add_args["content"]

def test_memory_prefetch_context(memory_setup):
    """Verify that MemoryManager fetches and formats context for system injection."""
    manager, provider = memory_setup
    
    # Pre-populate some memories
    provider._engine.add_memory("docker", "All databases must run in docker containers.", importance=1.0)
    provider._engine.add_memory("languages", "Ukrainian is the canonical interface language.", importance=1.0)
    
    # Query something related to docker
    context_str = manager.prefetch_all("How should we run our databases?")
    
    # Should contain context fencing
    assert "<memory-context>" in context_str
    assert "</memory-context>" in context_str
    assert "recalled memory context" in context_str
    assert "All databases must run in docker" in context_str
    
    # Should not contain unrelated language memory
    assert "Ukrainian" not in context_str
