# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_swarm_director_and_control_plane_consolidation.py"
# purpose: "Adversarial Quality Gate testing SwarmDirector, SwarmEngineAdapter, and ExecutionBroker consolidation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from typing import Dict, Any

from core.framework.execution_broker import ExecutionBroker, PipelineBuilder
from core.orchestrator.control_plane import NodeState, SwarmControlPlane, TaskNode
from core.orchestrator.swarm_coordinator import GerychSwarmCoordinator
from core.orchestrator.swarm_director import SwarmDirector
from core.swarm.engine_adapter import SwarmEngineAdapter
from core.swarm.quantum_engine import TaskQuantum


class TestSwarmDirector:
    """Verifies authoritative SwarmDirector routing, registry, and execution."""

    def test_singleton_and_initialization(self):
        d1 = SwarmDirector.get_instance()
        d2 = SwarmDirector.get_instance()
        assert d1 is d2
        assert isinstance(d1.control_plane, SwarmControlPlane)
        assert isinstance(d1.coordinator, GerychSwarmCoordinator)
        assert isinstance(d1.engine_adapter, SwarmEngineAdapter)

    def test_routing_across_all_14_agents(self):
        director = SwarmDirector(control_plane=SwarmControlPlane())

        # Test capability matching
        assert director.route_agent("Build a React canvas component with Tailwind") == "gerych_builder"
        assert director.route_agent("Deep AST and GitHub research for SOTA paper") == "gerych_researcher"
        assert director.route_agent("Adversarial security review and vulnerability test gate") == "gerych_auditor"
        assert director.route_agent("FastAPI backend router with SQLAlchemy database models") == "dnk_dev_fullstack"
        assert director.route_agent("Shopify liquid checkout theme and store products") == "dnk_shopify"
        assert director.route_agent("Generate Remotion video animation composition") == "dnk_video_ai_creator"
        assert director.route_agent("Firewall authentication token vault secret") == "dnk_security_guard"
        assert director.route_agent("SCONES memory recall vector retrieval") == "dnk_scones_memory"
        assert director.route_agent("Prometheus metric telemetry dashboard analytics") == "dnk_analytics"
        assert director.route_agent("ERP inventory supply chain order logistics") == "dnk_erp_supply"
        assert director.route_agent("CFO budget revenue pricing cost finance") == "dnk_finance_cfo"
        assert director.route_agent("CMO marketing campaign growth social brand") == "dnk_marketing_cmo"
        assert director.route_agent("Obsidian vault notes markdown documentation librarian") == "herich_librarian"
        assert director.route_agent("Orchestrate general triage and root meta plan") == "gerych_prime"

    def test_preferred_agent_override(self):
        director = SwarmDirector(control_plane=SwarmControlPlane())
        routed = director.route_agent("Build React UI", preferred_agent="dnk_shopify")
        assert routed == "dnk_shopify"

    def test_agent_listing_and_health(self):
        director = SwarmDirector(control_plane=SwarmControlPlane())
        agents = director.list_agents()
        assert len(agents) == 14
        agent_ids = {a["agent_id"] for a in agents}
        assert "gerych_builder" in agent_ids
        assert "dnk_shopify" in agent_ids
        assert "herich_librarian" in agent_ids

        health = director.get_swarm_health()
        assert health["total_agents"] == 14
        assert health["status"] == "HEALTHY"
        assert "control_plane_run_id" in health

    def test_submit_step_and_execute_dag(self):
        cp = SwarmControlPlane()
        director = SwarmDirector(control_plane=cp)

        executed_steps = []

        def step1_handler():
            executed_steps.append("step1")
            return "step1_done"

        def step2_handler():
            executed_steps.append("step2")
            return "step2_done"

        director.submit_step("step1", handler=step1_handler, agent_role="gerych_prime")
        director.submit_step("step2", handler=step2_handler, depends_on=["step1"], agent_role="gerych_builder")

        results = director.execute_dag()
        assert results["step1"] == "step1_done"
        assert results["step2"] == "step2_done"
        assert executed_steps == ["step1", "step2"]


class TestSwarmEngineAdapter:
    """Verifies mapping of TaskQuanta into SwarmControlPlane TaskNodes."""

    def test_quantum_to_task_node_mapping(self):
        adapter = SwarmEngineAdapter()
        q = TaskQuantum(
            quantum_id="q_001",
            title="Create adapter interface",
            target_files=["core/swarm/adapter.py"],
            test_files=["tests/test_adapter.py"],
            instructions="Implement interface and tests",
            dependencies=["q_000"],
            max_retries=2,
        )

        def mock_handler(**kwargs):
            return {"status": "mock_ok"}

        node = adapter.quantum_to_task_node(q, handler_override=mock_handler)
        assert node.node_id == "q_001"
        assert node.depends_on == ["q_000"]
        assert node.max_retries == 2
        assert node.agent_role == "gerych_builder"
        assert node.payload["target_files"] == ["core/swarm/adapter.py"]

    def test_execute_quanta_pipeline_success(self):
        adapter = SwarmEngineAdapter()
        q1 = TaskQuantum(
            quantum_id="q_1",
            title="Step 1",
            target_files=[],
            test_files=[],
            instructions="Do step 1",
        )
        q2 = TaskQuantum(
            quantum_id="q_2",
            title="Step 2",
            target_files=[],
            test_files=[],
            instructions="Do step 2",
            dependencies=["q_1"],
        )

        execution_order = []

        def custom_quantum_to_node(q):
            def handler():
                execution_order.append(q.quantum_id)
                return f"ok_{q.quantum_id}"

            return TaskNode(
                node_id=q.quantum_id,
                handler=handler,
                depends_on=q.dependencies,
            )

        cp = SwarmControlPlane()
        cp.add_node(custom_quantum_to_node(q1))
        cp.add_node(custom_quantum_to_node(q2))

        results = cp.execute_graph()["results"]
        assert results["q_1"] == "ok_q_1"
        assert results["q_2"] == "ok_q_2"
        assert execution_order == ["q_1", "q_2"]


class TestExecutionBroker:
    """Verifies high-level ExecutionBroker fluent builder and action tracking."""

    def test_fluent_dag_pipeline(self):
        broker = ExecutionBroker()
        pipe = broker.create_dag_pipeline("pipeline_test_001")

        call_log = []

        def task_a():
            call_log.append("A")
            return "res_A"

        def task_b():
            call_log.append("B")
            return "res_B"

        pipe.step("A", handler=task_a).step("B", handler=task_b, depends_on=["A"])
        res = pipe.execute()

        assert res["pipeline_id"] == "pipeline_test_001"
        assert res["results"]["A"] == "res_A"
        assert res["results"]["B"] == "res_B"
        assert call_log == ["A", "B"]

    def test_telemetry_tracking(self):
        broker = ExecutionBroker()
        
        # Test mock execution record
        telemetry = broker.get_telemetry()
        assert "total_executed" in telemetry
        assert "successful" in telemetry
        assert "failed" in telemetry
        assert "control_plane_health" in telemetry
