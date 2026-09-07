# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_phase1_core.py"
# purpose: "Comprehensive Unit Test Suite for Core V2 MVP Phase 1 (100% coverage target)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import os
import time
import pytest
import shutil
from typing import Generator
from core.auth_engine import MaksymAuthEngine
from core.canvas_engine import CanvasEngine
from core.hermes_runtime import HermesRuntime
from core.swarm_orchestrator import SwarmOrchestrator
from core.accounting_engine import AccountingEngine
from core.kernel import FastMCPKernel

# Define paths for test artifacts (keep isolated within a test temp folder)
TEST_DIR = "test_run_temp"
SESSION_STORE = f"{TEST_DIR}/session_registry.json"
ACCOUNTING_LOG = f"{TEST_DIR}/accounting_log.json"

@pytest.fixture(autouse=True)
def run_around_tests() -> Generator[None, None, None]:
    """Cleans and scaffolds the temporary test run directory before and after each test."""
    os.makedirs(TEST_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR, ignore_errors=True)

# ==========================================
# 1. TEST SUITE: MaksymAuthEngine
# ==========================================

def test_auth_verify_phrase():
    auth = MaksymAuthEngine(session_store_path=SESSION_STORE, expected_phrase="погоджую")
    assert auth.verify_maksym("погоджую") is True
    assert auth.verify_maksym("непогоджую") is False
    assert auth.verify_maksym("") is False

def test_auth_session_lifecycle():
    auth = MaksymAuthEngine(session_store_path=SESSION_STORE)
    
    # Create session
    session_id = auth.create_session("Maksym", duration_sec=2)
    assert len(session_id) > 10
    assert auth.validate_session(session_id) is True
    
    # Terminate session
    assert auth.terminate_session(session_id) is True
    assert auth.validate_session(session_id) is False
    assert auth.terminate_session("non_existent") is False

def test_auth_session_expiration():
    auth = MaksymAuthEngine(session_store_path=SESSION_STORE)
    session_id = auth.create_session("Maksym", duration_sec=-10) # already expired
    assert auth.validate_session(session_id) is False

def test_auth_redact_secret():
    assert MaksymAuthEngine.redact_secret("sk-proj-example1234567890abcdef", prefix_len=7) == "sk-proj***def"
    assert MaksymAuthEngine.redact_secret("", prefix_len=7) == "«empty»"
    assert MaksymAuthEngine.redact_secret("abc", prefix_len=7) == "***"

# ==========================================
# 2. TEST SUITE: CanvasEngine
# ==========================================

def test_canvas_node_creation():
    engine = CanvasEngine()
    node = engine.add_node("node1", "Analyze Shopify", "TaskNode", "Queued")
    assert node.id == "node1"
    assert node.name == "Analyze Shopify"
    assert node.type == "TaskNode"
    assert node.state == "Queued"
    assert node.get_state_indicator() == "🔘 Queued"
    
    # Try invalid type
    with pytest.raises(ValueError):
        engine.add_node("node2", "Bad Node", "UnknownType")
        
    # Try invalid state
    with pytest.raises(ValueError):
        engine.add_node("node3", "Bad State", "TaskNode", "UnknownState")

def test_canvas_edge_management():
    engine = CanvasEngine()
    engine.add_node("node1", "Auth Node", "AgentNode", "Done")
    engine.add_node("node2", "Canvas Node", "TaskNode", "Executing")
    
    # Add Edge
    engine.add_edge("node1", "node2")
    assert ("node1", "node2") in engine.edges
    
    # Attempting to add edge with missing nodes raises KeyError
    with pytest.raises(KeyError):
        engine.add_edge("node1", "missing_node")
        
    # Remove Edge
    assert engine.remove_edge("node1", "node2") is True
    assert engine.remove_edge("node1", "node2") is False

def test_canvas_cycle_detection():
    engine = CanvasEngine()
    engine.add_node("n1", "Node 1", "TaskNode")
    engine.add_node("n2", "Node 2", "TaskNode")
    engine.add_node("n3", "Node 3", "TaskNode")
    
    # No edges -> no cycle
    assert engine.has_cycle() is False
    
    # Acyclic path
    engine.add_edge("n1", "n2")
    engine.add_edge("n2", "n3")
    assert engine.has_cycle() is False
    
    # Cyclic loop
    engine.add_edge("n3", "n1")
    assert engine.has_cycle() is True

