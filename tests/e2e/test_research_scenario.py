# --- DNK-MRH-HEADER ---
# mrh_id: "tests/e2e/test_research_scenario.py"
# purpose: "E2E research & RAG scenario integration tests"
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


class TestResearchScenario:
    """E2E Test suite for research and RAG scenarios."""

    def test_research_scenario(self):
        """Test research scenario with RAG and knowledge base loading."""
        supervisor = DNKSupervisor(name="Antigravity")
        worker = DNKWorker(name="Герич", capabilities=["research", "rag"])

        supervisor.register_worker(
            worker_name="Герич",
            worker_config={"name": "Герич"},
            capabilities=["research", "rag"],
        )
        supervisor.create_state_graph()
        supervisor.compile()

        # Load knowledge base into worker
        documents = [
            "Paris is the capital of France.",
            "Berlin is the capital of Germany.",
            "Tokyo is the capital of Japan.",
        ]
        num_loaded = worker.load_knowledge_base(documents=documents)
        assert num_loaded == 3

        # Execute RAG task via worker
        task_query = "What is the capital of France?"
        rag_res = worker.execute_task(task=task_query, task_type="rag")

        assert "answer" in rag_res
        assert "output" in rag_res
        assert rag_res["status"] == "completed"
        assert "Paris" in rag_res["answer"]

        # Supervisor task delegation
        delegated = supervisor.delegate_task(
            task="Research capital of France",
            thread_id="thread_research_001",
        )
        assert delegated["worker"] == "Герич"
