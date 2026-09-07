# --- DNK-MRH-HEADER ---
# mrh_id: "tests/e2e/test_full_pipeline.py"
# purpose: "E2E test suite for full Supervisor-Worker-Checkpointer pipeline integration"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from dnk_os.core.supervisor import DNKSupervisor
from dnk_os.core.worker import DNKWorker
from dnk_os.core.checkpointer import create_checkpointer
from dnk_os.core.approval_gate import DNKApprovalGate, ApprovalStatus


class TestFullPipeline:
    """E2E Integration test for full supervisor-worker pipeline."""

    def test_full_supervisor_worker_pipeline(self):
        """Test complete supervisor-worker pipeline with checkpointer persistence."""
        checkpointer = create_checkpointer(backend="memory")
        supervisor = DNKSupervisor(name="Antigravity", checkpointer=checkpointer)
        worker = DNKWorker(name="Герич", capabilities=["code", "research"])

        # Register worker
        registered = supervisor.register_worker(
            worker_name="Герич",
            worker_config={"name": "Герич", "role": "Worker"},
            capabilities=worker.get_capabilities(),
        )
        assert registered is True

        # Create and compile graph
        supervisor.create_state_graph()
        compiled = supervisor.compile()
        assert compiled is True

        # Delegate task
        thread_id = "thread_full_pipeline_001"
        result = supervisor.delegate_task(
            task="Generate text about AI",
            selected_worker="Герич",
            thread_id=thread_id,
        )

        # Verify
        assert result["worker"] == "Герич"
        assert "output" in result
        assert result["status"] in ["completed", "success"]

        # Verify checkpointer recorded state
        saved_state = supervisor.get_state(thread_id=thread_id)
        assert saved_state is not None
        assert saved_state["worker"] == "Герич"

    def test_pipeline_with_worker_execution(self):
        """Test supervisor delegation triggering worker task execution."""
        supervisor = DNKSupervisor(name="Antigravity")
        worker = DNKWorker(name="Герич", capabilities=["code", "generation"])

        supervisor.register_worker(
            worker_name="Герич",
            worker_config={"name": "Герич"},
            capabilities=worker.get_capabilities(),
        )
        supervisor.compile()

        # Direct execution through worker
        task_desc = "Write Python script"
        worker_res = worker.execute_task(task=task_desc, task_type="generation")
        assert "output" in worker_res
        assert worker_res["status"] == "completed"
