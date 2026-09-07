# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_schemas_workflow_dag_schemas"
# purpose: "Pydantic Schemas and DAG Validation Engine for Visual Canvas Workflows (DNK-CANVAS-001 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import enum
import uuid
from typing import Dict, List, Optional, Any, Set, Union
from pydantic import BaseModel, Field, field_validator, model_validator


class WorkflowNodeType(str, enum.Enum):
    A2A_AGENT = "a2a_agent"
    EVENT_TRIGGER = "event_trigger"
    BATCH_TASK = "batch_task"
    SHOPIFY_ACTION = "shopify_action"
    HARDWARE_ACTION = "hardware_action"


class NodeExecutionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class NodePosition(BaseModel):
    x: float = 0.0
    y: float = 0.0


# --- Specific Node Configuration Payloads ---

class A2AAgentNodeConfig(BaseModel):
    agent_id: str = Field(..., description="Target A2A Agent ID (e.g. gerych_builder, dnk_shopify)")
    role: str = Field("worker", description="Agent execution role in mesh")
    task_prompt: str = Field(..., description="Prompt or instruction for the agent")
    capabilities: List[str] = Field(default_factory=list, description="Required capabilities")
    consensus_threshold: float = Field(0.75, ge=0.0, le=1.0, description="Mesh consensus threshold")
    timeout_sec: int = Field(30, ge=1, le=300, description="Execution timeout in seconds")


class EventTriggerNodeConfig(BaseModel):
    stream_topic: str = Field(..., description="Event stream topic or channel name")
    event_type: str = Field("custom", description="Type of event trigger")
    filter_condition: Optional[str] = Field(None, description="Optional filter expression or jq query")
    debounce_ms: int = Field(0, ge=0, description="Debounce time in milliseconds")
    auto_ack: bool = Field(True, description="Automatically acknowledge consumed event")


class BatchTaskNodeConfig(BaseModel):
    batch_job_type: str = Field(..., description="Batch job classification or handler")
    payload_template: Dict[str, Any] = Field(default_factory=dict, description="Job parameters and template")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry count")
    backoff_factor: float = Field(2.0, ge=1.0, description="Exponential backoff multiplier")
    priority: int = Field(1, ge=1, le=10, description="Task execution priority")


class ShopifyActionNodeConfig(BaseModel):
    action_type: str = Field(..., description="Shopify action: order_create, inventory_sync, customer_tag, product_update")
    shop_domain: str = Field(..., description="Shopify store domain")
    mutation_params: Dict[str, Any] = Field(default_factory=dict, description="GraphQL/REST mutation parameters")
    api_version: str = Field("2026-01", description="Shopify API version")


class HardwareActionNodeConfig(BaseModel):
    device_id: str = Field(..., description="ReBurn device identifier")
    action_type: str = Field(..., description="Action: gpio_write, read_sensor, trigger_actuator, pwm_set")
    pin: Optional[int] = Field(None, ge=0, le=40, description="GPIO pin number if applicable")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Control payload or telemetry criteria")


# --- General Node and Edge Models ---

class WorkflowNode(BaseModel):
    id: str = Field(default_factory=lambda: f"node_{uuid.uuid4().hex[:8]}")
    type: WorkflowNodeType
    label: str = Field(..., description="Display title for the canvas node")
    position: NodePosition = Field(default_factory=NodePosition)
    config: Dict[str, Any] = Field(default_factory=dict, description="Node configuration matching its type")
    status: NodeExecutionStatus = Field(default=NodeExecutionStatus.PENDING)
    last_output: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None

    def get_typed_config(self) -> Union[A2AAgentNodeConfig, EventTriggerNodeConfig, BatchTaskNodeConfig, ShopifyActionNodeConfig, HardwareActionNodeConfig, Dict[str, Any]]:
        """Validate and return typed configuration object."""
        if self.type == WorkflowNodeType.A2A_AGENT:
            return A2AAgentNodeConfig(**self.config)
        elif self.type == WorkflowNodeType.EVENT_TRIGGER:
            return EventTriggerNodeConfig(**self.config)
        elif self.type == WorkflowNodeType.BATCH_TASK:
            return BatchTaskNodeConfig(**self.config)
        elif self.type == WorkflowNodeType.SHOPIFY_ACTION:
            return ShopifyActionNodeConfig(**self.config)
        elif self.type == WorkflowNodeType.HARDWARE_ACTION:
            return HardwareActionNodeConfig(**self.config)
        return self.config


class WorkflowEdge(BaseModel):
    id: str = Field(default_factory=lambda: f"edge_{uuid.uuid4().hex[:8]}")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_handle: Optional[str] = Field(None, description="Source port handle (e.g. output, success, failure)")
    target_handle: Optional[str] = Field(None, description="Target port handle (e.g. input)")
    condition: Optional[str] = Field(None, description="Conditional execution predicate")
    edge_type: str = Field("default", description="Visual and execution edge style")


# --- Workflow DAG Model & Validation ---

