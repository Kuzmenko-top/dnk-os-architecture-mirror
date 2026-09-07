# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/batch_dead_letter_record.py"
# purpose: "ORM Model representing Dead Letter Queue (DLQ) task records for failed batch executions."
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
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class DLQStatus(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    REPLAYED = "REPLAYED"
    DISCARDED = "DISCARDED"


class BatchDeadLetterRecord(BaseModel):
    """Represents a failed batch task moved to the Dead-Letter Queue after exhausting retries."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = Field(..., description="Original failed task ID")
    job_id: str = Field(..., description="Original failed job ID")
    tenant_id: str = Field(default="ws-alpha-001")
    
    task_name: str = Field(..., description="Task operation/name")
    payload: Dict[str, Any] = Field(default_factory=dict)
    
    error_message: str = Field(...)
    stack_trace: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0)
    
    trace_id: Optional[str] = Field(default=None)
    span_id: Optional[str] = Field(default=None)
    
    status: DLQStatus = Field(default=DLQStatus.UNRESOLVED)
    replayed_at: Optional[datetime] = Field(default=None)
    replayed_task_id: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def mark_replayed(self, new_task_id: str) -> None:
        self.status = DLQStatus.REPLAYED
        self.replayed_at = datetime.now(timezone.utc)
        self.replayed_task_id = new_task_id

    def mark_discarded(self) -> None:
        self.status = DLQStatus.DISCARDED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "job_id": self.job_id,
            "tenant_id": self.tenant_id,
            "task_name": self.task_name,
            "payload": self.payload,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "retry_count": self.retry_count,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "replayed_at": self.replayed_at.isoformat() if self.replayed_at else None,
            "replayed_task_id": self.replayed_task_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }
