# --- DNK-MRH-HEADER ---
# mrh_id: "core/error_distillation/models.py"
# purpose: "DTO models for Error events and distilled cognitive error memory."
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, UTC
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ErrorEvent(BaseModel):
    """Information representing a raw worker exception event."""
    task_id: str
    execution_id: str
    agent_id: str
    tenant_id: str
    workspace_id: str
    error_type: str  # transient, validation, dependency, logic, security
    error_code: int  # HTTP code, custom code, or exit status
    input_hash: str  # Hash of task input/params for idempotency tracing
    retry_count: int = 0
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

class DistilledErrorMemory(BaseModel):
    """Synthesized long-term error memory with root-cause insights and workarounds."""
    fingerprint: str
    problem: str
    root_cause: str
    failed_action: str
    workaround: str
    confidence: float = 1.0
    occurrence_count: int = 1
    tenant_id: str
    workspace_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
