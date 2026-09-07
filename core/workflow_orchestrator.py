# --- DNK-MRH-HEADER ---
# mrh_id: "core/workflow_orchestrator.py"
# purpose: "WorkflowOrchestrator manages Directed Acyclic Graph (DAG) task execution chains with Human Approval gates, backed by SwarmControlPlane."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Any, Set, Tuple, Callable, Optional
from core.orchestrator.control_plane import SwarmControlPlane, TaskNode, NodeState

class WorkflowNode:
    def __init__(self, step_id: str, handler: Callable[[], Any], depends_on: Optional[List[str]] = None, requires_approval: bool = False):
        self.id = step_id
        self.handler = handler
        self.depends_on = depends_on or []
        self.requires_approval = requires_approval
        self.status = "pending"  # pending, running, completed, failed, paused

class WorkflowOrchestrator:
    """
    Directed Acyclic Graph (DAG) workflow orchestrator for coordinating
    parallel and sequential multi-agent operations with Human-in-the-Loop validation gates.
    Integrated with SwarmControlPlane as the unified state machine backend.
    """
    def __init__(self, control_plane: Optional[SwarmControlPlane] = None):
        self.control_plane = control_plane or SwarmControlPlane()
        self.nodes: Dict[str, WorkflowNode] = {}
        self.approval_granted: Dict[str, bool] = {}

    def add_step(self, step_id: str, handler: Callable[[], Any], depends_on: Optional[List[str]] = None, requires_approval: bool = False) -> None:
        """Registers a new workflow step in the execution DAG and backing Control Plane."""
        node = WorkflowNode(step_id, handler, depends_on, requires_approval)
        self.nodes[step_id] = node
        self.control_plane.add_step(
            step_id=step_id,
            handler=handler,
            depends_on=depends_on,
            requires_approval=requires_approval,
        )

    def grant_approval(self, step_id: str) -> None:
        """Grants human approval for a paused step."""
        self.approval_granted[step_id] = True
        self.control_plane.grant_approval(step_id)
        if step_id in self.nodes and self.nodes[step_id].status == "paused":
            self.nodes[step_id].status = "pending"

    def has_cycle(self) -> bool:
        """Performs DFS via the Control Plane to verify loop-free DAG."""
        return self.control_plane.has_cycle()

    def run_workflow(self) -> Dict[str, Any]:
        """
        Executes the workflow graph following dependency ordering.
        If a step requires human approval and has not been granted, execution pauses.
        """
        if self.has_cycle():
            raise ValueError("Cannot execute workflow: Graph contains a cycle (not a DAG).")

        executed_steps = []
        paused_steps = []
        
        while True:
            runnable_this_iteration = []
            for node_id, node in self.nodes.items():
                if node.status != "pending":
                    continue
                deps_ok = True
                for dep in node.depends_on:
                    if dep not in self.nodes or self.nodes[dep].status != "completed":
                        deps_ok = False
                        break
                if deps_ok:
                    runnable_this_iteration.append(node)

            if not runnable_this_iteration:
                break

            for node in runnable_this_iteration:
                if node.requires_approval and not self.approval_granted.get(node.id, False):
                    node.status = "paused"
                    paused_steps.append(node.id)
                    continue

                node.status = "running"
                try:
                    node.handler()
                    node.status = "completed"
                    executed_steps.append(node.id)
                except Exception:
                    node.status = "failed"
                    raise

        return {
            "executed": executed_steps,
            "paused": paused_steps,
            "status": "paused" if paused_steps else "completed"
        }
