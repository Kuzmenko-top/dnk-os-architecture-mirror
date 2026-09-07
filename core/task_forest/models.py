# --- DNK-MRH-HEADER ---
# mrh_id: "core/task_forest/models.py"
# purpose: "Task Forest node models, specialized node types, and serializations."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Type
from datetime import datetime
import uuid


class NodeType(str, Enum):
    TASK = "task"
    IDEA = "idea"
    GOAL = "goal"
    BUG = "bug"
    DOCUMENTATION = "documentation"


class ExecutionStage(str, Enum):
    BACKLOG = "backlog"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskNode:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: NodeType = NodeType.TASK
    title: str = ""
    description: str = ""
    stage: ExecutionStage = ExecutionStage.BACKLOG
    priority: Priority = Priority.MEDIUM
    dependencies: List[str] = field(default_factory=list)  # List of node IDs
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Swarm Agent Assignment (Variant A)
    assigned_agent: Optional[str] = None
    agent_status: Optional[str] = None  # idle, running, completed, failed
    agent_run_id: Optional[str] = None

    # Position in canvas (React Flow)
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    size: Dict[str, float] = field(default_factory=lambda: {"width": 260.0, "height": 140.0})

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, Enum) else str(self.type),
            "title": self.title,
            "description": self.description,
            "stage": self.stage.value if isinstance(self.stage, Enum) else str(self.stage),
            "priority": self.priority.value if isinstance(self.priority, Enum) else str(self.priority),
            "dependencies": list(self.dependencies),
            "tags": list(self.tags),
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at),
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else str(self.updated_at),
            "completed_at": self.completed_at.isoformat() if isinstance(self.completed_at, datetime) else None,
            "assigned_agent": self.assigned_agent,
            "agent_status": self.agent_status,
            "agent_run_id": self.agent_run_id,
            "metadata": dict(self.metadata),
            "position": dict(self.position),
            "size": dict(self.size),
        }

    @classmethod
    def from_dict(cls: Type["TaskNode"], data: Dict[str, Any]) -> "TaskNode":
        node_type_str = data.get("type", NodeType.TASK.value)
        try:
            node_type = NodeType(node_type_str)
        except ValueError:
            node_type = NodeType.TASK

        stage_str = data.get("stage", ExecutionStage.BACKLOG.value)
        try:
            stage = ExecutionStage(stage_str)
        except ValueError:
            stage = ExecutionStage.BACKLOG

        priority_str = data.get("priority", Priority.MEDIUM.value)
        try:
            priority = Priority(priority_str)
        except ValueError:
            priority = Priority.MEDIUM

        created_at_val = data.get("created_at")
        if isinstance(created_at_val, str):
            created_at = datetime.fromisoformat(created_at_val)
        elif isinstance(created_at_val, datetime):
            created_at = created_at_val
        else:
            created_at = datetime.now()

        updated_at_val = data.get("updated_at")
        if isinstance(updated_at_val, str):
            updated_at = datetime.fromisoformat(updated_at_val)
        elif isinstance(updated_at_val, datetime):
            updated_at = updated_at_val
        else:
            updated_at = datetime.now()

        completed_at_val = data.get("completed_at")
        if isinstance(completed_at_val, str):
            completed_at = datetime.fromisoformat(completed_at_val)
        elif isinstance(completed_at_val, datetime):
            completed_at = completed_at_val
        else:
            completed_at = None

        node_cls: Type[TaskNode] = cls
        if cls is TaskNode:
            if node_type == NodeType.IDEA:
                node_cls = IdeaNode
            elif node_type == NodeType.GOAL:
                node_cls = GoalNode
            elif node_type == NodeType.BUG:
                node_cls = BugNode
            elif node_type == NodeType.DOCUMENTATION:
                node_cls = DocumentationNode

        kwargs = {
            "id": data.get("id", str(uuid.uuid4())),
            "title": data.get("title", ""),
            "description": data.get("description", ""),
            "stage": stage,
            "priority": priority,
            "dependencies": list(data.get("dependencies", [])),
            "tags": list(data.get("tags", [])),
            "created_at": created_at,
            "updated_at": updated_at,
            "completed_at": completed_at,
            "metadata": dict(data.get("metadata", {})),
            "assigned_agent": data.get("assigned_agent"),
            "agent_status": data.get("agent_status"),
            "agent_run_id": data.get("agent_run_id"),
            "position": dict(data.get("position", {"x": 0.0, "y": 0.0})),
            "size": dict(data.get("size", {"width": 260.0, "height": 140.0})),
        }

        if node_cls is TaskNode:
            kwargs["type"] = node_type
            return TaskNode(**kwargs)
        else:
            return node_cls(**kwargs)


