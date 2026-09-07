# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-020_crewai-contracts.md"
# purpose: "Component Interfaces and Abstract Contracts for crewAI Framework Assimilation"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

# 🧩 COMPONENT CONTRACTS: CREWAI INTERFACES (DNK-COMP-020)

Abstract Python contracts (`abc.ABC`) defining type-safe interface boundaries for crewAI agents, tasks, processes, and memory components.

---

## 📐 Base Data Structures & Enums

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional, Sequence, Union

class ProcessType(str, Enum):
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"


class CrewOutput:
    """Payload returned upon Crew execution completion."""
    def __init__(
        self,
        raw: str,
        pydantic: Optional[Any] = None,
        json_dict: Optional[Dict[str, Any]] = None,
        tasks_output: Optional[List[Any]] = None,
        token_usage: Optional[Dict[str, int]] = None
    ) -> None:
        self.raw = raw
        self.pydantic = pydantic
        self.json_dict = json_dict
        self.tasks_output = tasks_output or []
        self.token_usage = token_usage or {}
```

---

## 🛠️ Abstract Component Interfaces

```python
class BaseAgent(ABC):
    """Abstract Role-Based Agent contract."""
    role: str
    goal: str
    backstory: str
    allow_delegation: bool

    @abstractmethod
    def execute_task(
        self,
        task_description: str,
        context: Optional[str] = None,
        tools: Optional[List[Any]] = None
    ) -> str:
        """Executes assigned task using prompt persona and toolset."""
        ...


class BaseTask(ABC):
    """Abstract Task definition contract."""
    description: str
    expected_output: str
    agent: Optional[BaseAgent]

    @abstractmethod
    def execute(self, context: Optional[str] = None) -> str:
        """Executes task with optional upstream context injection."""
        ...


class BaseMemoryStore(ABC):
    """Abstract Multi-Layer Memory Store contract."""

    @abstractmethod
    def save(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Saves entry into short/long-term memory store."""
        ...

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Retrieves relevant memory items via vector or key search."""
        ...


class BaseCrew(ABC):
    """Abstract Multi-Agent Crew Container contract."""

    @abstractmethod
    def kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> CrewOutput:
        """Executes all crew tasks according to configured ProcessType."""
        ...

    @abstractmethod
    def kickoff_async(self, inputs: Optional[Dict[str, Any]] = None) -> Any:
        """Asynchronously triggers crew task execution."""
        ...
```
