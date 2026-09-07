# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-006_crewai-interfaces.md"
# purpose: "Component Interfaces and Ports for crewAI-style multi-agent orchestration"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

# 🧱 Component Interfaces & Contracts: crewAI Orchestration (DNK-COMP-006)

This specification defines the strict abstract Python interfaces, contracts, and data structures for role-based agents, task sequences, and crews in DNK OS Core.

## 1. Abstract Interfaces (Hexagonal Ports)

As mandated by **Blueprint v1.1** (Rule 3), all component interfaces are declared using pure abstract Python base classes with `...` placeholders.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable

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
```

## 2. Integration with LangGraph Adapter

Crews compile into standalone execution sub-pipelines.
- To execute a crew as a LangGraph node, the LangGraph adapter node handler can bootstrap and trigger a Crew orchestrator:
```python
def research_node_handler(state: Dict[str, Any]) -> Dict[str, Any]:
    crew = DNKCrewOrchestrator()
    crew.add_agent(scout_agent)
    crew.add_task(research_task)
    result = crew.kickoff()
    return {"messages": [{"role": "assistant", "content": result}]}
```
