# --- DNK-MRH-HEADER ---
# mrh_id: "core/bricks/brick_01_agentic_brain/contracts/schemas.py"
# purpose: "Pydantic contract schemas for Brick 01: Agentic Brain & Swarm Core."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class AgentTaskRequest(BaseModel):
    task_id: str
    goal: str
    agent_id: str = "gerych_prime"
    context: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 1800


class AgentTaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Any] = None
    turns_used: int = 0
    error: Optional[str] = None
