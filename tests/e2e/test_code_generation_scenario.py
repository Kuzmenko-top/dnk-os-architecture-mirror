# --- DNK-MRH-HEADER ---
# mrh_id: "tests/e2e/test_code_generation_scenario.py"
# purpose: "E2E code generation scenario integration tests"
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


class TestCodeGenerationScenario:
    """E2E Test suite for code generation workflows."""

    def test_code_generation_scenario(self):
        """Test code generation scenario through Supervisor and Worker."""
        supervisor = DNKSupervisor(name="Antigravity")
        worker = DNKWorker(name="Герич", capabilities=["code"])

        supervisor.register_worker(
            worker_name="Герич",
            worker_config={"name": "Герич"},
            capabilities=["code"],
        )
        supervisor.create_state_graph()
        supervisor.compile()

        # Delegate code task through supervisor
        task_prompt = "def add_two_numbers(a, b):"
        result = supervisor.delegate_task(
            task=task_prompt,
            selected_worker="Герич",
        )

        assert "output" in result
        assert result["worker"] == "Герич"

        # Direct execution on worker using generation adapter
        worker_output = worker.execute_generation(prompt=task_prompt)
        assert "output" in worker_output
        assert "def add_two_numbers" in task_prompt
        assert worker_output["status"] == "completed"
