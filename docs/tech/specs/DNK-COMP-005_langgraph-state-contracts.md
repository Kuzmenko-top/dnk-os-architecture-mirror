# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-005_langgraph-state-contracts.md"
# purpose: "Component Interfaces and State Contracts for LangGraph and MCP Adapters"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

# 🧱 Component Interfaces & Contracts: Stateful Orchestrator (DNK-COMP-005)

This specification defines the strict abstract Python interfaces, contracts, and Pydantic/TypedDict state models for the stateful graph orchestrator and MCP adapters.

## 1. Abstract Interfaces (Hexagonal Ports)

As mandated by **Blueprint v1.1** (Rule 3), all component interfaces are declared using pure abstract Python base classes with `...` placeholders.

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union

class DNKLangGraphPort(ABC):
    """
    Abstract Port for LangGraph-style Stateful multi-agent loops.
    Defines the boundaries for state registration, compilation, node scheduling, and execution.
    """
    @abstractmethod
    def add_node(self, name: str, action: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        """Registers a node executing a computation on the graph state."""
        ...

    @abstractmethod
    def add_edge(self, from_node: str, to_node: str) -> None:
        """Registers a static transition edge from one node to another."""
        ...

    @abstractmethod
    def add_conditional_edges(
        self, 
        source_node: str, 
        router: Callable[[Dict[str, Any]], str], 
        path_map: Dict[str, str]
    ) -> None:
        """Registers a dynamic routing edge driven by a routing evaluation function."""
        ...

    @abstractmethod
    def compile_graph(self) -> None:
        """Validates the graph configuration and compiles the internal runner state."""
        ...

    @abstractmethod
    def execute(self, initial_state: Dict[str, Any], thread_id: str) -> Dict[str, Any]:
        """Runs the stateful loop, checkpointing state across each step."""
        ...


class DNKMCPAdapterPort(ABC):
    """
    Abstract Port for Model Context Protocol (MCP) clients and routing.
    Provides schema translation and tool discovery mappings.
    """
    @abstractmethod
    def register_mcp_server(self, server_name: str, connection_uri: str) -> None:
        """Registers a secure MCP server connection."""
        ...

    @abstractmethod
    def discover_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """Fetches the list of tools exposed by the MCP server and translates schemas."""
        ...

    @abstractmethod
    def execute_tool_call(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Dispatches a tool execution call to the MCP server and returns raw output."""
        ...
```

## 2. State & Payload Contracts

The central shared state uses a strictly typed schema representing a single thread conversation.

### 2.1 State Schema
```python
from typing import TypedDict, Annotated, List

def message_reducer(left: List[Dict[str, Any]], right: Union[List[Dict[str, Any]], Dict[str, Any]]) -> List[Dict[str, Any]]:
    """State reducer for aggregating conversation messages (avoids overwrites)."""
    combined = list(left)
    if isinstance(right, list):
        combined.extend(right)
    else:
        combined.append(right)
    return combined

class StatePayload(TypedDict):
    thread_id: str
    messages: Annotated[List[Dict[str, Any]], message_reducer]
    context_files: List[str]
    tasks_status: Dict[str, str]
    current_node: str
    interrupt_signal: Optional[str]
```
