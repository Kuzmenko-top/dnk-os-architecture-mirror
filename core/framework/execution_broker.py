# --- DNK-MRH-HEADER ---
# mrh_id: "core/framework/execution_broker.py"
# purpose: "Unified Framework Execution Broker mediating between application layer, SwarmDirector, and SwarmControlPlane."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional

from core.orchestrator.control_plane import NodeState, SwarmControlPlane, TaskNode
from core.orchestrator.swarm_director import SwarmDirector, swarm_director

logger = logging.getLogger("dnk.framework.execution_broker")


class ExecutionBroker:
    """
    Unified execution broker providing a high-level orchestration interface
    for application modules, API routers, and background jobs.
    Backwards-compatible, fail-closed, and integrated with SwarmControlPlane.
    """

    def __init__(
        self,
        director: Optional[SwarmDirector] = None,
        control_plane: Optional[SwarmControlPlane] = None,
    ):
        self.director = director or swarm_director
        self.control_plane = control_plane or self.director.control_plane
        self._lock = threading.RLock()
        self._task_history: List[Dict[str, Any]] = []

    def execute_action(
        self,
        agent: str,
        action: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Dict[str, Any]:
        """
        Executes a single domain action on a targeted agent.
        """
        start_time = time.time()
        task_desc = f"Action [{action}] on {agent}"
        full_payload = dict(payload or {})
        full_payload["action"] = action

        try:
            res = self.director.dispatch_task(
                task_description=task_desc,
                preferred_agent=agent,
                parameters=full_payload,
            )
            elapsed = time.time() - start_time
            record = {
                "agent": agent,
                "action": action,
                "status": "success" if res.get("status") != "failed" else "failed",
                "duration": elapsed,
                "timestamp": start_time,
            }
            with self._lock:
                self._task_history.append(record)
            return res
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error("Broker failed executing action %s on %s: %s", action, agent, e)
            record = {
                "agent": agent,
                "action": action,
                "status": "error",
                "error": str(e),
                "duration": elapsed,
                "timestamp": start_time,
            }
            with self._lock:
                self._task_history.append(record)
            return {"status": "error", "error": str(e), "agent": agent, "action": action}

    def execute_batch(
        self,
        tasks: List[Dict[str, Any]],
        parallel: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes a batch of tasks either in parallel or sequentially.
        """
        if parallel:
            return self.director.coordinator.dispatch_parallel(tasks)

        results = []
        for t in tasks:
            agent = t.get("agent") or self.director.route_agent(t.get("task_description", ""))
            action = t.get("action", "run")
            res = self.execute_action(agent=agent, action=action, payload=t.get("payload"))
            results.append(res)

        return {"status": "completed", "total": len(tasks), "results": results}

    def create_dag_pipeline(self, pipeline_id: str) -> "PipelineBuilder":
        """
        Factory for a fluent DAG pipeline builder.
        """
        return PipelineBuilder(pipeline_id=pipeline_id, broker=self)

    def get_telemetry(self) -> Dict[str, Any]:
        """
        Returns runtime execution stats and history overview.
        """
        with self._lock:
            total_tasks = len(self._task_history)
            successful = sum(1 for t in self._task_history if t.get("status") == "success")
            failed = total_tasks - successful
            avg_duration = (
                sum(t.get("duration", 0.0) for t in self._task_history) / max(1, total_tasks)
            )

        return {
            "total_executed": total_tasks,
            "successful": successful,
            "failed": failed,
            "average_duration_seconds": round(avg_duration, 4),
            "control_plane_health": self.director.get_swarm_health(),
        }


class PipelineBuilder:
    """
    Fluent builder for constructing and executing SwarmControlPlane DAGs.
    """

    def __init__(self, pipeline_id: str, broker: ExecutionBroker):
        self.pipeline_id = pipeline_id
        self.broker = broker
        self.cp = SwarmControlPlane()
        self.nodes: List[str] = []

    def step(
        self,
        step_id: str,
        handler: Callable[..., Any],
        depends_on: Optional[List[str]] = None,
        agent_role: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        requires_approval: bool = False,
        max_retries: int = 3,
    ) -> "PipelineBuilder":
        self.cp.add_step(
            step_id=step_id,
            handler=handler,
            depends_on=depends_on,
            requires_approval=requires_approval,
            agent_role=agent_role,
            payload=payload,
            max_retries=max_retries,
        )
        self.nodes.append(step_id)
        return self

    def execute(self) -> Dict[str, Any]:
        """Runs the constructed DAG pipeline and returns structured status."""
        summary = self.cp.execute_graph()
        state = self.cp.get_state()
        return {
            "pipeline_id": self.pipeline_id,
            "run_id": self.cp.run_id,
            "results": summary.get("results", {}),
            "summary": summary,
            "state": state,
        }


# Global canonical execution broker
execution_broker = ExecutionBroker()