def test_canvas_render_and_serialization():
    engine = CanvasEngine()
    engine.add_node("n1", "Test Node", "TaskNode", "Executing")
    text_view = engine.render_canvas_text()
    assert "n1" in text_view
    assert "🔵 Executing" in text_view
    
    data = engine.to_dict()
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["state"] == "Executing"

def test_canvas_sync_patterns():
    engine = CanvasEngine()
    synced_ids = engine.sync_patterns_to_nodes()
    assert len(synced_ids) >= 9, f"Expected at least 9 synced patterns, got {len(synced_ids)}"
    assert "DNK-PAT-001" in engine.nodes
    assert engine.nodes["DNK-PAT-001"].type == "TaskNode"
    assert engine.nodes["DNK-PAT-001"].state == "Done"
    assert "DNK-AGNT-001" in engine.nodes
    assert engine.nodes["DNK-AGNT-001"].type == "AgentNode"

# ==========================================
# 3. TEST SUITE: HermesRuntime
# ==========================================

def test_runtime_dry_run():
    auth = MaksymAuthEngine(session_store_path=SESSION_STORE)
    runtime = HermesRuntime(auth_engine=auth)
    plan = runtime.generate_dry_run_plan("reconstruct_kernel", ["file1.py"], {"arg": 1})
    assert plan["dry_run"] is True
    assert "file1.py" in plan["targets"]

def test_runtime_destructive_actions():
    auth = MaksymAuthEngine(session_store_path=SESSION_STORE, expected_phrase="погоджую")
    runtime = HermesRuntime(auth_engine=auth)
    
    approval_id = runtime.request_destructive_action("delete_file", "junk.txt", {"force": True})
    assert len(approval_id) == 8
    assert runtime.pending_approvals[approval_id]["approved"] is False
    
    # Verify with correct phrase
    success = runtime.approve_destructive_action(approval_id, "погоджую")
    assert success is True
    assert runtime.pending_approvals[approval_id]["approved"] is True
    
    # Check invalid phrase
    approval_id_2 = runtime.request_destructive_action("delete_file", "junk2.txt", {})
    assert runtime.approve_destructive_action(approval_id_2, "wrong_phrase") is False
    
    with pytest.raises(KeyError):
        runtime.approve_destructive_action("invalid_id", "погоджую")

def test_runtime_safe_execution_and_rollback():
    auth = MaksymAuthEngine(session_store_path=SESSION_STORE)
    runtime = HermesRuntime(auth_engine=auth, max_failures=2)
    
    test_file_path = f"{TEST_DIR}/victim.py"
    # Create initial file content
    with open(test_file_path, "w", encoding="utf-8") as f:
        f.write("print('original')")
        
    def action_good():
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("print('changed')")

    def action_bad():
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("print('broken_code_block')")

    def verify_success():
        return True

    def verify_fail():
        return False

    # 1. Run a successful action
    res = runtime.execute_safely(action_good, verify_success, [test_file_path])
    assert res["status"] == "Success"
    assert runtime.consecutive_failures == 0
    with open(test_file_path, "r", encoding="utf-8") as f:
        assert f.read() == "print('changed')"

    # 2. Run a failed action (1st failure)
    res_fail1 = runtime.execute_safely(action_bad, verify_fail, [test_file_path])
    assert res_fail1["status"] == "Failure"
    assert runtime.consecutive_failures == 1
    assert runtime.is_locked is False
    
    # 3. Run a failed action again (2nd failure -> Fail-Closed Rollback!)
    res_fail2 = runtime.execute_safely(action_bad, verify_fail, [test_file_path])
    assert res_fail2["status"] == "Rolled Back"
    assert runtime.consecutive_failures == 2
    assert runtime.is_locked is True
    
    # Content of victim.py should be rolled back to "print('changed')" (state before failed actions)
    with open(test_file_path, "r", encoding="utf-8") as f:
        assert f.read() == "print('changed')"

    # Attempting to run when locked is refused
    res_locked = runtime.execute_safely(action_good, verify_success, [test_file_path])
    assert res_locked["status"] == "Error"
    assert res_locked["locked"] is True

    # Unlock runtime
    runtime.unlock_runtime()
    assert runtime.is_locked is False
    assert runtime.consecutive_failures == 0

# ==========================================
# 4. TEST SUITE: SwarmOrchestrator
# ==========================================

