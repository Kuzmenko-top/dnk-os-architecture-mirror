# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_hexagonal_adapters.py"
# purpose: "Comprehensive Unit Tests for Hexagonal Ports and Adapters."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import os
import shutil
import pytest
from typing import Generator
from core.auth_engine import MaksymAuthEngine
from core.canvas_engine import CanvasEngine
from core.hermes_runtime import HermesRuntime
from core.swarm_orchestrator import SwarmOrchestrator
from core.adapters.hermes_adapter import HermesAdapter
from core.adapters.canvas_adapter import CanvasAdapter
from core.adapters.swarm_adapter import SwarmAdapter

TEST_DIR = "test_run_adapters_temp"
SESSION_STORE = f"{TEST_DIR}/session_registry.json"

@pytest.fixture(autouse=True)
def run_around_tests() -> Generator[None, None, None]:
    """Cleans and scaffolds the temporary test run directory."""
    os.makedirs(TEST_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR, ignore_errors=True)


def test_hermes_adapter():
    auth = MaksymAuthEngine(session_store_path=SESSION_STORE, expected_phrase="погоджую")
    runtime = HermesRuntime(auth_engine=auth, max_failures=2)
    adapter = HermesAdapter(runtime)

    # 1. Test Dry Run
    plan = adapter.run_dry_run("test_action", ["file.txt"], {"arg": "value"})
    assert plan["dry_run"] is True
    assert "file.txt" in plan["targets"]

    # 2. Test Safe Run (Success)
    test_file = f"{TEST_DIR}/test_adapter.py"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("data")

    def run_fn():
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("mutated")

    res = adapter.run_safely(run_fn, lambda: True, [test_file])
    assert res["status"] == "Success"

    # 3. Test Destructive Actions
    app_id = adapter.stage_destructive_action("wipe", "db", {"force": True})
    assert len(app_id) == 8

    # Approve with wrong phrase
    assert adapter.confirm_destructive_action(app_id, "wrong") is False

    # Approve with correct phrase
    assert adapter.confirm_destructive_action(app_id, "погоджую") is True


def test_canvas_adapter():
    engine = CanvasEngine()
    adapter = CanvasAdapter(engine)

    # 1. Create node
    node = adapter.create_node("n1", "Node 1", "TaskNode", "Queued")
    assert node.id == "n1"
    assert node.state == "Queued"

    # 2. Modify node state
    adapter.modify_node_state("n1", "Executing")
    assert engine.nodes["n1"].state == "Executing"

    # 3. Connect nodes
    node2 = adapter.create_node("n2", "Node 2", "TaskNode", "Queued")
    adapter.connect_nodes("n1", "n2")
    assert ("n1", "n2") in engine.edges

    # 4. Cycle detection
    assert adapter.check_cycle_dependencies() is False
    adapter.connect_nodes("n2", "n1")
    assert adapter.check_cycle_dependencies() is True

    # 5. Disconnect nodes
    assert adapter.disconnect_nodes("n1", "n2") is True
    assert adapter.disconnect_nodes("n1", "n2") is False

    # 6. Text representation and export
    txt = adapter.draw_text_representation()
    assert "n1" in txt
    assert "n2" in txt

    exported = adapter.export_state_dict()
    assert len(exported["nodes"]) == 2


def test_swarm_adapter():
    orchestrator = SwarmOrchestrator()
    adapter = SwarmAdapter(orchestrator)

    # 1. Load role
    yaml_str = """
    name: test_agent
    role: CHIEF_BUILDER
    system_instructions: "Builder instructions."
    """
    manifest = adapter.load_role(yaml_str)
    assert manifest["name"] == "test_agent"
    assert orchestrator.roles["test_agent"]["role"] == "CHIEF_BUILDER"

    # 2. Add skill
    adapter.add_skill(
        name="test_skill",
        description="A great skill for adapter tests",
        content="def test(): pass",
        tags=["adapter", "test"]
    )
    assert "test_skill" in orchestrator.skills

    # 3. Retrieve skills
    skills, duration = adapter.retrieve_skills("test_agent", "adapter execution", limit=1)
    assert len(skills) == 1
    assert skills[0]["name"] == "test_skill"
    assert duration >= 0.0

    # 4. Prepare instructions
    prompt = adapter.prepare_instructions("test_agent", "adapter execution")
    assert "Builder instructions." in prompt
    assert "test_skill" in prompt
