# --- DNK-MRH-HEADER ---
# mrh_id: "core/swarm/engine_adapter.py"
# purpose: "Swarm Engine Adapter bridging Quantum Task Quanta and Subagents with Unified SwarmControlPlane DAG."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from core.orchestrator.control_plane import NodeState, SwarmControlPlane, TaskNode
from core.swarm.quantum_engine import (
    QuantumExecutionResult,
    QuantumSwarmCoordinator,
    TaskQuantum,
)

logger = logging.getLogger("dnk.swarm.engine_adapter")


class SwarmEngineAdapter:
    """
    Adapter between low-level Quantum Swarm execution and authoritative
    DAG state machine in SwarmControlPlane.
    """

    def __init__(
        self,
        control_plane: Optional[SwarmControlPlane] = None,
        coordinator: Optional[QuantumSwarmCoordinator] = None,
    ):
        self.control_plane = control_plane or SwarmControlPlane()
        self.coordinator = coordinator or QuantumSwarmCoordinator()

    def quantum_to_task_node(
        self,
        quantum: TaskQuantum,
        handler_override: Optional[Callable[..., Any]] = None,
    ) -> TaskNode:
        """
        Transforms a TaskQuantum into a SwarmControlPlane TaskNode with identical
        dependencies, retries, and execution handler.
        """
        def default_quantum_handler(**kwargs: Any) -> Dict[str, Any]:
            # Run the synchronous or asynchronous quantum execution
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                # In nested event loop scenarios, execute subagent pipeline synchronously
                res = self.coordinator.builder.execute_quantum(
                    quantum_name=quantum.title,
                    target_files=quantum.target_files,
                    instructions=quantum.instructions,
                    context={"error_summary": quantum.error_summary},
                )
                if not res.success:
                    raise RuntimeError(f"Builder failed: {'; '.join(res.errors)}")
                return {"status": "VERIFIED", "output": res.output}
            else:
                executed = loop.run_until_complete(self.coordinator.execute_quantum(quantum))
                if executed.status != "VERIFIED":
                    raise RuntimeError(f"Quantum {executed.quantum_id} failed: {executed.error_summary}")
                return {"status": "VERIFIED", "artifacts": executed.artifacts}

        node_handler = handler_override or default_quantum_handler

        node = TaskNode(
            node_id=quantum.quantum_id,
            handler=node_handler,
            depends_on=quantum.dependencies,
            requires_approval=False,
            agent_role="gerych_builder",
            payload={
                "title": quantum.title,
                "target_files": quantum.target_files,
                "test_files": quantum.test_files,
                "instructions": quantum.instructions,
            },
            max_retries=quantum.max_retries,
        )
        return node

    def register_quanta_dag(
        self,
        quanta: List[TaskQuantum],
        control_plane: Optional[SwarmControlPlane] = None,
    ) -> SwarmControlPlane:
        """
        Registers a collection of TaskQuanta into the given (or instance) SwarmControlPlane.
        """
        cp = control_plane or self.control_plane
        for q in quanta:
            node = self.quantum_to_task_node(q)
            cp.add_node(node)
        return cp

    def execute_quanta_pipeline(
        self,
        task_id: str,
        quanta: List[TaskQuantum],
    ) -> QuantumExecutionResult:
        """
        Executes a sequence of TaskQuanta via SwarmControlPlane DAG engine,
        producing a standard QuantumExecutionResult.
        """
        cp = SwarmControlPlane()
        self.register_quanta_dag(quanta, control_plane=cp)

        results = cp.execute()
        state = cp.get_state()

        completed = 0
        failed = 0
        timeline: List[Dict[str, Any]] = []
        quanta_dict: Dict[str, TaskQuantum] = {q.quantum_id: q for q in quanta}

        for q in quanta:
            node_info = state["nodes"].get(q.quantum_id, {})
            node_status = node_info.get("status")
            node_err = node_info.get("error")

            if node_status == NodeState.COMPLETED.value:
                q.status = "VERIFIED"
                q.artifacts = results.get(q.quantum_id, {})
                completed += 1
            else:
                q.status = "FAILED"
                q.error_summary = node_err or "DAG node failed or skipped"
                failed += 1

            timeline.append({
                "quantum_id": q.quantum_id,
                "status": q.status,
                "error": q.error_summary,
            })

        overall_status = "SUCCESS" if failed == 0 else ("PARTIAL" if completed > 0 else "FAILED")

        return QuantumExecutionResult(
            task_id=task_id,
            total_quanta=len(quanta),
            completed_quanta=completed,
            failed_quanta=failed,
            overall_status=overall_status,
            execution_timeline=timeline,
            quanta_results=quanta_dict,
        )