@dataclass
class IdeaNode(TaskNode):
    def __init__(self, **kwargs):
        kwargs["type"] = NodeType.IDEA
        metadata = dict(kwargs.pop("metadata", {}))
        tasknode_fields = {"id", "type", "title", "description", "stage", "priority", "dependencies", "tags", "created_at", "updated_at", "completed_at", "assigned_agent", "agent_status", "agent_run_id", "position", "size"}
        extra = {k: v for k, v in list(kwargs.items()) if k not in tasknode_fields}
        for k in extra:
            metadata[k] = kwargs.pop(k)
        super().__init__(**kwargs)
        self.metadata = metadata
        if "votes" not in self.metadata:
            self.metadata["votes"] = 0
        if "status" not in self.metadata:
            self.metadata["status"] = "proposed"  # proposed, approved, rejected


@dataclass
class GoalNode(TaskNode):
    def __init__(self, **kwargs):
        kwargs["type"] = NodeType.GOAL
        metadata = dict(kwargs.pop("metadata", {}))
        tasknode_fields = {"id", "type", "title", "description", "stage", "priority", "dependencies", "tags", "created_at", "updated_at", "completed_at", "assigned_agent", "agent_status", "agent_run_id", "position", "size"}
        extra = {k: v for k, v in list(kwargs.items()) if k not in tasknode_fields}
        for k in extra:
            metadata[k] = kwargs.pop(k)
        super().__init__(**kwargs)
        self.metadata = metadata
        if "milestone" not in self.metadata:
            self.metadata["milestone"] = None
        if "progress" not in self.metadata:
            self.metadata["progress"] = 0.0  # 0.0 - 1.0


@dataclass
class BugNode(TaskNode):
    def __init__(self, **kwargs):
        kwargs["type"] = NodeType.BUG
        metadata = dict(kwargs.pop("metadata", {}))
        tasknode_fields = {"id", "type", "title", "description", "stage", "priority", "dependencies", "tags", "created_at", "updated_at", "completed_at", "assigned_agent", "agent_status", "agent_run_id", "position", "size"}
        extra = {k: v for k, v in list(kwargs.items()) if k not in tasknode_fields}
        for k in extra:
            metadata[k] = kwargs.pop(k)
        super().__init__(**kwargs)
        self.metadata = metadata
        if "severity" not in self.metadata:
            self.metadata["severity"] = "medium"  # low, medium, high, critical
        if "reported_by" not in self.metadata:
            self.metadata["reported_by"] = None
        if "fixed_in_version" not in self.metadata:
            self.metadata["fixed_in_version"] = None


@dataclass
class DocumentationNode(TaskNode):
    def __init__(self, **kwargs):
        kwargs["type"] = NodeType.DOCUMENTATION
        metadata = dict(kwargs.pop("metadata", {}))
        tasknode_fields = {"id", "type", "title", "description", "stage", "priority", "dependencies", "tags", "created_at", "updated_at", "completed_at", "assigned_agent", "agent_status", "agent_run_id", "position", "size"}
        extra = {k: v for k, v in list(kwargs.items()) if k not in tasknode_fields}
        for k in extra:
            metadata[k] = kwargs.pop(k)
        super().__init__(**kwargs)
        self.metadata = metadata
        if "doc_type" not in self.metadata:
            self.metadata["doc_type"] = "guide"  # guide, api, tutorial, troubleshooting
        if "version" not in self.metadata:
            self.metadata["version"] = "1.0.0"
