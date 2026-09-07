# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/batch_workflow_dag.py"
# purpose: "ORM Model representing a Directed Acyclic Graph (DAG) Workflow for Batch Orchestration."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DAGStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class DAGNode(BaseModel):
    """Represents a node within a workflow DAG."""
    node_id: str = Field(..., description="Unique task node identifier")
    name: str = Field(..., description="Task/handler name")
    task_type: str = Field(default="python_func")
    dependencies: List[str] = Field(default_factory=list, description="Upstream node IDs required before execution")
    payload: Dict[str, Any] = Field(default_factory=dict)
    max_retries: int = Field(default=3)


class BatchWorkflowDAG(BaseModel):
    """Represents a Directed Acyclic Graph workflow definition and execution state."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Workflow title")
    description: str = Field(default="")
    tenant_id: str = Field(default="ws-alpha-001")
    status: DAGStatus = Field(default=DAGStatus.DRAFT)
    
    nodes: Dict[str, DAGNode] = Field(default_factory=dict, description="Dictionary of node_id -> DAGNode")
    concurrency_limit: int = Field(default=5, description="Max parallel nodes executing simultaneously")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_node(self, node: DAGNode) -> None:
        self.nodes[node.node_id] = node
        self.updated_at = datetime.now(timezone.utc)

    def get_root_nodes(self) -> List[DAGNode]:
        """Returns nodes with no dependencies (entry points)."""
        return [node for node in self.nodes.values() if not node.dependencies]

    def has_cycles(self) -> bool:
        """Validates whether the graph has any circular dependencies using Kahn's algorithm."""
        in_degree = {k: 0 for k in self.nodes}
        for node in self.nodes.values():
            for dep in node.dependencies:
                if dep in in_degree:
                    in_degree[node.node_id] += 1
        
        queue = [k for k, v in in_degree.items() if v == 0]
        visited_count = 0
        
        while queue:
            curr = queue.pop(0)
            visited_count += 1
            # Check who depends on curr
            for node in self.nodes.values():
                if curr in node.dependencies:
                    in_degree[node.node_id] -= 1
                    if in_degree[node.node_id] == 0:
                        queue.append(node.node_id)
                        
        return visited_count != len(self.nodes)

    def get_topological_order(self) -> List[str]:
        """Returns ordered list of node IDs executable in sequence/batches."""
        if self.has_cycles():
            raise ValueError("Cannot calculate topological sort: DAG contains circular dependencies.")
            
        in_degree = {k: 0 for k in self.nodes}
        for node in self.nodes.values():
            for dep in node.dependencies:
                if dep in in_degree:
                    in_degree[node.node_id] += 1
                    
        queue = [k for k, v in in_degree.items() if v == 0]
        order = []
        
        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for node in self.nodes.values():
                if curr in node.dependencies:
                    in_degree[node.node_id] -= 1
                    if in_degree[node.node_id] == 0:
                        queue.append(node.node_id)
                        
        return order

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tenant_id": self.tenant_id,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "nodes": {k: v.model_dump() for k, v in self.nodes.items()},
            "node_count": len(self.nodes),
            "concurrency_limit": self.concurrency_limit,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }
