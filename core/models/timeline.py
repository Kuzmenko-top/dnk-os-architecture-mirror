# --- DNK-MRH-HEADER ---
# mrh_id: "core_models_timeline"
# purpose: "Domain models for agent executions timeline (Agent, Run, Task, Event)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, UTC
from typing import Optional, Any, Dict
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class Agent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class Run(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    run_type: str
    status: str  # pending, running, completed, failed, interrupted
    idempotency_key: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    task_type: str
    status: str  # pending, running, completed, failed
    payload: Dict[str, Any] = Field(default_factory=dict)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

class Event(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    task_id: Optional[UUID] = None
    event_type: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
