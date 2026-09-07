# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_swarm_engine.py"
# purpose: "Unit, integration, and E2E tests for memory-aware worker execution and tenant isolation."
# author: "Maxim"
# license: "DNK-INTERNAL"
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
from core.swarm_engine import Worker, Supervisor

TEST_STORAGE_PATH = "core/tests/scones_swarm_test_storage.json"

@pytest.fixture
def clean_storage():
    if os.path.exists(TEST_STORAGE_PATH):
        os.remove(TEST_STORAGE_PATH)
    yield TEST_STORAGE_PATH
    if os.path.exists(TEST_STORAGE_PATH):
        os.remove(TEST_STORAGE_PATH)

# --- 1. Unit/Integration Tests ---

def test_worker_execution_success():
    """Unit test: Verify that a Worker executes successfully and returns its handler's output."""
    def mock_handler(task, context):
        return {"summary": f"Executed: {task['name']}", "data": "test"}
        
    worker = Worker("worker_1", "tester", mock_handler)
    task = {"name": "Audit AST"}
    res = worker.execute(task, "Test Context")
    
    assert res["summary"] == "Executed: Audit AST"
    assert res["data"] == "test"

def test_supervisor_initialization(clean_storage):
    """Integration test: Verify Supervisor is initialized with correct tenant/workspace parameters."""
    supervisor = Supervisor("sup_1", tenant_id="tenant_A", workspace_id="workspace_alpha")
    supervisor.provider._engine.storage_path = clean_storage
    supervisor.provider._engine.memories = []
    supervisor.provider._engine.save_memories()
    
    assert supervisor.tenant_id == "tenant_A"
    assert supervisor.workspace_id == "workspace_alpha"
    assert supervisor.provider._tenant_id == "tenant_A"
    assert supervisor.provider._workspace_id == "workspace_alpha"

def test_supervisor_memory_retrieval(clean_storage):
    """Integration test: Verify Supervisor pre-execution retrieval phase pulls memories."""
    supervisor = Supervisor("sup_1", tenant_id="tenant_A", workspace_id="workspace_alpha")
    supervisor.provider._engine.storage_path = clean_storage
    supervisor.provider._engine.memories = []
    
    # Add memory inside tenant_A scope
    supervisor.provider._engine.add_memory(
        "git", "All branches must be synced.", importance=1.0, 
        metadata={"tenant_id": "tenant_A", "workspace_id": "workspace_alpha"}
    )
    
    task = {"id": "t1", "query": "Need details about git branches"}
    retrieved = supervisor.memory_manager.prefetch_all(task["query"])
    
    assert "recalled memory context" in retrieved.lower()
    assert "All branches must be synced" in retrieved

def test_supervisor_retry_mechanism_and_status(clean_storage):
    """Integration test: Verify retry loop limits, logs errors, and sets correct statuses with correlation IDs."""
    supervisor = Supervisor("sup_1", tenant_id="tenant_A", workspace_id="workspace_alpha")
    supervisor.provider._engine.storage_path = clean_storage
    supervisor.provider._engine.memories = []
    supervisor.provider._engine.save_memories()
    
    attempts = 0
    def failing_handler(task, context):
        nonlocal attempts
        attempts += 1
        raise TimeoutError(f"Failing on attempt {attempts} (Rate limit exceeded 429)")
        
    worker = Worker("fail_worker", "tester", failing_handler)
    task = {"id": "task_fail", "query": "Test error handling", "topic": "error-handling"}
    
    res = supervisor.execute_task_pipeline(task, worker, max_retries=3)
    
    assert res["status"] == "failed"
    assert len(res["errors"]) == 3
    assert res["retries"] == 3
    assert "correlation_id" in res
    assert attempts == 3
    
    # Verify that error episodes are logged and deduplicated inside scones store by our distiller
    fingerprint = supervisor.distiller.fingerprinter.generate_fingerprint(TimeoutError("Failing on attempt 1 (Rate limit exceeded 429)"))
    errors_recorded = supervisor.provider._engine.get_memories(topic=f"distilled-error-{fingerprint}")
    assert len(errors_recorded) == 1
    # Retrieve nested JSON and verify occurrences
    parsed = json.loads(errors_recorded[0]["content"])
    assert parsed["occurrence_count"] == 3
    assert "Failing on attempt 1" in errors_recorded[0]["content"]

