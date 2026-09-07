# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/batch_worker_node.py"
# purpose: "ORM Model representing an active distributed Worker Node executing batch workloads."
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


class WorkerStatus(str, Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    PAUSED = "PAUSED"
    OFFLINE = "OFFLINE"
    DRAINING = "DRAINING"


class BatchWorkerNode(BaseModel):
    """Represents a registered worker process or pod capable of processing tasks."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hostname: str = Field(default="localhost")
    ip_address: Optional[str] = Field(default="127.0.0.1")
    status: WorkerStatus = Field(default=WorkerStatus.IDLE)
    
    concurrency_slots: int = Field(default=4, description="Max simultaneous tasks handled by this worker")
    active_tasks_count: int = Field(default=0)
    current_task_ids: List[str] = Field(default_factory=list)
    
    supported_task_types: List[str] = Field(default_factory=lambda: ["*"])
    tenant_id: str = Field(default="ws-alpha-001")
    
    cpu_usage_percent: float = Field(default=0.0)
    memory_usage_mb: float = Field(default=0.0)
    
    tasks_processed_total: int = Field(default=0)
    tasks_failed_total: int = Field(default=0)
    
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_heartbeat_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def heartbeat(self, cpu: Optional[float] = None, mem: Optional[float] = None) -> None:
        self.last_heartbeat_at = datetime.now(timezone.utc)
        if cpu is not None:
            self.cpu_usage_percent = cpu
        if mem is not None:
            self.memory_usage_mb = mem

    def is_alive(self, timeout_seconds: float = 30.0) -> bool:
        delta = (datetime.now(timezone.utc) - self.last_heartbeat_at).total_seconds()
        return delta <= timeout_seconds

    def has_capacity(self) -> bool:
        return self.status in [WorkerStatus.IDLE, WorkerStatus.BUSY] and self.active_tasks_count < self.concurrency_slots

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "hostname": self.hostname,
            "ip_address": self.ip_address,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "concurrency_slots": self.concurrency_slots,
            "active_tasks_count": self.active_tasks_count,
            "current_task_ids": self.current_task_ids,
            "supported_task_types": self.supported_task_types,
            "tenant_id": self.tenant_id,
            "cpu_usage_percent": self.cpu_usage_percent,
            "memory_usage_mb": self.memory_usage_mb,
            "tasks_processed_total": self.tasks_processed_total,
            "tasks_failed_total": self.tasks_failed_total,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            "is_alive": self.is_alive(),
            "has_capacity": self.has_capacity(),
            "metadata": self.metadata,
        }
