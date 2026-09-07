# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/batch_job.py"
# purpose: "ORM Model representing a top-level Batch Processing Job in DNK OS."
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


class BatchJobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"


class BatchJobPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class BatchJob(BaseModel):
    """Represents a high-level batch processing job consisting of one or more tasks or a DAG."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Human-readable name of the batch job")
    tenant_id: str = Field(default="ws-alpha-001", description="Tenant isolation ID")
    status: BatchJobStatus = Field(default=BatchJobStatus.PENDING)
    priority: BatchJobPriority = Field(default=BatchJobPriority.NORMAL)
    workflow_id: Optional[str] = Field(default=None, description="Associated DAG Workflow ID if applicable")
    created_by: str = Field(default="system", description="User or agent initiator")
    trace_id: Optional[str] = Field(default=None, description="Associated W3C Distributed Trace ID")
    
    total_tasks: int = Field(default=0)
    completed_tasks: int = Field(default=0)
    failed_tasks: int = Field(default=0)
    
    payload: Dict[str, Any] = Field(default_factory=dict, description="Job input parameters and configuration")
    result: Dict[str, Any] = Field(default_factory=dict, description="Consolidated job output")
    error_message: Optional[str] = Field(default=None)
    
    timeout_seconds: int = Field(default=3600, description="Job execution timeout in seconds")
    max_retries: int = Field(default=3)
    retry_count: int = Field(default=0)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def mark_started(self) -> None:
        self.status = BatchJobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self, result: Optional[Dict[str, Any]] = None) -> None:
        self.status = BatchJobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        if result:
            self.result = result

    def mark_failed(self, error: str) -> None:
        self.status = BatchJobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "tenant_id": self.tenant_id,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "priority": self.priority.value if isinstance(self.priority, Enum) else self.priority,
            "workflow_id": self.workflow_id,
            "created_by": self.created_by,
            "trace_id": self.trace_id,
            "total_tasks": self.total_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "payload": self.payload,
            "result": self.result,
            "error_message": self.error_message,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
        }
