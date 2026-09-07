# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_node_tasks/models.py"
# purpose: "Pydantic Domain Models for Node Based Task & Ideas System with DAG Dependencies"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    IDEA = "idea"
    EPIC = "epic"
    TASK = "task"
    SLICE = "slice"
    GATE = "gate"


class ExecutionStage(str, Enum):
    IDEATION = "ideation"
    ARCHITECTURE = "architecture"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    VERIFICATION = "verification"
    COMPLETED = "completed"


class NodeStatus(str, Enum):
    DRAFT = "draft"
    BACKLOG = "backlog"
    BLOCKED = "blocked"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EdgeRelation(str, Enum):
    DEPENDS_ON = "depends_on"      # target depends on source (source must be completed)
    SPAWNS_FROM = "spawns_from"    # target task/epic spawned from source idea
    BLOCKS = "blocks"              # source blocks target
    VALIDATES = "validates"        # source gate validates target task
    PARENT_OF = "parent_of"        # hierarchy


class DependencyEdge(BaseModel):
    id: str = Field(description="Unique edge identifier")
    source: str = Field(description="Source node ID")
    target: str = Field(description="Target node ID")
    relation: EdgeRelation = Field(default=EdgeRelation.DEPENDS_ON, description="Relationship semantic")
    description: Optional[str] = Field(default="", description="Edge notes or criteria")


class NodePosition(BaseModel):
    x: float = 0.0
    y: float = 0.0


class ProjectInfo(BaseModel):
    id: str = Field(description="Unique project identifier, e.g. 'dnk_core', 'm_craft'")
    name: str = Field(description="Display name of the project")
    slug: str = Field(description="URL-friendly slug")
    description: str = Field(default="", description="Detailed project overview")
    color: str = Field(default="#06b6d4", description="Hex or Tailwind accent color")
    icon: str = Field(default="dna", description="Lucide icon name")
    is_active: bool = Field(default=True, description="Whether project is active")
    created_at: str = Field(default="", description="ISO datetime created")


class NodeItem(BaseModel):
    id: str = Field(description="Unique node identifier")
    title: str = Field(description="Title of task or idea")
    description: str = Field(default="", description="Detailed description / problem statement")
    node_type: NodeType = Field(default=NodeType.TASK, description="Node semantic type")
    stage: ExecutionStage = Field(default=ExecutionStage.READY, description="Lifecycle execution stage")
    status: NodeStatus = Field(default=NodeStatus.READY, description="Current workflow status")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Percentage completion (0-100)")
    
    project_id: str = Field(default="dnk_core", description="Project or workspace partition ID")
    
    assigned_agent: Optional[str] = Field(
        default="gerych_builder",
        description="Assigned swarm worker or human (e.g. gerych_builder, dnk_dev_fullstack, Maxim)"
    )
    target_module: Optional[str] = Field(
        default="core",
        description="Target DNK OS subsystem (e.g. core, apps/web, apps/api, services)"
    )
    target_files: List[str] = Field(
        default_factory=list,
        description="List of target relative files for this task"
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="Checklist items for completion or gate passing"
    )
    tags: List[str] = Field(default_factory=list, description="Categorization tags")
    priority: str = Field(default="medium", description="Priority level: low, medium, high, critical")
    
    # Visual canvas coordinates
    position: NodePosition = Field(default_factory=NodePosition)
    
    # Dynamic computed DAG fields
    is_blocked: bool = Field(default=False, description="Calculated: true if any prerequisite is incomplete")
    blocked_by: List[str] = Field(default_factory=list, description="IDs of incomplete prerequisite nodes")
    
    # Metadata & timestamps
    created_at: str = Field(default="", description="ISO datetime created")
    updated_at: str = Field(default="", description="ISO datetime updated")


class NodeTaskGraph(BaseModel):
    nodes: Dict[str, NodeItem] = Field(default_factory=dict)
    edges: List[DependencyEdge] = Field(default_factory=list)
    stages: List[str] = Field(
        default_factory=lambda: [
            ExecutionStage.IDEATION.value,
            ExecutionStage.ARCHITECTURE.value,
            ExecutionStage.READY.value,
            ExecutionStage.IN_PROGRESS.value,
            ExecutionStage.VERIFICATION.value,
            ExecutionStage.COMPLETED.value,
        ]
    )
    version: str = "1.0.0"
    updated_at: str = ""


class CreateOrUpdateNodeRequest(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = ""
    node_type: NodeType = NodeType.TASK
    stage: Optional[ExecutionStage] = None
    status: Optional[NodeStatus] = None
    progress: Optional[float] = None
    assigned_agent: Optional[str] = None
    target_module: Optional[str] = None
    target_files: Optional[List[str]] = None
    acceptance_criteria: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    position: Optional[NodePosition] = None
    project_id: Optional[str] = "dnk_core"


class AddEdgeRequest(BaseModel):
    source: str
    target: str
    relation: EdgeRelation = EdgeRelation.DEPENDS_ON
    description: Optional[str] = ""


class StageTransitionRequest(BaseModel):
    node_id: str
    target_stage: ExecutionStage
    target_status: Optional[NodeStatus] = None
    force: bool = Field(default=False, description="Bypass dependency validation if true")


class IdeaConversionRequest(BaseModel):
    idea_id: str
    new_task_title: Optional[str] = None
    node_type: NodeType = NodeType.TASK
    assigned_agent: Optional[str] = "gerych_builder"
    target_module: Optional[str] = "core"
    target_files: Optional[List[str]] = None


class GraphStatistics(BaseModel):
    total_nodes: int
    ideas_count: int
    epics_count: int
    tasks_count: int
    slices_count: int
    gates_count: int
    blocked_count: int
    ready_count: int
    in_progress_count: int
    completed_count: int
    overall_progress: float
    agent_workload: Dict[str, int]
    by_type: Optional[Dict[str, int]] = None
    by_stage: Optional[Dict[str, int]] = None
    blocked_nodes_count: Optional[int] = None
    overall_progress_pct: Optional[float] = None
