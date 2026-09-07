# --- DNK-MRH-HEADER ---
# mrh_id: "core_coordinators_agent_coordinator"
# purpose: "Abstract interface (Port) for multi-agent coordinator"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from uuid import UUID

from core.models.collaboration import AgentRole, Task

class AgentCoordinator(ABC):
    @abstractmethod
    def assign_role(self, agent_id: UUID, role: AgentRole) -> None:
        pass

    @abstractmethod
    def distribute_tasks(
        self,
        tasks: List[Task],
        agents: List[UUID],
    ) -> Dict[UUID, List[Task]]:
        pass

    @abstractmethod
    def handle_failures(
        self,
        failed_tasks: List[Task],
    ) -> List[Task]:
        pass

class ControlPlaneAgentCoordinator(AgentCoordinator):
    """
    Authoritative concrete implementation of AgentCoordinator backed by SwarmControlPlane.
    """
    def __init__(self, control_plane: Optional[Any] = None):
        from core.orchestrator.control_plane import SwarmControlPlane
        self.control_plane = control_plane or SwarmControlPlane()
        self.roles: Dict[UUID, AgentRole] = {}

    def assign_role(self, agent_id: UUID, role: AgentRole) -> None:
        self.roles[agent_id] = role
        self.control_plane.register_role(str(agent_id), {"role": role.value if hasattr(role, "value") else str(role)})

    def distribute_tasks(
        self,
        tasks: List[Task],
        agents: List[UUID],
    ) -> Dict[UUID, List[Task]]:
        distribution: Dict[UUID, List[Task]] = {agent_id: [] for agent_id in agents}
        if not agents:
            return distribution

        for idx, task in enumerate(tasks):
            assigned_agent = agents[idx % len(agents)]
            distribution[assigned_agent].append(task)
            self.control_plane.add_step(
                step_id=str(task.id) if hasattr(task, "id") else f"t_{idx}",
                agent_role=str(self.roles.get(assigned_agent, "worker")),
                payload={"description": getattr(task, "description", "")},
            )
        self.control_plane.checkpoint()
        return distribution

    def handle_failures(
        self,
        failed_tasks: List[Task],
    ) -> List[Task]:
        retryable: List[Task] = []
        for task in failed_tasks:
            retries = getattr(task, "retries", 0)
            max_r = getattr(task, "max_retries", 3)
            if retries < max_r:
                if hasattr(task, "retries"):
                    task.retries += 1
                retryable.append(task)
        self.control_plane.checkpoint()
        return retryable

