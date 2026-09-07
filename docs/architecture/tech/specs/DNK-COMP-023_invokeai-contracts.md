# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-023_invokeai-contracts.md"
# purpose: "Component Contracts & Interfaces for InvokeAI Invocations Graph Engine"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

# 🧩 Component Contracts: InvokeAI Invocations & Canvas Ports (DNK-COMP-023)

Abstract Python interfaces and Pydantic schemas for building generative DAG invocations, model management, and canvas bridging in DNK OS.

---

## 🐍 Python Interface Definitions

```python
# --- DNK-MRH-HEADER ---
# mrh_id: "core/contracts/invokeai_contracts.py"
# purpose: "Abstract contracts for InvokeAI generative DAG invoker integration"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class ImageFieldDTO(BaseModel):
    """Reference to an image asset with dimensions and storage URI."""
    image_name: str
    image_url: Optional[str] = None
    width: int = 512
    height: int = 512
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LatentsFieldDTO(BaseModel):
    """Reference to cached or generated tensor latents."""
    latents_name: str
    seed: int
    width: int = 512
    height: int = 512


class InvocationNodeDTO(BaseModel):
    """Discrete node in the generation graph."""
    id: str
    type: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, executing, completed, failed


class InvocationEdgeDTO(BaseModel):
    """Directed connection between node output and node input."""
    source_node_id: str
    source_field: str
    target_node_id: str
    target_field: str


class GenerationGraphDTO(BaseModel):
    """Complete invocations DAG payload."""
    graph_id: str
    nodes: Dict[str, InvocationNodeDTO] = Field(default_factory=dict)
    edges: List[InvocationEdgeDTO] = Field(default_factory=list)


class DNKInvocationPort(ABC):
    """Port for executing discrete generative operations."""

    @abstractmethod
    def get_invocation_type(self) -> str:
        """Return the unique string identifier of this invocation type."""
        ...

    @abstractmethod
    def execute(self, inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute node logic and produce output fields."""
        ...


class DNKGraphExecutionEnginePort(ABC):
    """Port for scheduling and evaluating full generation DAGs."""

    @abstractmethod
    def add_node(self, node: InvocationNodeDTO) -> None:
        """Add an invocation node to the current graph."""
        ...

    @abstractmethod
    def add_edge(self, edge: InvocationEdgeDTO) -> None:
        """Connect output of source node to input of target node."""
        ...

    @abstractmethod
    def execute_graph(self, graph: GenerationGraphDTO, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute full DAG in topological order and return materialised outputs."""
        ...


class DNKModelManagerPort(ABC):
    """Port for discovering, loading, and offloading diffusion models."""

    @abstractmethod
    def list_models(self) -> List[Dict[str, Any]]:
        """List registered checkpoints, LoRAs, and ControlNets."""
        ...

    @abstractmethod
    def load_model(self, model_key: str, device: str = "mps") -> Any:
        """Load and cache model weights onto target hardware accelerator."""
        ...
```
