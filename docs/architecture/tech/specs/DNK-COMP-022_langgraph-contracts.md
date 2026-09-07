# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-022_langgraph-contracts.md"
# purpose: "Component Contracts & Interfaces for LangGraph State Machines"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# --- END DNK-MRH-HEADER ---

# 🧩 Component Contracts: LangGraph Interfaces (DNK-COMP-022)

Abstract Python interfaces for building cyclic state graphs, checkpointing, and human-in-the-loop workflows within DNK OS.

---

## 🐍 Python Interface Definitions

```python
# --- DNK-MRH-HEADER ---
# mrh_id: "core/contracts/langgraph_contracts.py"
# purpose: "Abstract contracts for LangGraph state machine integration"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field


class GraphStateSnapshot(BaseModel):
    """Snapshot of graph state at a specific execution step."""
    thread_id: str = Field(description="Unique session or thread identifier")
    step: int = Field(description="Execution step number")
    node_name: str = Field(description="Name of the node executing or completed")
    state_data: Dict[str, Any] = Field(description="State payload at this snapshot")
    next_nodes: List[str] = Field(default_factory=list, description="Pending nodes scheduled for execution")


class DNKCheckpointerPort(ABC):
    """Port for persistent graph state storage."""

    @abstractmethod
    def get_tuple(self, thread_id: str) -> Optional[GraphStateSnapshot]:
        """Fetch the latest state snapshot for a given thread."""
        ...

    @abstractmethod
    def put(self, snapshot: GraphStateSnapshot) -> None:
        """Save a new state snapshot."""
        ...


class DNKStateGraphPort(ABC):
    """Port for configuring cyclic state graphs."""

    @abstractmethod
    def add_node(self, name: str, action: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """Register a node function into the graph."""
        ...

    @abstractmethod
    def add_edge(self, start_key: str, end_key: str) -> None:
        """Add an unconditional directed edge between two nodes."""
        ...

    @abstractmethod
    def add_conditional_edges(self, source: str, path_function: Callable[[Dict[str, Any]], str], path_map: Optional[Dict[str, str]] = None) -> None:
        """Add a dynamic routing edge driven by graph state evaluation."""
        ...

    @abstractmethod
    def compile(self, checkpointer: Optional[DNKCheckpointerPort] = None, interrupt_before: Optional[List[str]] = None) -> "DNKCompiledGraphPort":
        """Compile graph definitions into an executable instance."""
        ...


class DNKCompiledGraphPort(ABC):
    """Port for executing compiled state graphs."""

    @abstractmethod
    def invoke(self, input_state: Dict[str, Any], thread_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute graph from start to completion or interrupt."""
        ...

    @abstractmethod
    def stream(self, input_state: Dict[str, Any], thread_id: Optional[str] = None) -> Any:
        """Stream node execution state updates in real time."""
        ...

    @abstractmethod
    def resume(self, thread_id: str, state_update: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resume execution from an interrupted breakpoint."""
        ...
```
