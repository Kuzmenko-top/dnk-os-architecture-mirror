# --- DNK-MRH-HEADER ---
# mrh_id: "tests/test_swarm_control_plane.py"
# purpose: "Comprehensive test suite for Unified Swarm Control Plane, DAG State Machine, Checkpointing, and Facade Consolidation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
import os
import tempfile
from uuid import uuid4
from core.orchestrator.control_plane import SwarmControlPlane, TaskNode, NodeState
from core.workflow_orchestrator import WorkflowOrchestrator
from core.swarm_orchestrator import SwarmOrchestrator
from core.swarm_engine import Supervisor, Worker
from core.coordinators.agent_coordinator import ControlPlaneAgentCoordinator
from core.models.collaboration import AgentRole, Task, TaskPriority, TaskStatus

def test_control_plane_dag_execution():
    cp = SwarmControlPlane()
    execution_order = []

    def step_a():
        execution_order.append("A")
        return "result_a"

    def step_b():
        execution_order.append("B")
        return "result_b"

    def step_c():
        execution_order.append("C")
        return "result_c"

    cp.add_step("step_a", handler=step_a)
    cp.add_step("step_b", handler=step_b, depends_on=["step_a"])
    cp.add_step("step_c", handler=step_c, depends_on=["step_b"])

    assert not cp.has_cycle()
    results = cp.execute_dag()

    assert execution_order == ["A", "B", "C"]
    assert results["step_a"]["status"] == NodeState.COMPLETED
    assert results["step_b"]["status"] == NodeState.COMPLETED
    assert results["step_c"]["status"] == NodeState.COMPLETED
    assert results["step_c"]["result"] == "result_c"

def test_control_plane_cycle_detection():
    cp = SwarmControlPlane()
    cp.add_step("node_1", depends_on=["node_2"])
    cp.add_step("node_2", depends_on=["node_3"])
    cp.add_step("node_3", depends_on=["node_1"])

    assert cp.has_cycle() is True
    with pytest.raises(ValueError, match="circular dependency cycle"):
        cp.execute_dag()

def test_control_plane_human_approval_gate():
    cp = SwarmControlPlane()
    executed = []

    def safe_step():
        executed.append("safe")

    def dangerous_step():
        executed.append("dangerous")

    cp.add_step("step_1", handler=safe_step)
    cp.add_step("step_2", handler=dangerous_step, depends_on=["step_1"], requires_approval=True)

    # First run without approval
    res = cp.execute_dag()
    assert executed == ["safe"]
    assert cp.nodes["step_2"].status == NodeState.PAUSED_APPROVAL

    # Grant approval and resume
    cp.grant_approval("step_2")
    res_after = cp.execute_dag()
    assert executed == ["safe", "dangerous"]
    assert cp.nodes["step_2"].status == NodeState.COMPLETED

def test_control_plane_checkpoint_persistence():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        chk_path = f.name

    try:
        cp = SwarmControlPlane(checkpoint_path=chk_path)
        cp.add_step("step_1", handler=lambda: "done_1")
        cp.execute_dag()
        assert os.path.exists(chk_path)

        # Restore in a fresh instance
        restored_cp = SwarmControlPlane(checkpoint_path=chk_path)
        ok = restored_cp.restore_checkpoint(cp.run_id)
        assert ok is True
        assert "step_1" in restored_cp.nodes
        assert restored_cp.nodes["step_1"].status == NodeState.COMPLETED
        assert restored_cp.nodes["step_1"].result == "done_1"
    finally:
        if os.path.exists(chk_path):
            os.remove(chk_path)

def test_control_plane_rag_skills_latency():
    cp = SwarmControlPlane()
    cp.register_skill("git_hygiene", "Best practices for clean commits", "Always commit atomically.")
    cp.register_skill("liquid_engine", "Shopify Liquid AST rules", "Ensure balanced schema tags.")

    matches, duration = cp.inject_skills_rag("gerych_builder", "liquid template error", limit=1)
    assert len(matches) == 1
    assert matches[0]["name"] == "liquid_engine"
    assert duration < 0.05  # Latency under 50ms invariant

def test_workflow_orchestrator_facade():
    wo = WorkflowOrchestrator()
    calls = []
    wo.add_step("init", lambda: calls.append("init"))
    wo.add_step("build", lambda: calls.append("build"), depends_on=["init"])
    res = wo.run_workflow()
    assert calls == ["init", "build"]
    assert res["status"] == "completed"

def test_swarm_orchestrator_facade():
    so = SwarmOrchestrator()
    manifest = """
name: test_agent
role: tester
system_instructions: You are a tester.
"""
    loaded = so.load_role_manifest(manifest)
    assert loaded["name"] == "test_agent"
    so.register_skill("test_skill", "testing skill", "Test thoroughly.")
    prompt = so.compile_agent_system_instructions("test_agent", "testing query")
    assert "test_skill" in prompt

def test_control_plane_agent_coordinator_facade():
    coordinator = ControlPlaneAgentCoordinator()
    agent_id = uuid4()
    task = Task(
        id=uuid4(),
        run_id=uuid4(),
        agent_id=agent_id,
        task_type="analysis",
        priority=TaskPriority.HIGH,
        status=TaskStatus.PENDING,
        created_at=1000,
        updated_at=1000,
        payload={"description": "Analyze PR"}
    )
    
    coordinator.assign_role(agent_id, AgentRole.RESEARCHER)
    distribution = coordinator.distribute_tasks([task], [agent_id])
    assert len(distribution[agent_id]) == 1
    assert distribution[agent_id][0].id == task.id

def test_supervisor_control_plane_integration():
    supervisor = Supervisor(supervisor_id="test_sup", tenant_id="tenant_x", workspace_id="ws-alpha-001")
    assert supervisor.control_plane is not None
    assert supervisor.control_plane.tenant_id == "tenant_x"
    assert supervisor.control_plane.workspace_id == "ws-alpha-001"
