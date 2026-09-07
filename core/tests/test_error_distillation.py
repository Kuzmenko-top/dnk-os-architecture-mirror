# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_error_distillation.py"
# purpose: "Unit, integration, and E2E self-healing tests for the Error Distillation Engine (Flower 17)."
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
from datetime import datetime
from core.error_distillation.models import ErrorEvent, DistilledErrorMemory
from core.error_distillation.classifier import ErrorClassifier
from core.error_distillation.fingerprint import ErrorFingerprint
from core.error_distillation.retry_policy import AdaptiveRetryPolicy
from core.error_distillation.distiller import ErrorDistiller
from core.swarm_engine import Worker, Supervisor

TEST_MEM_STORAGE_PATH = "core/tests/scones_distill_test_storage.json"

@pytest.fixture
def clean_storage():
    if os.path.exists(TEST_MEM_STORAGE_PATH):
        os.remove(TEST_MEM_STORAGE_PATH)
    yield TEST_MEM_STORAGE_PATH
    if os.path.exists(TEST_MEM_STORAGE_PATH):
        os.remove(TEST_MEM_STORAGE_PATH)


# --- 1. Unit & Integration Tests (Min 8 required) ---

def test_error_event_and_distilled_memory_schemas():
    """Test 1: Verify ErrorEvent and DistilledErrorMemory Pydantic models initialize correctly."""
    event = ErrorEvent(
        task_id="t-1",
        execution_id="exec-123",
        agent_id="agent_1",
        tenant_id="t_1",
        workspace_id="ws_1",
        error_type="transient",
        error_code=429,
        input_hash="hash-123",
        message="Rate limit exceeded"
    )
    assert event.error_code == 429
    assert isinstance(event.timestamp, datetime)

    memory = DistilledErrorMemory(
        fingerprint="ERR-FPR-abcdef",
        problem="Division by zero",
        root_cause="Math logic failure",
        failed_action="exec",
        workaround="Check denominator",
        tenant_id="t_1",
        workspace_id="ws_1"
    )
    assert memory.fingerprint == "ERR-FPR-abcdef"
    assert memory.occurrence_count == 1

def test_classifier_pattern_mapping():
    """Test 2: Verify ErrorClassifier groups standard exceptions into correct categories with codes."""
    classifier = ErrorClassifier()

    # Transient Rate Limit
    t_type, t_code = classifier.classify(ValueError("Rate limit exceeded 429"))
    assert t_type == "transient"
    assert t_code == 429

    # Transient Timeout
    t_type2, t_code2 = classifier.classify(TimeoutError("Request timed out"))
    assert t_type2 == "transient"
    assert t_code2 == 503

    # Security Violation
    s_type, s_code = classifier.classify(PermissionError("Isolation violation on node"))
    assert s_type == "security"
    assert s_code == 403

    # Logic Error
    l_type, l_code = classifier.classify(ZeroDivisionError("division by zero"))
    assert l_type == "logic"
    assert l_code == 500

    # Dependency Error
    d_type, d_code = classifier.classify(ModuleNotFoundError("No module named 'numpy'"))
    assert d_type == "dependency"
    assert d_code == 500

def test_fingerprint_cleansing():
    """Test 3: Verify that ErrorFingerprint scrubs addresses, numbers, and UUIDs properly."""
    fingerprinter = ErrorFingerprint()
    raw_msg = "Error in connection to 0x7ffd5345 at line 42 with id 12345678-1234-5678-1234-123456781234 in /Users/<username>/file.py"
    
    cleansed = fingerprinter.cleanse_message(raw_msg)
    assert "0x" not in cleansed
    assert "<hex_address>" in cleansed
    assert "42" not in cleansed
    assert "<number>" in cleansed
    assert "<uuid>" in cleansed
    assert "<file_path>" in cleansed