class WorkflowDAG(BaseModel):
    id: str = Field(default_factory=lambda: f"wf_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., description="Workflow title")
    description: Optional[str] = Field(None, description="Detailed description")
    workspace_id: str = Field("ws-alpha-001", description="Workspace ID")
    nodes: List[WorkflowNode] = Field(default_factory=list)
    edges: List[WorkflowEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    version: int = Field(1, description="Workflow schema version")

    @model_validator(mode="after")
    def validate_dag_integrity(self) -> "WorkflowDAG":
        """
        Validates:
        1. Unique node IDs
        2. Valid edge references (source and target exist)
        3. DAG acyclicity (Kahn's Topological Sort algorithm)
        4. Valid typed configurations for all nodes
        """
        node_ids: Set[str] = set()
        for node in self.nodes:
            if node.id in node_ids:
                raise ValueError(f"Duplicate node ID detected: {node.id}")
            node_ids.add(node.id)
            # Validate typed config integrity
            try:
                node.get_typed_config()
            except Exception as e:
                raise ValueError(f"Invalid configuration for node {node.id} ({node.type}): {e}")

        # Check edge endpoints
        for edge in self.edges:
            if edge.source not in node_ids:
                raise ValueError(f"Edge {edge.id} references non-existent source node: {edge.source}")
            if edge.target not in node_ids:
                raise ValueError(f"Edge {edge.id} references non-existent target node: {edge.target}")
            if edge.source == edge.target:
                raise ValueError(f"Self-loop detected on node {edge.source} via edge {edge.id}")

        # Cycle detection via Kahn's Algorithm
        in_degree: Dict[str, int] = {nid: 0 for nid in node_ids}
        adj_list: Dict[str, List[str]] = {nid: [] for nid in node_ids}

        for edge in self.edges:
            adj_list[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        queue: List[str] = [nid for nid, deg in in_degree.items() if deg == 0]
        visited_count = 0

        while queue:
            curr = queue.pop(0)
            visited_count += 1
            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if visited_count != len(node_ids) and len(node_ids) > 0:
            raise ValueError("Cycle detected in Workflow graph! Workflows must be Directed Acyclic Graphs (DAG).")

        return self

    def get_topological_order(self) -> List[str]:
        """Returns node IDs in topologically sorted dependency order."""
        node_ids = [n.id for n in self.nodes]
        in_degree: Dict[str, int] = {nid: 0 for nid in node_ids}
        adj_list: Dict[str, List[str]] = {nid: [] for nid in node_ids}

        for edge in self.edges:
            adj_list[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        queue: List[str] = [nid for nid, deg in in_degree.items() if deg == 0]
        order: List[str] = []

        while queue:
            curr = queue.pop(0)
            order.append(curr)
            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return order

    def to_react_flow(self) -> Dict[str, Any]:
        """Convert DAG into React Flow canvas state format."""
        rf_nodes = []
        for node in self.nodes:
            rf_nodes.append({
                "id": node.id,
                "type": node.type.value,
                "position": {"x": node.position.x, "y": node.position.y},
                "data": {
                    "label": node.label,
                    "type": node.type.value,
                    "config": node.config,
                    "status": node.status.value,
                    "last_output": node.last_output,
                    "last_error": node.last_error
                }
            })

        rf_edges = []
        for edge in self.edges:
            rf_edges.append({
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "sourceHandle": edge.source_handle,
                "targetHandle": edge.target_handle,
                "data": {
                    "condition": edge.condition,
                    "edge_type": edge.edge_type
                }
            })

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "workspace_id": self.workspace_id,
            "nodes": rf_nodes,
            "edges": rf_edges,
            "metadata": self.metadata,
            "version": self.version
        }

    @classmethod
    def from_react_flow(cls, payload: Dict[str, Any]) -> "WorkflowDAG":
        """Construct a validated WorkflowDAG from React Flow JSON format."""
        nodes = []
        for n in payload.get("nodes", []):
            pos_data = n.get("position", {})
            pos = NodePosition(x=pos_data.get("x", 0.0), y=pos_data.get("y", 0.0))
            data = n.get("data", {})
            nodes.append(WorkflowNode(
                id=n["id"],
                type=WorkflowNodeType(n.get("type", data.get("type", "a2a_agent"))),
                label=data.get("label", n.get("id")),
                position=pos,
                config=data.get("config", {}),
                status=NodeExecutionStatus(data.get("status", "pending")),
                last_output=data.get("last_output"),
                last_error=data.get("last_error")
            ))

        edges = []
        for e in payload.get("edges", []):
            data = e.get("data", {})
            edges.append(WorkflowEdge(
                id=e.get("id", f"edge_{uuid.uuid4().hex[:8]}"),
                source=e["source"],
                target=e["target"],
                source_handle=e.get("sourceHandle"),
                target_handle=e.get("targetHandle"),
                condition=data.get("condition"),
                edge_type=data.get("edge_type", "default")
            ))

        return cls(
            id=payload.get("id", f"wf_{uuid.uuid4().hex[:12]}"),
            name=payload.get("name", "Untitled Workflow"),
            description=payload.get("description"),
            workspace_id=payload.get("workspace_id", "ws-alpha-001"),
            nodes=nodes,
            edges=edges,
            metadata=payload.get("metadata", {}),
            version=payload.get("version", 1)
        )


# --- Execution DTOs ---

class WorkflowExecuteRequest(BaseModel):
    initial_context: Dict[str, Any] = Field(default_factory=dict, description="Initial execution runtime context")
    trigger_event: Optional[Dict[str, Any]] = Field(None, description="Triggering event payload if initiated via trigger")


class NodeExecutionEvent(BaseModel):
    workflow_id: str
    node_id: str
    status: NodeExecutionStatus
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=lambda: 0.0)


class WorkflowExecutionSummary(BaseModel):
    workflow_id: str
    execution_id: str
    status: str
    total_nodes: int
    completed_nodes: int
    failed_nodes: int
    node_results: Dict[str, Dict[str, Any]]
    execution_duration_sec: float
