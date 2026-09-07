# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_agent.py"
# purpose: "Test suite for DNKAgent supervisor, worker, checkpointer & HITL approval gate integration"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
Unit tests for DNKAgent.
"""

import pytest
from dnk_os.core.agent import DNKAgent
from dnk_os.core.approval_gate import ApprovalStatus


class TestDNKAgent:
    """Test suite for DNKAgent orchestration."""

    def test_init_and_execution(self):
        """Test agent initialization and supervisor task delegation."""
        agent = DNKAgent()
        assert agent.supervisor is not None
        assert agent.worker is not None
        assert agent.approval_gate is not None
        
        result = agent.execute_task(task="Analyze data", thread_id="t1")
        assert result["status"] == "completed"
        assert result["worker"] == "Герич"

    def test_execute_worker_direct(self):
        """Test direct worker task execution."""
        agent = DNKAgent()
        result = agent.execute_worker_direct(task="Generate summary report", task_type="generation")
        assert result["status"] == "completed"
        assert "output" in result

    def test_state_persistence(self):
        """Test state retrieval from checkpointer."""
        agent = DNKAgent()
        agent.checkpointer.put(thread_id="t1", checkpoint={"step": "complete"})
        state = agent.get_state(thread_id="t1")
        assert state is not None
        assert state["step"] == "complete"

    def test_execute_sensitive_action(self):
        """Test execute sensitive action with approval gate."""
        agent = DNKAgent()

        def sensitive_op():
            return {"deleted": True}

        result = agent.execute_sensitive_action(
            action="delete_agent",
            action_function=sensitive_op,
            context={"agent": "Герич"},
            thread_id="t1",
            auto_approve_actions=["delete_agent"]
        )
        assert result["status"] == "success"
        assert result["approval_status"] == ApprovalStatus.APPROVED
        assert result["output"] == {"deleted": True}
