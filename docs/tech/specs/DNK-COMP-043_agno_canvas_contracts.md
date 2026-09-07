# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-043_agno_canvas_contracts.md"
# purpose: "Component Contracts & Pydantic DTOs for Agno Canvas Node Execution in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-CANVAS-AGNO-CONTRACTS"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# 📜 DNK-COMP-043: Agno Infinite Canvas Component Contracts

## 1. Domain Entities & Enums

### 1.1 Canvas Node Execution State
```python
from enum import Enum

class CanvasNodeStatus(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED_HITL = "paused_hitl"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class AgnoTeamMode(str, Enum):
    ROUTE = "route"
    BROADCAST = "broadcast"
    TASKS = "tasks"
    CONSENSUS = "consensus"

class WorkflowStepType(str, Enum):
    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"
```

---

## 2. Pydantic DTO Specifications

### 2.1 Spatial Canvas Node DTO
```python
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class CanvasNodeConfig(BaseModel):
    node_id: str
    node_type: str  # "agent", "team", "workflow_step", "memory", "hitl_gate", "tool"
    title: str
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    agent_name: Optional[str] = None
    model_id: Optional[str] = "gemini-2.5-pro"
    instructions: Optional[str] = None
    team_mode: Optional[AgnoTeamMode] = AgnoTeamMode.ROUTE
    member_agents: List[str] = Field(default_factory=list)
    tools: List[str] = Field(default_factory=list)
    requires_hitl: bool = False
    hitl_threshold_tokens: Optional[int] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    memory_workspace: Optional[str] = "ws-alpha-001"
```

### 2.2 Connection Edge DTO
```python
class CanvasEdge(BaseModel):
    edge_id: str
    source_node_id: str
    source_port: str = "output"
    target_node_id: str
    target_port: str = "input"
    condition_expr: Optional[str] = None
```

### 2.3 Canvas Execution Graph DTO
```python
class CanvasGraphPayload(BaseModel):
    graph_id: str
    workspace_id: str = "ws-alpha-001"
    nodes: List[CanvasNodeConfig]
    edges: List[CanvasEdge]
    initial_inputs: Dict[str, Any] = Field(default_factory=dict)
```

### 2.4 HITL Verification & Checkpoint DTO
```python
class HITLCheckpoint(BaseModel):
    checkpoint_id: str
    graph_id: str
    node_id: str
    paused_at_timestamp: float
    reason: str
    pending_action: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    state_snapshot: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # "pending", "approved", "rejected"
    user_feedback: Optional[str] = None

class HITLResolutionRequest(BaseModel):
    checkpoint_id: str
    decision: str  # "approve" | "reject"
    modified_parameters: Optional[Dict[str, Any]] = None
    user_comment: Optional[str] = None
```

### 2.5 Execution Output DTO
```python
class NodeExecutionResult(BaseModel):
    node_id: str
    status: CanvasNodeStatus
    output_data: Optional[Dict[str, Any]] = None
    tokens_consumed: int = 0
    duration_ms: float = 0.0
    checkpoint_id: Optional[str] = None
    error_message: Optional[str] = None
```

---

## 3. Abstract Hexagonal Port Interface
```python
from abc import ABC, abstractmethod

class IAgnoCanvasAdapter(ABC):
    @abstractmethod
    def validate_graph(self, graph: CanvasGraphPayload) -> bool:
        """Validates DAG structure, types, and edge compatibility."""
        pass

    @abstractmethod
    def execute_graph_stepwise(self, graph: CanvasGraphPayload) -> Dict[str, NodeExecutionResult]:
        """Executes nodes in topological order handling Agent, Team, and Workflow nodes."""
        pass

    @abstractmethod
    def create_hitl_checkpoint(self, node: CanvasNodeConfig, action: str, params: Dict[str, Any]) -> HITLCheckpoint:
        """Saves current state and returns a pending checkpoint."""
        pass

    @abstractmethod
    def resume_hitl_checkpoint(self, resolution: HITLResolutionRequest) -> NodeExecutionResult:
        """Resumes execution from checkpoint with user feedback."""
        pass

    @abstractmethod
    def sync_memory(self, workspace_id: str, node_id: str, extracted_facts: Dict[str, Any]) -> bool:
        """Persists agentic memories into SCONES memory store."""
        pass
```
