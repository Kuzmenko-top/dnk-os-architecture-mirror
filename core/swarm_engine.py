# --- DNK-MRH-HEADER ---
# mrh_id: "core/swarm_engine.py"
# purpose: "Memory-Aware Worker Execution engine coordinating Supervisor/Worker pipeline under tenant isolation with visual context and error distillation self-healing loops."
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import os
import logging
import uuid
import hashlib
from typing import Any, Callable, Dict, List, Optional

from core.memory.memory_manager import MemoryManager
from core.memory.scones_provider import SCONESMemoryProvider
from core.error_distillation.distiller import ErrorDistiller
from core.orchestrator.control_plane import SwarmControlPlane, TaskNode, NodeState

logger = logging.getLogger(__name__)

class Worker:
    """
    Specialized agentic Worker that executes individual tasks 
    using the provided structured context (which includes retrieved memories, visual context, and self-healing details).
    """
    def __init__(self, worker_id: str, role: str, handler: Callable[[Dict[str, Any], str], Dict[str, Any]]):
        self.id = worker_id
        self.role = role
        self.handler = handler

    def execute(self, task: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Executes the task handler, passing the task details and compiled memory context."""
        try:
            return self.handler(task, context)
        except Exception as e:
            logger.error("Worker %s (%s) execution failed: %s", self.id, self.role, e)
            raise

class Supervisor:
    """
    Supervisor coordinates task execution, performs memory retrieval under tenant 
    isolation, prepares structured context, and manages worker retries with correlation IDs.
    """
    def __init__(
        self,
        supervisor_id: str,
        tenant_id: str,
        workspace_id: str,
        control_plane: Optional[SwarmControlPlane] = None,
    ):
        self.id = supervisor_id
        self.tenant_id = tenant_id
        self.workspace_id = workspace_id
        self.control_plane = control_plane or SwarmControlPlane(tenant_id=tenant_id, workspace_id=workspace_id)
        
        # Initialize the MemoryManager with Gerych's SCONES provider
        self.memory_manager = MemoryManager()
        self.provider = SCONESMemoryProvider()
        self.memory_manager.add_provider(self.provider)
        
        # Set up hermes_home directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Initialize memory context with tenant and workspace isolation!
        self.memory_manager.initialize_all(
            session_id=f"supervisor_session_{self.id}",
            hermes_home=base_dir,
            platform="cli",
            tenant_id=self.tenant_id,
            workspace_id=self.workspace_id
        )

        # Initialize the ErrorDistiller, sharing the MemoryManager connection
        self.distiller = ErrorDistiller(memory_manager=self.memory_manager)

    def execute_task_pipeline(
        self,
        task: Dict[str, Any],
        worker: Worker,
        max_retries: int = 3,
        visual_context_id: Optional[str] = None,
        context_bridge: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Supervisor/Worker pipeline execution flow:
        1. Retrieval: prefetch memories under tenant and workspace isolation boundaries.
        2. Context Preparation: package memories and optional visual contexts inside structured fences.
        3. Worker Execution: execute worker task within the context.
        4. Record Outcome: persist execution results back to memory.
        5. Failures & Distilled Retries: retry on failure using error classifications and self-healing.
        """
        # Generate clean tracking metrics
        correlation_id = str(uuid.uuid4())
        retries_done = 0
        status = "pending"
        error_logs = []

        # Safely bind visual context if provided (DoD Flower 14 compliance)
        if visual_context_id and context_bridge:
            task = context_bridge.bind_to_task_context(
                visual_context_id, task, self.tenant_id, self.workspace_id
            )

        query = task.get("query", "")
        
        # 1. Retrieval Phase (Prefetch under isolated tenant/workspace scope)
        retrieved_memory_context = self.memory_manager.prefetch_all(query)
        
        # 3 & 5. Execution & Retry Loop
        while retries_done < max_retries:
            # 2. Context Preparation (Re-evaluated on retry to capture new self-healing workarounds)
            additional_ctx = task.get("additional_context", "")
            additional_ctx_str = f"\n\n{additional_ctx}" if additional_ctx else ""

            structured_context = (
                f"[Supervisor Context for Worker]\n"
                f"Correlation ID: {correlation_id}\n"
                f"Tenant ID: {self.tenant_id}\n"
                f"Workspace ID: {self.workspace_id}\n"
                f"Role Assignment: {worker.role}\n"
                f"----------------------------------------\n"
                f"{retrieved_memory_context}{additional_ctx_str}\n"
                f"----------------------------------------"
            )

            try:
                logger.info("Supervisor %s: Executing worker %s on task %s (Attempt %d/%d, Correlation ID: %s)",
                            self.id, worker.id, task.get("id"), retries_done + 1, max_retries, correlation_id)
                
                # Execute worker
                execution_result = worker.execute(task, structured_context)
                status = "completed"
                
                # 4. Result Recording (Write outcome back to SCONES store under isolated tenant/workspace)
                outcome_topic = task.get("topic", "task-outcome")
                outcome_summary = f"Task successful under correlation ID {correlation_id}. Result: {execution_result.get('summary', 'No summary')}"
                
                self.memory_manager.handle_tool_call("scones_add_memory", {
                    "topic": outcome_topic,
                    "content": outcome_summary,
                    "importance": 1.2
                })
                
                return {
                    "status": status,
                    "correlation_id": correlation_id,
                    "retries": retries_done,
                    "result": execution_result,
                    "errors": []
                }
                
            except Exception as e:
                # Compute input hash for error event mapping
                input_hash = hashlib.sha256(str(task).encode("utf-8")).hexdigest()
                
                try:
                    # Distill the exception programmatically
                    dist_res = self.distiller.distill_exception(
                        exception=e,
                        task_id=task.get("id", "t_unknown"),
                        execution_id=correlation_id,
                        agent_id=worker.id,
                        tenant_id=self.tenant_id,
                        workspace_id=self.workspace_id,
                        input_hash=input_hash,
                        retry_count=retries_done
                    )
                    
                    retry_eligible = dist_res["retry_eligible"]
                    error_type = dist_res["error_type"]
                    
                    # Self-Healing: inject distilled workaround directly into subsequent retry context
                    workaround = dist_res["distilled_memory"]["workaround"]
                    if workaround:
                        task["additional_context"] = (
                            task.get("additional_context", "") +
                            f"\n\n[Self-Healing Recovery Workaround]\n"
                            f"Previous run hit a known distilled issue (Type: {error_type}).\n"
                            f"Actionable Workaround: {workaround}"
                        )
                except Exception as de:
                    logger.error("Supervisor: Failed to run error distiller: %s", de)
                    retry_eligible = True # Fallback to standard retry
                    error_type = "unknown"

                retries_done += 1
                error_msg = f"Attempt {retries_done} failed: {str(e)} (Type: {error_type})"
                error_logs.append(error_msg)
                logger.warning("Supervisor %s: Attempt %d failed for Correlation ID: %s. Error: %s",
                               self.id, retries_done, correlation_id, e)
                
                # If non-retryable or retries exceeded, stop and fail
                if not retry_eligible or retries_done >= max_retries:
                    status = "failed"
                    break
                else:
                    status = "retry_pending"

        # Return failure output if all retries exceeded or aborted on non-retryable error
        return {
            "status": status,
            "correlation_id": correlation_id,
            "retries": retries_done,
            "result": {},
            "errors": error_logs
        }
