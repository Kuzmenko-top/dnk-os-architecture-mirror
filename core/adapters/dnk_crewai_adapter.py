# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/dnk_crewai_adapter.py"
# purpose: "Hexagonal Port & Adapter for crewAI-style role-playing agents, tasks, and sequential crews"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger("DNKCrewAIAdapter")

class DNKCrewAgentPort(ABC):
    """
    Abstract Port representing a Persona-driven Role-Playing Agent.
    """
    @property
    @abstractmethod
    def role(self) -> str:
        ...

    @property
    @abstractmethod
    def goal(self) -> str:
        ...

    @property
    @abstractmethod
    def backstory(self) -> str:
        ...

    @abstractmethod
    def execute_task(self, task_description: str, context: Optional[str] = None) -> str:
        """Executes a task description using the agent's role playing persona."""
        ...


class DNKCrewTaskPort(ABC):
    """
    Abstract Port representing an atomic Task within a Crew pipeline.
    """
    @property
    @abstractmethod
    def description(self) -> str:
        ...

    @property
    @abstractmethod
    def expected_output(self) -> str:
        ...

    @property
    @abstractmethod
    def assigned_agent(self) -> DNKCrewAgentPort:
        ...

    @abstractmethod
    def run(self, context: Optional[str] = None) -> str:
        """Executes the task and returns the result string."""
        ...


class DNKCrewOrchestratorPort(ABC):
    """
    Abstract Port representing a Crew, coordinating agents and tasks sequentially.
    """
    @abstractmethod
    def add_agent(self, agent: DNKCrewAgentPort) -> None:
        ...

    @abstractmethod
    def add_task(self, task: DNKCrewTaskPort) -> None:
        ...

    @abstractmethod
    def kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> str:
        """Launches the sequential pipeline execution flow."""
        ...


class DNKCrewAgent(DNKCrewAgentPort):
    """
    Concrete implementation of a Role-Playing Agent.
    """
    def __init__(self, role: str, goal: str, backstory: str) -> None:
        self._role = role
        self._goal = goal
        self._backstory = backstory

    @property
    def role(self) -> str:
        return self._role

    @property
    def goal(self) -> str:
        return self._goal

    @property
    def backstory(self) -> str:
        return self._backstory

    def execute_task(self, task_description: str, context: Optional[str] = None) -> str:
        logger.info(f"Agent '{self.role}' starts task: {task_description}")
        prompt = (
            f"System: You are playing the role of '{self.role}'. Goal: {self.goal}. Backstory: {self.backstory}\n"
            f"Context: {context or 'None'}\n"
            f"Task: {task_description}"
        )
        # Mock successful execution output reflecting the agent's persona
        result = f"Result of executing '{task_description}' by role '{self.role}': Successfully accomplished goals."
        return result


class DNKCrewTask(DNKCrewTaskPort):
    """
    Concrete implementation of a Pipeline Task.
    """
    def __init__(self, description: str, expected_output: str, agent: DNKCrewAgentPort) -> None:
        self._description = description
        self._expected_output = expected_output
        self._assigned_agent = agent

    @property
    def description(self) -> str:
        return self._description

    @property
    def expected_output(self) -> str:
        return self._expected_output

    @property
    def assigned_agent(self) -> DNKCrewAgentPort:
        return self._assigned_agent

    def run(self, context: Optional[str] = None) -> str:
        logger.info(f"Running Task: {self.description} (Expected: {self.expected_output})")
        return self.assigned_agent.execute_task(self.description, context)


class DNKCrewOrchestrator(DNKCrewOrchestratorPort):
    """
    Concrete implementation of the Crew Pipeline.
    """
    def __init__(self) -> None:
        self._agents: List[DNKCrewAgentPort] = []
        self._tasks: List[DNKCrewTaskPort] = []

    def add_agent(self, agent: DNKCrewAgentPort) -> None:
        self._agents.append(agent)

    def add_task(self, task: DNKCrewTaskPort) -> None:
        self._tasks.append(task)

    def kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> str:
        if not self._tasks:
            raise ValueError("No tasks registered in the crew.")

        context = json_dumps(inputs) if inputs else ""
        step_outputs = []

        # Run sequential pipeline
        for i, task in enumerate(self._tasks):
            logger.info(f"Processing Crew Task {i+1}/{len(self._tasks)}")
            # Pipe accumulated context
            task_context = context
            if step_outputs:
                task_context += "\nPrevious step results:\n" + "\n".join(step_outputs)
            
            output = task.run(task_context)
            step_outputs.append(f"Task {i+1} ({task.description}) Output: {output}")

        final_output = "\n".join(step_outputs)
        logger.info("Crew execution kickoff completed successfully.")
        return final_output

def json_dumps(obj: Any) -> str:
    import json
    return json.dumps(obj)
