# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_organic_synthesis.py"
# purpose: "End-to-End Pipeline Verification Test for DNK OS MVP 0.1.0."
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
from core.kernel import FastMCPKernel
from core.omni_router import omni_router
from core.adapters.canvas_adapter import CanvasAdapter
from core.adapters.swarm_adapter import SwarmAdapter
from core.adapters.hermes_adapter import HermesAdapter

TEST_DIR = "test_run_synthesis_temp"
SESSION_STORE = f"{TEST_DIR}/session_registry.json"
ACCOUNTING_LOG = f"{TEST_DIR}/accounting_log.json"

@pytest.fixture(autouse=True)
def run_around_tests() -> Generator[None, None, None]:
    """Cleans and scaffolds the temporary test run directory."""
    os.makedirs(TEST_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR, ignore_errors=True)


def test_end_to_end_synthesis_pipeline():
    """
    Verifies the end-to-end pipeline:
    Task Input -> Intent Routing -> Swarm Dispatch -> Hermes Execution -> Accounting Audit.
    """
    # Initialize the Unified Kernel (Organism)
    kernel = FastMCPKernel(session_store_path=SESSION_STORE, log_path=ACCOUNTING_LOG)
    
    # Initialize Hexagonal Adapters
    canvas_adapter = CanvasAdapter(kernel.canvas)
    swarm_adapter = SwarmAdapter(kernel.orchestrator)
    hermes_adapter = HermesAdapter(kernel.runtime)

    # 1. Task Input
    task_goal = "Configure and verify Shopify theme Tinker 4.3.1 layout"

    # 2. Intent Routing
    dispatch_res = omni_router.dispatch(task_goal)
    assert dispatch_res["status"] == "dispatched"
    assert dispatch_res["classification"]["assigned_agent"] == "shopify_pro"
    
    assigned_agent = dispatch_res["classification"]["assigned_agent"]
    domain = dispatch_res["classification"]["intent"]

    # 3. Swarm Dispatch (Register Agent, Skills & Add to Canvas)
    yaml_manifest = f"""
    name: {assigned_agent}
    role: Shopify_Theme_Specialist
    system_instructions: "You are a specialized Shopify Theme engineer."
    """
    swarm_adapter.load_role(yaml_manifest)
    
    swarm_adapter.add_skill(
        name="shopify_theme_validator",
        description="Validates Shopify liquid structure and assets",
        content="def validate_theme(): return True",
        tags=["shopify", "theme", "tinker"]
    )

    # Create Task & Agent nodes on the visual canvas
    task_node = canvas_adapter.create_node("t1", task_goal, "TaskNode", "Queued")
    agent_node = canvas_adapter.create_node("a1", f"Agent: {assigned_agent}", "AgentNode", "Queued")
    canvas_adapter.connect_nodes("t1", "a1")

    # Generate instructions with dynamic skill RAG injection
    compiled_instructions = swarm_adapter.prepare_instructions(assigned_agent, task_goal)
    assert "shopify_theme_validator" in compiled_instructions
    assert "Shopify Theme engineer" in compiled_instructions

    # 4. Hermes Execution (Safe runtime environment with rollback & checks)
    canvas_adapter.modify_node_state("t1", "Executing")
    canvas_adapter.modify_node_state("a1", "Executing")

    victim_file = f"{TEST_DIR}/theme.liquid"
    with open(victim_file, "w", encoding="utf-8") as f:
        f.write("<html>original</html>")

    def execute_action():
        # Modify code safely
        with open(victim_file, "w", encoding="utf-8") as f:
            f.write("<html>shopify_verified</html>")

    def verify_action():
        # Check if verified
        with open(victim_file, "r", encoding="utf-8") as f:
            content = f.read()
        return "shopify_verified" in content

    run_res = hermes_adapter.run_safely(execute_action, verify_action, [victim_file])
    assert run_res["status"] == "Success"

    # 5. Accounting Audit (Log Telemetry & Finalize Canvas)
    canvas_adapter.modify_node_state("t1", "Done")
    canvas_adapter.modify_node_state("a1", "Done")

    kernel.accounting.log_workflow_telemetry(
        project_id="02_Shopify",
        task_id="DNK-TASK-003",
        tokens_in=1200,
        tokens_out=1800,
        cost_usd=0.0035,
        duration_ms=250,
        success=True,
        token_savings_pct=85.0,
        dev_time_saved_pct=98.0,
        estimated_usd_saved=0.25,
        notes="Organic synthesis pipeline integration completed successfully"
    )

    # Verify Accounting and Canvas state via the Kernel (FastMCP interface)
    report_res = kernel.call_tool("accounting_get_report", {"project_id": "02_Shopify"})
    assert report_res["success"] is True
    assert report_res["metrics"]["total_runs"] == 1
    assert report_res["metrics"]["success_rate"] == 100.0
    assert report_res["metrics"]["total_cost_usd"] == 0.0035
    assert report_res["metrics"]["total_usd_saved"] == 0.25

    canvas_res = kernel.call_tool("canvas_get_view", {})
    text_view = canvas_res["text_render"]
    assert "t1" in text_view
    assert "🟢 Done" in text_view
    assert "a1" in text_view
    assert "Blocks: a1" in text_view
