# --- DNK-MRH-HEADER ---
# mrh_id: "core_adapters_langgraph_crewai_coordinator"
# purpose: "Concrete implementation of AgentCoordinator coordinating LangGraph, crewAI, and TaskQueue with Self-Healing"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import asyncio
from datetime import datetime, UTC
import logging
from threading import Thread
import time
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from core.coordinators.agent_coordinator import AgentCoordinator
from core.models.collaboration import AgentRole, Task, TaskPriority, TaskStatus
from core.models.timeline import Event
from core.queues.task_queue import TaskQueue
from core.adapters.dnk_langgraph_adapter import DNKLangGraphAdapter
from core.adapters.dnk_crewai_adapter import DNKCrewAgent, DNKCrewTask, DNKCrewOrchestrator

logger = logging.getLogger("DNKLangGraphCrewAICoordinator")

class AsyncLoopThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_coro(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

class LangGraphCrewAICoordinator(AgentCoordinator):
    def __init__(self, timeline_repo=None):
        self.roles: Dict[UUID, AgentRole] = {}
        self.retries: Dict[UUID, int] = {}
        self.timeline_repo = timeline_repo
        self.loop_thread = AsyncLoopThread() if timeline_repo else None

    def assign_role(self, agent_id: UUID, role: AgentRole) -> None:
        self.roles[agent_id] = role
        logger.info(f"Assigned role {role} to agent {agent_id}")

    def distribute_tasks(
        self,
        tasks: List[Task],
        agents: List[UUID],
    ) -> Dict[UUID, List[Task]]:
        # Initialize empty lists for all agents
        distribution: Dict[UUID, List[Task]] = {agent_id: [] for agent_id in agents}
        
        if not agents:
            return distribution

        # Group agents by role
        agents_by_role: Dict[AgentRole, List[UUID]] = {}
        for agent_id in agents:
            role = self.roles.get(agent_id)
            if role:
                agents_by_role.setdefault(role, []).append(agent_id)

        # Map task types or payload properties to AgentRole
        type_to_role = {
            "research": AgentRole.RESEARCHER,
            "write": AgentRole.WRITER,
            "validate": AgentRole.VALIDATOR,
            "critic": AgentRole.CRITIC,
            "orchestrate": AgentRole.ORCHESTRATOR
        }

        # Keep track of index for round robin per role
        role_indices: Dict[AgentRole, int] = {}

        # Priority weights for sorting (CRITICAL > HIGH > MEDIUM > LOW)
        priority_weights = {
            TaskPriority.CRITICAL: 4,
            TaskPriority.HIGH: 3,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 1
        }

        # Sort tasks descending by priority weight, then ascending by created_at (FIFO for same priority)
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (priority_weights.get(t.priority, 1), -t.created_at),
            reverse=True
        )

        for task in sorted_tasks:
            required_role = None
            task_type_lower = task.task_type.lower()
            
            # 1. Match based on task_type
            for k, r in type_to_role.items():
                if k in task_type_lower:
                    required_role = r
                    break
            
            # 2. Check payload fallback
            if not required_role:
                role_val = task.payload.get("role")
                if role_val:
                    try:
                        required_role = AgentRole(role_val)
                    except ValueError:
                        pass
            
            # 3. Default fallback
            if not required_role:
                required_role = AgentRole.RESEARCHER

            # Get eligible agents for the required role
            eligible_agents = agents_by_role.get(required_role, [])
            if not eligible_agents:
                # If no agents are registered with this specific role, fallback to any available agent
                eligible_agents = agents

            if eligible_agents:
                idx = role_indices.get(required_role, 0)
                assigned_agent_id = eligible_agents[idx % len(eligible_agents)]
                role_indices[required_role] = idx + 1

                # Update task properties
                task.agent_id = assigned_agent_id
                task.updated_at = int(time.time())
                distribution[assigned_agent_id].append(task)
                logger.info(f"Distributed task {task.id} (type: {task.task_type}) to agent {assigned_agent_id} (role: {required_role})")

        return distribution

    def handle_failures(
        self,
        failed_tasks: List[Task],
    ) -> List[Task]:
        re_run_tasks: List[Task] = []
        max_attempts = 3  # Config value fallback

        for task in failed_tasks:
            # Mark that task has failed first
            self._log_event(task.run_id, task.id, "task_failed", {"error": task.error or "Unknown error"})

            current_retries = self.retries.get(task.id, 0)
            if current_retries < max_attempts:
                # 1. Retry strategy
                new_retries = current_retries + 1
                self.retries[task.id] = new_retries
                
                # Update task to pending
                task.status = TaskStatus.PENDING
                task.error = None
                task.updated_at = int(time.time())
                task.payload["retry_count"] = new_retries
                
                re_run_tasks.append(task)
                self._log_event(task.run_id, task.id, "task_retried", {"attempt": new_retries})
                logger.info(f"Retrying task {task.id}. Attempt {new_retries}/{max_attempts}")
            else:
                # 2. Reassign strategy
                current_agent_id = task.agent_id
                current_role = self.roles.get(current_agent_id)
                
                # Find other agents with same role
                other_agents = [
                    aid for aid, role in self.roles.items()
                    if role == current_role and aid != current_agent_id
                ]

                if other_agents:
                    new_agent_id = other_agents[0]
                    task.agent_id = new_agent_id
                    task.status = TaskStatus.PENDING
                    task.error = None
                    task.updated_at = int(time.time())
                    self.retries[task.id] = 0 # Reset retries for the new agent
                    
                    re_run_tasks.append(task)
                    self._log_event(task.run_id, task.id, "task_reassigned", {
                        "from_agent_id": str(current_agent_id),
                        "to_agent_id": str(new_agent_id),
                        "role": current_role
                    })
                    logger.info(f"Reassigned task {task.id} from agent {current_agent_id} to agent {new_agent_id}")
                else:
                    # 3. Escalate strategy
                    orchestrators = [
                        aid for aid, role in self.roles.items()
                        if role == AgentRole.ORCHESTRATOR
                    ]
                    
                    if orchestrators:
                        orchestrator_id = orchestrators[0]
                        task.agent_id = orchestrator_id
                        task.status = TaskStatus.PENDING
                        task.error = None
                        task.updated_at = int(time.time())
                        self.retries[task.id] = 0
                        
                        re_run_tasks.append(task)
                        self._log_event(task.run_id, task.id, "task_escalated", {
                            "escalated_to": str(orchestrator_id)
                        })
                        logger.info(f"Escalated task {task.id} to orchestrator {orchestrator_id}")
                    else:
                        # Unrecoverable failure
                        task.status = TaskStatus.FAILED
                        logger.warning(f"Task {task.id} failed permanently. No agents or orchestrators available for recovery.")

        return re_run_tasks

    def _log_event(self, run_id: UUID, task_id: Optional[UUID], event_type: str, payload: Dict[str, Any]) -> None:
        event = Event(
            id=uuid4(),
            run_id=run_id,
            task_id=task_id,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(UTC)
        )
        if self.timeline_repo:
            try:
                async def _save():
                    await self.timeline_repo.create_event(event)

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop and loop.is_running():
                    loop.create_task(_save())
                elif self.loop_thread:
                    self.loop_thread.run_coro(_save())
            except Exception as e:
                logger.error(f"Failed to save timeline event: {e}")

    def create_collaboration_graph(self, task_queue: TaskQueue) -> DNKLangGraphAdapter:
        """
        Compiles a LangGraph adapter state graph integrated with crewAI agents.
        """
        adapter = DNKLangGraphAdapter()

        # Group our agents by role to run role-specific handlers
        def create_handler_for_role(role: AgentRole):
            def handler(state: Dict[str, Any]) -> Dict[str, Any]:
                # Find all agent IDs matching this role
                matching_agents = [aid for aid, r in self.roles.items() if r == role]
                if not matching_agents:
                    return {"messages": [f"No active agents for role: {role}"]}
                
                # Check for tasks in queue for each matching agent
                processed_tasks = []
                messages = []
                for agent_id in matching_agents:
                    task = task_queue.dequeue(agent_id)
                    if task:
                        logger.info(f"Agent {agent_id} ({role}) dequeued task {task.id}")
                        try:
                            # Build crewAI persona and execute
                            crew_agent = DNKCrewAgent(
                                role=role.value,
                                goal=task.payload.get("goal", "Accomplish task goals"),
                                backstory=task.payload.get("backstory", "Experienced agent")
                            )
                            # Run task
                            result_str = crew_agent.execute_task(task.task_type, str(task.payload))
                            
                            # Complete task
                            task.status = TaskStatus.COMPLETED
                            task.result = {"output": result_str}
                            task.updated_at = int(time.time())
                            task_queue.enqueue(task)  # re-enqueue to save state

                            processed_tasks.append(task)
                            messages.append(f"[{role.value}] Task {task.id} succeeded: {result_str}")
                        except Exception as e:
                            # Handle fail and invoke self-healing
                            task.status = TaskStatus.FAILED
                            task.error = str(e)
                            task.updated_at = int(time.time())
                            task_queue.enqueue(task)

                            logger.warning(f"Task {task.id} failed in graph node. Triggering self-healing.")
                            re_runs = self.handle_failures([task])
                            for r_task in re_runs:
                                task_queue.enqueue(r_task)
                            
                            messages.append(f"[{role.value}] Task {task.id} failed and self-healed: {e}")

                return {"messages": messages}
            return handler

        # Add nodes for all AgentRoles
        for role in AgentRole:
            adapter.add_node(role.value, create_handler_for_role(role))

        # Wire up a simple pipeline RESEARCHER -> WRITER -> VALIDATOR -> CRITIC -> ORCHESTRATOR -> __end__
        adapter.add_edge("researcher", "writer")
        adapter.add_edge("writer", "validator")
        adapter.add_edge("validator", "critic")
        adapter.add_edge("critic", "orchestrator")
        adapter.add_edge("orchestrator", "__end__")

        adapter.compile_graph()
        return adapter