def test_fingerprint_idempotency_matching():
    """Test 4: Verify that exceptions with identical cleansed patterns yield identical fingerprint hashes."""
    fingerprinter = ErrorFingerprint()
    
    exc1 = ValueError("Failed connection to 0x123abc45 at line 12")
    exc2 = ValueError("Failed connection to 0x999def88 at line 34")
    
    fp1 = fingerprinter.generate_fingerprint(exc1)
    fp2 = fingerprinter.generate_fingerprint(exc2)
    
    assert fp1 == fp2 # Fingerprints match because values are cleansed
    
    exc_different = ValueError("Authentication token expired")
    fp_diff = fingerprinter.generate_fingerprint(exc_different)
    assert fp1 != fp_diff

def test_retry_policy_rules():
    """Test 5: Verify AdaptiveRetryPolicy retry permissions and backoff calculations."""
    policy = AdaptiveRetryPolicy(base_delay=1.0, max_delay=10.0)
    
    assert policy.is_retryable("transient") is True
    assert policy.is_retryable("validation") is False
    assert policy.is_retryable("security") is False
    assert policy.is_retryable("logic") is False
    
    # Backoff progression: 1 * 2^0 = 1.0, 1 * 2^1 = 2.0, 1 * 2^2 = 4.0
    assert 1.0 <= policy.calculate_backoff(0) < 1.5
    assert 2.0 <= policy.calculate_backoff(1) < 2.5
    
    # Cap delay
    assert policy.calculate_backoff(10) <= 10.5

def test_distiller_classification_and_fingerprinting(clean_storage):
    """Test 6: Verify ErrorDistiller correctly classifies, fingerprints, and saves a fresh distilled memory."""
    distiller = ErrorDistiller()
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    distiller.memory_manager.initialize_all(
        session_id="test_session",
        hermes_home=base_dir,
        platform="cli",
        tenant_id="tenant_A",
        workspace_id="ws_1"
    )
    distiller.memory_manager.get_provider("scones")._engine.storage_path = clean_storage
    distiller.memory_manager.get_provider("scones")._engine.memories = []
    distiller.memory_manager.get_provider("scones")._engine.save_memories()
    
    exc = ModuleNotFoundError("No module named 'fastmcp'")
    
    res = distiller.distill_exception(
        exception=exc,
        task_id="task_1",
        execution_id="exec_1",
        agent_id="worker_1",
        tenant_id="tenant_A",
        workspace_id="ws_1",
        input_hash="hash-1"
    )
    
    assert res["error_type"] == "dependency"
    assert res["retry_eligible"] is False # Dependencies are non-retryable by default
    assert "ERR-FPR-" in res["fingerprint"]
    
    dist_mem = res["distilled_memory"]
    assert dist_mem["tenant_id"] == "tenant_A"
    assert "fastmcp" in dist_mem["root_cause"]
    assert "Verify dependency registration" in dist_mem["workaround"]

def test_distiller_deduplication_and_occurrences(clean_storage):
    """Test 7: Verify ErrorDistiller correctly increments occurrence_count on duplicate exceptions."""
    distiller = ErrorDistiller()
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    distiller.memory_manager.initialize_all(
        session_id="test_session",
        hermes_home=base_dir,
        platform="cli",
        tenant_id="tenant_A",
        workspace_id="ws_1"
    )
    distiller.memory_manager.get_provider("scones")._engine.storage_path = clean_storage
    distiller.memory_manager.get_provider("scones")._engine.memories = []
    distiller.memory_manager.get_provider("scones")._engine.save_memories()
    
    exc = ValueError("bad format at index 15")
    
    # First occurrence
    res1 = distiller.distill_exception(exc, "task_1", "exec_1", "worker_1", "tenant_A", "ws_1", "hash-1")
    assert res1["distilled_memory"]["occurrence_count"] == 1
    
    # Second occurrence (same error, different index which gets cleansed!)
    exc_dup = ValueError("bad format at index 99")
    res2 = distiller.distill_exception(exc_dup, "task_1", "exec_2", "worker_1", "tenant_A", "ws_1", "hash-1")
    
    assert res2["distilled_memory"]["occurrence_count"] == 2
    assert res2["fingerprint"] == res1["fingerprint"]