def test_swarm_role_manifest_loading():
    orchestrator = SwarmOrchestrator()
    yaml_str = """
    name: gerych
    role: CHIEF_BUILDER
    system_instructions: "You are Gerych, Chief Builder of DNK OS."
    """
    manifest = orchestrator.load_role_manifest(yaml_str)
    assert manifest["name"] == "gerych"
    assert manifest["role"] == "CHIEF_BUILDER"
    
    # Invalid YAML raises ValueError
    with pytest.raises(ValueError):
        orchestrator.load_role_manifest("name: [unclosed_bracket")
        
    # Invalid format (missing mandatory fields)
    with pytest.raises(ValueError):
        orchestrator.load_role_manifest("role: CHIEF_BUILDER")

def test_swarm_rag_performance_and_injection():
    orchestrator = SwarmOrchestrator()
    
    # Load agent role
    orchestrator.load_role_manifest("""
    name: dev_agent
    role: Software_Developer
    system_instructions: "Solve coding tasks."
    """)

    # Register skills
    orchestrator.register_skill(
        name="shopify_api_helper",
        description="Helper for querying Shopify REST API for product catalogs",
        content="def get_products(): pass",
        tags=["shopify", "api", "products"]
    )
    orchestrator.register_skill(
        name="postgres_manager",
        description="Manager for PostgreSQL pgvector connections",
        content="def connect_pg(): pass",
        tags=["postgres", "db", "vector"]
    )

    # Inject skill on query
    matched, duration = orchestrator.inject_skills_rag("dev_agent", "how to pull products from shopify")
    assert len(matched) == 1
    assert matched[0]["name"] == "shopify_api_helper"
    # Assert RAG execution speed is strictly under the 0.05s budget (it is normally < 0.001s)
    assert duration < 0.05

    # Check instruction compilation
    system_prompt = orchestrator.compile_agent_system_instructions("dev_agent", "pull shopify catalog")
    assert "shopify_api_helper" in system_prompt
    assert "INJECTED PROCEDURAL SKILLS" in system_prompt

# ==========================================
# 5. TEST SUITE: AccountingEngine
# ==========================================

def test_accounting_telemetry_and_metrics():
    engine = AccountingEngine(log_path=ACCOUNTING_LOG)
    
    # Log 1st record
    engine.log_workflow_telemetry(
        project_id="PROJ_A",
        task_id="T001",
        tokens_in=1000,
        tokens_out=2000,
        cost_usd=0.0045,
        duration_ms=450,
        success=True,
        token_savings_pct=80.0,
        estimated_usd_saved=0.15
    )
    
    # Log 2nd record (failure)
    engine.log_workflow_telemetry(
        project_id="PROJ_A",
        task_id="T002",
        tokens_in=500,
        tokens_out=500,
        cost_usd=0.0015,
        duration_ms=200,
        success=False,
        token_savings_pct=0.0,
        estimated_usd_saved=0.0
    )

    # Log 3rd record (different project)
    engine.log_workflow_telemetry(
        project_id="PROJ_B",
        task_id="T003",
        tokens_in=100,
        tokens_out=100,
        cost_usd=0.0003,
        duration_ms=50,
        success=True,
        token_savings_pct=50.0,
        estimated_usd_saved=0.01
    )

    # Get aggregate metrics globally
    metrics = engine.get_aggregated_metrics()
    assert metrics["total_runs"] == 3
    assert metrics["success_rate"] == 66.67
    assert metrics["total_tokens_in"] == 1600
    assert metrics["total_tokens_out"] == 2600
    assert metrics["total_cost_usd"] == round(0.0045 + 0.0015 + 0.0003, 6)
    assert metrics["avg_duration_ms"] == round((450 + 200 + 50) / 3, 2)
    assert metrics["total_usd_saved"] == 0.16

    # Get metrics filtered by Project A
    proj_a_metrics = engine.get_aggregated_metrics(project_id="PROJ_A")
    assert proj_a_metrics["total_runs"] == 2
    assert proj_a_metrics["success_rate"] == 50.0

    # Get metrics when empty or unknown project
    empty_metrics = engine.get_aggregated_metrics(project_id="PROJ_UNKNOWN")
    assert empty_metrics["total_runs"] == 0
    assert empty_metrics["success_rate"] == 100.0

# ==========================================
# 6. TEST SUITE: FastMCPKernel (Unified Router)
# ==========================================

