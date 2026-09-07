# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/batch_task.py"
# purpose: "ORM Model representing an individual granular task within a Batch Job or DAG Workflow."
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


class BatchTaskStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRYING = "RETRYING"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class BatchTask(BaseModel):
    """Represents an atomic execution unit inside a batch job or DAG step."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    job_id: str = Field(..., description="Parent Batch Job ID")
    name: str = Field(..., description="Task operation name or handler key")
    tenant_id: str = Field(default="ws-alpha-001")
    status: BatchTaskStatus = Field(default=BatchTaskStatus.PENDING)
    
    task_type: str = Field(default="generic_compute", description="Handler type e.g. python, http, sql, agent_call")
    assigned_worker_id: Optional[str] = Field(default=None, description="Worker Node executing this task")
    
    dependencies: List[str] = Field(default_factory=list, description="List of prerequisite task IDs in DAG")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Input payload for task execution")
    result: Dict[str, Any] = Field(default_factory=dict, description="Output result of execution")
    error_message: Optional[str] = Field(default=None)
    stack_trace: Optional[str] = Field(default=None)
    
    max_retries: int = Field(default=3)
    retry_count: int = Field(default=0)
    retry_backoff_seconds: float = Field(default=1.0)
    
    trace_id: Optional[str] = Field(default=None, description="Distributed Trace ID")
    span_id: Optional[str] = Field(default=None, description="Distributed Span ID")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    queued_at: Optional[datetime] = Field(default=None)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    duration_ms: float = Field(default=0.0)

    def mark_queued(self) -> None:
        self.status = BatchTaskStatus.QUEUED
        self.queued_at = datetime.now(timezone.utc)

    def mark_running(self, worker_id: Optional[str] = None) -> None:
        self.status = BatchTaskStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
        if worker_id:
            self.assigned_worker_id = worker_id

    def mark_completed(self, result: Optional[Dict[str, Any]] = None) -> None:
        self.status = BatchTaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000.0
        if result:
            self.result = result

    def mark_failed(self, error: str, stack: Optional[str] = None) -> None:
        self.status = BatchTaskStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        if self.started_at:
            self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000.0
        self.error_message = error
        self.stack_trace = stack

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "name": self.name,
            "tenant_id": self.tenant_id,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "task_type": self.task_type,
            "assigned_worker_id": self.assigned_worker_id,
            "dependencies": self.dependencies,
            "payload": self.payload,
            "result": self.result,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "retry_backoff_seconds": self.retry_backoff_seconds,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "queued_at": self.queued_at.isoformat() if self.queued_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
        }
