# --- DNK-MRH-HEADER ---
# mrh_id: "core_workflows_models"
# purpose: "Pydantic domain contracts and typed schemas for Nodes, Ports, Capabilities, and Workflow DAG Plans"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# --- END DNK-MRH-HEADER ---

from enum import Enum
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NodeCategory(str, Enum):
    GOAL = "goal"
    TASK = "task"
    AGENT = "agent"
    APPROVAL = "approval"
    ARTIFACT = "artifact"
    ECOMMERCE = "ecommerce"
    MEDIA = "media"
    RESEARCH = "research"
    DEPLOYMENT = "deployment"


class PortType(str, Enum):
    DATA = "data"
    CONTROL = "control"
    APPROVAL = "approval"
    REFERENCE = "reference"


class PortDefinition(BaseModel):
    name: str = Field(..., description="Unique port name on this node")
    data_type: str = Field(..., description="Semantic data type e.g. shopify.store_ref, text.brief")
    port_type: PortType = Field(default=PortType.DATA, description="Port categorization")
    required: bool = Field(default=True, description="Whether port connection is mandatory")
    description: Optional[str] = Field(default=None, description="Human-readable description")


class NodeContract(BaseModel):
    id: str = Field(..., description="Unique node contract identifier e.g. dnk.shopify.store")
    version: str = Field(default="1.0.0", description="Semantic version of node contract")
    title: str = Field(..., description="Human-friendly node title")
    category: NodeCategory = Field(default=NodeCategory.TASK, description="Category in Node Registry")
    icon: str = Field(default="bot", description="Lucide icon identifier")
    ui_component: str = Field(..., description="Matching React component name e.g. ShopifyStoreNode")
    executor: Optional[str] = Field(default=None, description="Backend executor class / module")
    inputs: List[PortDefinition] = Field(default_factory=list, description="Input port specifications")
    outputs: List[PortDefinition] = Field(default_factory=list, description="Output port specifications")
    capabilities: List[str] = Field(default_factory=list, description="List of capabilities this node can fulfill")
    permissions: List[str] = Field(default_factory=list, description="Required permissions e.g. shopify:write_themes")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Base risk level")
    approval_required: bool = Field(default=False, description="Whether explicit approval is mandatory")
    description: Optional[str] = Field(default=None, description="Summary of node responsibility")


class CapabilityDefinition(BaseModel):
    id: str = Field(..., description="Unique capability identifier e.g. shopify.theme.preview")
    name: str = Field(..., description="Human-readable capability name")
    domain: str = Field(..., description="Domain e.g. shopify, video, code, memory, patent")
    node_type: str = Field(..., description="Primary node contract fulfilling this capability")
    assigned_agent: Optional[str] = Field(default=None, description="Assigned swarm worker")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Assessed risk level")
    description: Optional[str] = Field(default=None, description="Detailed explanation")


class WorkflowNodeInstance(BaseModel):
    id: str = Field(..., description="Unique node instance ID in this workflow")
    type: str = Field(..., description="React Flow node type or Contract ID")
    title: str = Field(..., description="Display title on canvas")
    category: Optional[NodeCategory] = None
    assigned_agent: Optional[str] = None
    state: str = Field(default="idle", description="Execution state: idle, running, completed, waiting_approval, failed")
    config: Dict[str, Any] = Field(default_factory=dict, description="Config parameters")
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    risk: RiskLevel = Field(default=RiskLevel.LOW)
    required_before: List[str] = Field(default_factory=list)


class WorkflowEdgeInstance(BaseModel):
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    source_port: Optional[str] = None
    target_port: Optional[str] = None
    edge_type: PortType = Field(default=PortType.DATA)
    animated: bool = Field(default=True)
    label: Optional[str] = None


class WorkflowPlan(BaseModel):
    workflow_id: str = Field(..., description="Unique workflow execution ID")
    title: str = Field(..., description="Display title for workflow")
    intent: str = Field(..., description="Classified intent")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    user_goal: str = Field(..., description="Original user prompt")
    nodes: List[WorkflowNodeInstance] = Field(default_factory=list)
    edges: List[WorkflowEdgeInstance] = Field(default_factory=list)
    approval_required: bool = Field(default=False)
    high_risk_actions: List[str] = Field(default_factory=list)
    trace_id: Optional[str] = None
    created_at: Optional[str] = None