def test_supervisor_tenant_workspace_isolation(clean_storage):
    """Integration test: Verify absolute memory isolation between tenant_A and tenant_B."""
    # Setup shared SCONES storage file
    sup_A = Supervisor("sup_A", tenant_id="tenant_A", workspace_id="workspace_1")
    sup_A.provider._engine.storage_path = clean_storage
    sup_A.provider._engine.memories = []
    sup_A.provider._engine.save_memories()
    
    sup_B = Supervisor("sup_B", tenant_id="tenant_B", workspace_id="workspace_1")
    sup_B.provider._engine.storage_path = clean_storage
    sup_B.provider._engine.load_memories() # Loads sup_A's storage
    
    # sup_A writes a memory
    sup_A.memory_manager.handle_tool_call("scones_add_memory", {
        "topic": "security",
        "content": "Secret API keys are encrypted."
    })
    
    # sup_A queries it -> should find it
    context_A = sup_A.memory_manager.prefetch_all("API security keys")
    assert "Secret API keys are encrypted" in context_A
    
    # sup_B queries it -> should NOT find it (tenant isolation)
    context_B = sup_B.memory_manager.prefetch_all("API security keys")
    assert "Secret API keys are encrypted" not in context_B


# --- 2. End-to-End (E2E) Test ---

def test_e2e_supervisor_worker_memory_loop(clean_storage):
    """
    End-to-End test: Verify complete supervisor/worker loop.
    Task 1 execution outcome is saved to memory, and Task 2 execution
    automatically retrieves and leverages Task 1's outcome within the context.
    """
    # 1. Setup Supervisor for Tenant 1
    supervisor_T1 = Supervisor("supervisor_T1", tenant_id="tenant_1", workspace_id="ws_main")
    supervisor_T1.provider._engine.storage_path = clean_storage
    supervisor_T1.provider._engine.memories = []
    supervisor_T1.provider._engine.save_memories()
    
    # 2. Run Task 1 (Saves custom outcome)
    def task1_handler(task, context):
        return {"summary": "Completed AST analysis of dnk-core.", "status": "ok"}
        
    worker_1 = Worker("worker_1", "ast-scout", task1_handler)
    task1 = {"id": "t1", "topic": "ast-report", "query": "Scan core folder"}
    
    res1 = supervisor_T1.execute_task_pipeline(task1, worker_1)
    assert res1["status"] == "completed"
    
    # 3. Setup Task 2 which depends on the output of Task 1
    received_context_for_task2 = None
    def task2_handler(task, context):
        nonlocal received_context_for_task2
        received_context_for_task2 = context
        return {"summary": "Built code map based on AST report.", "status": "ok"}
        
    worker_2 = Worker("worker_2", "map-maker", task2_handler)
    task2 = {"id": "t2", "topic": "code-mapping", "query": "Generate code map using past ast-report details"}
    
    # 4. Run Task 2 -> must automatically perform retrieval and fetch Task 1's outcome
    res2 = supervisor_T1.execute_task_pipeline(task2, worker_2)
    assert res2["status"] == "completed"
    
    # Verify Task 2 received Task 1's outcome in its context!
    assert received_context_for_task2 is not None
    assert "Completed AST analysis of dnk-core" in received_context_for_task2
    
    # 5. Setup Supervisor for Tenant 2 -> must NOT retrieve Tenant 1's memory
    supervisor_T2 = Supervisor("supervisor_T2", tenant_id="tenant_2", workspace_id="ws_main")
    supervisor_T2.provider._engine.storage_path = clean_storage
    supervisor_T2.provider._engine.load_memories()
    
    received_context_for_task2_T2 = None
    def task2_handler_T2(task, context):
        nonlocal received_context_for_task2_T2
        received_context_for_task2_T2 = context
        return {"summary": "Attempt mapping.", "status": "ok"}
        
    worker_2_T2 = Worker("worker_2_T2", "map-maker", task2_handler_T2)
    
    res2_T2 = supervisor_T2.execute_task_pipeline(task2, worker_2_T2)
    assert res2_T2["status"] == "completed"
    
    # Confirm Tenant 2's worker received clean context without Tenant 1's AST report
    assert received_context_for_task2_T2 is not None
    assert "Completed AST analysis of dnk-core" not in received_context_for_task2_T2
