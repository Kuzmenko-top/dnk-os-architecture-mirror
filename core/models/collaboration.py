# --- DNK-MRH-HEADER ---
# mrh_id: "core_models_collaboration"
# purpose: "Domain models for multi-agent collaboration (Task, TaskPriority, TaskStatus, AgentRole)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from enum import Enum
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Dict, Any, Optional

class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AgentRole(str, Enum):
    RESEARCHER = "researcher"
    WRITER = "writer"
    VALIDATOR = "validator"
    ORCHESTRATOR = "orchestrator"
    CRITIC = "critic"

class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    agent_id: UUID
    task_type: str
    priority: TaskPriority
    status: TaskStatus
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: int
    updated_at: int