def test_kernel_unified_calls():
    kernel = FastMCPKernel(session_store_path=SESSION_STORE, log_path=ACCOUNTING_LOG)
    
    # Pre-register agent to orchestrator for execution tests
    kernel.orchestrator.load_role_manifest("""
    name: test_agent
    role: Tester
    system_instructions: "Run tests."
    """)

    # 1. Tool Call: auth_verify
    res_auth = kernel.call_tool("auth_verify", {"phrase": "погоджую"})
    assert res_auth["success"] is True
    
    res_auth_fail = kernel.call_tool("auth_verify", {"phrase": "wrong"})
    assert res_auth_fail["success"] is False

    # 2. Tool Call: canvas_add_node & canvas_get_view
    res_add = kernel.call_tool("canvas_add_node", {"node_id": "c1", "name": "Auth Dev", "node_type": "AgentNode", "state": "Executing"})
    assert res_add["success"] is True
    assert res_add["node"]["state"] == "Executing"
    
    res_view = kernel.call_tool("canvas_get_view", {})
    assert "c1" in res_view["text_render"]
    assert len(res_view["data"]["nodes"]) == 1

    # 3. Tool Call: execute_safe_task
    res_exec = kernel.call_tool("execute_safe_task", {
        "agent_name": "test_agent",
        "task_query": "verify credentials engine",
        "project_id": "PROJ_X",
        "task_id": "T77",
        "tokens_in": 200,
        "tokens_out": 300,
        "cost_usd": 0.001,
        "duration_ms": 100
    })
    assert res_exec["success"] is True
    assert res_exec["execution"]["status"] == "Success"

    # 4. Tool Call: request_destructive_action & approve_destructive_action
    res_req = kernel.call_tool("request_destructive_action", {"action_type": "db_purge", "target": "users_table", "details": {"all": True}})
    assert res_req["success"] is True
    approval_id = res_req["approval_id"]
    
    res_app = kernel.call_tool("approve_destructive_action", {"approval_id": approval_id, "phrase": "погоджую"})
    assert res_app["success"] is True

    # 5. Tool Call: accounting_get_report
    res_report = kernel.call_tool("accounting_get_report", {"project_id": "PROJ_X"})
    assert res_report["success"] is True
    assert res_report["metrics"]["total_runs"] == 1
    assert res_report["metrics"]["success_rate"] == 100.0

    # Unknown tool handling
    res_unknown = kernel.call_tool("unknown_tool", {})
    assert res_unknown["success"] is False
    assert "Unknown tool" in res_unknown["error"]


def test_uncovered_edge_cases():
    # 1. CanvasEngine node errors and edge renderings
    engine = CanvasEngine()
    engine.add_node("n1", "Node 1", "TaskNode", "Queued")
    engine.add_node("n2", "Node 2", "TaskNode", "Queued")
    engine.add_edge("n1", "n2")

    with pytest.raises(KeyError):
        engine.update_node_state("non_existent", "Done")

    with pytest.raises(ValueError):
        engine.update_node_state("n1", "invalid_state_abc")

    # Render with connections
    render_text = engine.render_canvas_text()
    assert "Blocks: n2" in render_text
    assert "Depends on: n1" in render_text

    # 2. HermesRuntime execute_safely throwing error in action function
    auth = MaksymAuthEngine(session_store_path=SESSION_STORE)
    runtime = HermesRuntime(auth_engine=auth)

    def bad_action():
        raise RuntimeError("Crash during execution")

    def dummy_verify():
        return True

    res = runtime.execute_safely(bad_action, dummy_verify, [])
    assert res["status"] == "Failure"
    assert "Crash during execution" in res["error"]

    # 3. FastMCPKernel call_tool missing agent name or causing unexpected exception
    kernel = FastMCPKernel(session_store_path=SESSION_STORE, log_path=ACCOUNTING_LOG)
    res_missing_agent = kernel.call_tool("execute_safe_task", {
        "agent_name": "non_existent_agent",
        "task_query": "hello"
    })
    assert res_missing_agent["success"] is False
    assert "not registered" in res_missing_agent["error"]

    # Cause generic exception (e.g. arguments is None causing TypeError)
    res_err = kernel.call_tool("auth_verify", None)
    assert res_err["success"] is False
    assert "error" in res_err

    # 4. SwarmOrchestrator empty skills compile context
    orchestrator = SwarmOrchestrator()
    orchestrator.load_role_manifest("""
    name: simple_agent
    role: Tester
    system_instructions: "Tester prompt."
    """)
    prompt = orchestrator.compile_agent_system_instructions("simple_agent", "no matching skills query at all")
    assert prompt == "Tester prompt."