def test_distiller_tenant_workspace_isolation(clean_storage):
    """Test 8: Verify strict isolation on distilled error memories between Tenant A and Tenant B."""
    dist_A = ErrorDistiller()
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dist_A.memory_manager.initialize_all(
        session_id="test_session_A",
        hermes_home=base_dir,
        platform="cli",
        tenant_id="tenant_A",
        workspace_id="ws_1"
    )
    dist_A.memory_manager.get_provider("scones")._engine.storage_path = clean_storage
    dist_A.memory_manager.get_provider("scones")._engine.memories = []
    dist_A.memory_manager.get_provider("scones")._engine.save_memories()
    
    dist_B = ErrorDistiller()
    dist_B.memory_manager.initialize_all(
        session_id="test_session_B",
        hermes_home=base_dir,
        platform="cli",
        tenant_id="tenant_B",
        workspace_id="ws_1"
    )
    dist_B.memory_manager.get_provider("scones")._engine.storage_path = clean_storage
    dist_B.memory_manager.get_provider("scones")._engine.load_memories()
    
    exc = TimeoutError("Rate limit exceeded 429")
    
    # Tenant A registers error
    res_A = dist_A.distill_exception(exc, "task_1", "exec_1", "worker_1", "tenant_A", "ws_1", "hash-1")
    assert res_A["distilled_memory"]["occurrence_count"] == 1
    
    # Tenant B registers same error -> must be occurrence 1 (isolated!), not occurrence 2!
    res_B = dist_B.distill_exception(exc, "task_2", "exec_2", "worker_1", "tenant_B", "ws_1", "hash-2")
    assert res_B["distilled_memory"]["occurrence_count"] == 1


# --- 2. End-to-End (E2E) Self-Healing Test ---

def test_e2e_supervisor_worker_distilled_self_healing(clean_storage):
    """
    E2E Test: Verify supervisor/worker closed-loop self-healing workflow.
    First run fails on dependency exception -> classified and workaround distilled to memory.
    Second run automatically pre-retrieves distilled workaround, worker adapts and succeeds!
    """
    supervisor = Supervisor("sup_e2e_distill", tenant_id="tenant_X", workspace_id="ws_main")
    supervisor.provider._engine.storage_path = clean_storage
    supervisor.provider._engine.memories = []
    supervisor.provider._engine.save_memories()
    
    # Define worker that crashes on the first attempt with ModuleNotFoundError,
    # but succeeds on subsequent runs if it sees the workaround in its context
    runs = 0
    workaround_detected_in_worker = False
    
    def worker_handler(task, context):
        nonlocal runs, workaround_detected_in_worker
        runs += 1
        
        # Worker inspects its structured context for self-healing hints
        if "Self-Healing Recovery Workaround" in context and "fastmcp" in context:
            workaround_detected_in_worker = True
            # Worker successfully applies the self-healing workaround and runs cleanly!
            return {"summary": "Applied docker fastmcp library. Server started successfully.", "status": "ok"}
            
        # First attempt: crashes
        raise ModuleNotFoundError("No module named 'fastmcp'")
        
    worker = Worker("e2e_worker", "python-architect", worker_handler)
    
    task1 = {"id": "t_ast_01", "query": "Build FastMCP service integration", "topic": "fastmcp-build"}
    
    # Run 1: Worker crashes immediately on dependency.
    # Distiller intercepts, classifies as 'dependency' (non-retryable), aborts retries, and stores workaround.
    pipeline_res1 = supervisor.execute_task_pipeline(task1, worker, max_retries=3)
    
    assert pipeline_res1["status"] == "failed"
    assert pipeline_res1["retries"] == 1 # Aborted on first fail (dependency is non-retryable!)
    assert "No module named 'fastmcp'" in pipeline_res1["errors"][0]
    
    # Run 2: Re-executing task. Supervisor now retrieves the distilled memory of previous failure
    # and automatically injects the self-healing workaround into the task's context!
    pipeline_res2 = supervisor.execute_task_pipeline(task1, worker, max_retries=3)
    
    assert pipeline_res2["status"] == "completed"
    assert pipeline_res2["result"]["status"] == "ok"
    assert workaround_detected_in_worker is True
    assert "Applied docker fastmcp library" in pipeline_res2["result"]["summary"]
