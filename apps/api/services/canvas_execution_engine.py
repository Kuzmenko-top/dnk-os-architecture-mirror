# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_canvas_execution_engine"
# purpose: "Graph Execution Engine, Step Runner, and SSE Real-time Streaming for Visual Canvas Workflows (DNK-CANVAS-001 Phase 2)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, AsyncGenerator

from apps.api.schemas.workflow_dag_schemas import (
    WorkflowDAG,
    WorkflowNode,
    WorkflowNodeType,
    NodeExecutionStatus,
    WorkflowExecuteRequest,
    WorkflowExecutionSummary,
    NodeExecutionEvent,
    A2AAgentNodeConfig,
    EventTriggerNodeConfig,
    BatchTaskNodeConfig,
    ShopifyActionNodeConfig,
    HardwareActionNodeConfig
)


class CanvasExecutionEngine:
    """
    Executes Workflow DAGs node-by-node in topological order with real-time SSE streaming,
    A2A agent mesh integration, Batch DAG dispatch, Shopify actions, and ReBurn hardware control.
    """

    def __init__(self):
        self._workflows: Dict[str, WorkflowDAG] = {}
        self._execution_histories: Dict[str, WorkflowExecutionSummary] = {}
        self._execution_event_queues: Dict[str, List[asyncio.Queue]] = {}

    def save_workflow(self, dag: WorkflowDAG) -> WorkflowDAG:
        """Saves or updates a validated WorkflowDAG."""
        self._workflows[dag.id] = dag
        return dag

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDAG]:
        """Retrieves a workflow DAG by its ID."""
        return self._workflows.get(workflow_id)

    def list_workflows(self, workspace_id: Optional[str] = None) -> List[WorkflowDAG]:
        """Lists all workflows, optionally filtered by workspace_id."""
        if workspace_id:
            return [wf for wf in self._workflows.values() if wf.workspace_id == workspace_id]
        return list(self._workflows.values())

    def delete_workflow(self, workflow_id: str) -> bool:
        """Deletes a workflow DAG."""
        if workflow_id in self._workflows:
            del self._workflows[workflow_id]
            return True
        return False

    async def execute_node(
        self,
        node: WorkflowNode,
        context: Dict[str, Any],
        trigger_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a single workflow node based on its specialized type.
        """
        config = node.get_typed_config()

        if node.type == WorkflowNodeType.EVENT_TRIGGER:
            assert isinstance(config, EventTriggerNodeConfig)
            return {
                "triggered": True,
                "stream_topic": config.stream_topic,
                "event_type": config.event_type,
                "payload": trigger_payload or {"source": "manual_or_stream_trigger", "data": context}
            }

        elif node.type == WorkflowNodeType.A2A_AGENT:
            assert isinstance(config, A2AAgentNodeConfig)
            # Simulated A2A mesh invocation
            return {
                "agent_id": config.agent_id,
                "role": config.role,
                "status": "consensus_reached",
                "consensus_score": config.consensus_threshold,
                "response": f"Autonomous agent {config.agent_id} completed task: {config.task_prompt}",
                "artifacts": ["artifact_v1"]
            }

        elif node.type == WorkflowNodeType.BATCH_TASK:
            assert isinstance(config, BatchTaskNodeConfig)
            # Simulated batch task execution
            return {
                "batch_job_type": config.batch_job_type,
                "status": "COMPLETED",
                "processed_items": 100,
                "metrics": {"duration_ms": 120, "retries": 0}
            }

        elif node.type == WorkflowNodeType.SHOPIFY_ACTION:
            assert isinstance(config, ShopifyActionNodeConfig)
            # Simulated Shopify store integration
            return {
                "action": config.action_type,
                "shop_domain": config.shop_domain,
                "result": "success",
                "resource_id": f"gid://shopify/Resource/{uuid.uuid4().hex[:10]}"
            }

        elif node.type == WorkflowNodeType.HARDWARE_ACTION:
            assert isinstance(config, HardwareActionNodeConfig)
            # Simulated ReBurn hardware pin control / sensor ingestion
            return {
                "device_id": config.device_id,
                "action_type": config.action_type,
                "pin": config.pin,
                "hardware_state": "ACK_CONFIRMED",
                "telemetry": {"voltage": 3.3, "temperature_c": 24.5}
            }

        return {"status": "unhandled_node_type"}

    async def execute_workflow(
        self,
        workflow_id: str,
        request: Optional[WorkflowExecuteRequest] = None
    ) -> WorkflowExecutionSummary:
        """
        Executes a workflow DAG in topological dependency order, broadcasting SSE status updates.
        """
        req = request if request is not None else WorkflowExecuteRequest()
        dag = self.get_workflow(workflow_id)
        if not dag:
            raise ValueError(f"Workflow with ID {workflow_id} not found")

        execution_id = f"exec_{uuid.uuid4().hex[:12]}"
        start_time = time.time()
        order = dag.get_topological_order()

        node_map = {n.id: n for n in dag.nodes}
        node_results: Dict[str, Dict[str, Any]] = {}
        context = dict(req.initial_context)
        completed_count = 0
        failed_count = 0

        for node_id in order:
            node = node_map[node_id]
            node.status = NodeExecutionStatus.RUNNING
            await self._broadcast_event(
                workflow_id,
                execution_id,
                NodeExecutionEvent(
                    workflow_id=workflow_id,
                    node_id=node_id,
                    status=NodeExecutionStatus.RUNNING,
                    timestamp=time.time()
                )
            )

            try:
                result = await self.execute_node(
                    node=node,
                    context=context,
                    trigger_payload=req.trigger_event
                )
                node.status = NodeExecutionStatus.COMPLETED
                node.last_output = result
                node.last_error = None
                node_results[node_id] = result
                context[f"node_{node_id}_output"] = result
                completed_count += 1

                await self._broadcast_event(
                    workflow_id,
                    execution_id,
                    NodeExecutionEvent(
                        workflow_id=workflow_id,
                        node_id=node_id,
                        status=NodeExecutionStatus.COMPLETED,
                        output=result,
                        timestamp=time.time()
                    )
                )
            except Exception as e:
                node.status = NodeExecutionStatus.FAILED
                node.last_error = str(e)
                node_results[node_id] = {"error": str(e)}
                failed_count += 1

                await self._broadcast_event(
                    workflow_id,
                    execution_id,
                    NodeExecutionEvent(
                        workflow_id=workflow_id,
                        node_id=node_id,
                        status=NodeExecutionStatus.FAILED,
                        error=str(e),
                        timestamp=time.time()
                    )
                )
                break

        duration = time.time() - start_time
        overall_status = "COMPLETED" if failed_count == 0 else "FAILED"

        summary = WorkflowExecutionSummary(
            workflow_id=workflow_id,
            execution_id=execution_id,
            status=overall_status,
            total_nodes=len(dag.nodes),
            completed_nodes=completed_count,
            failed_nodes=failed_count,
            node_results=node_results,
            execution_duration_sec=round(duration, 4)
        )

        self._execution_histories[execution_id] = summary
        return summary

    async def _broadcast_event(
        self,
        workflow_id: str,
        execution_id: str,
        event: NodeExecutionEvent
    ):
        """Broadcasts event to active SSE subscriber queues for the workflow."""
        channel_key = f"{workflow_id}:{execution_id}"
        queues = self._execution_event_queues.get(channel_key, [])
        for q in queues:
            await q.put(event)

    async def subscribe_execution_stream(
        self,
        workflow_id: str,
        execution_id: str
    ) -> AsyncGenerator[str, None]:
        """
        Async generator yielding SSE data events for real-time frontend canvas updates.
        """
        channel_key = f"{workflow_id}:{execution_id}"
        q: asyncio.Queue = asyncio.Queue()

        if channel_key not in self._execution_event_queues:
            self._execution_event_queues[channel_key] = []
        self._execution_event_queues[channel_key].append(q)

        try:
            while True:
                try:
                    event: NodeExecutionEvent = await asyncio.wait_for(q.get(), timeout=1.0)
                    yield f"data: {json.dumps(event.model_dump())}\n\n"
                    if event.status in [NodeExecutionStatus.COMPLETED, NodeExecutionStatus.FAILED]:
                        # Check if workflow is finished
                        pass
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat
                    yield ": ping\n\n"
        finally:
            if channel_key in self._execution_event_queues:
                if q in self._execution_event_queues[channel_key]:
                    self._execution_event_queues[channel_key].remove(q)
                if not self._execution_event_queues[channel_key]:
                    del self._execution_event_queues[channel_key]


# Singleton default engine instance
_default_canvas_execution_engine = CanvasExecutionEngine()

def get_canvas_execution_engine() -> CanvasExecutionEngine:
    return _default_canvas_execution_engine
