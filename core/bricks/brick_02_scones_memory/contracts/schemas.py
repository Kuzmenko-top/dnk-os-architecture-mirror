# --- DNK-MRH-HEADER ---
# mrh_id: "core/bricks/brick_02_scones_memory/contracts/schemas.py"
# purpose: "Pydantic contract schemas for Brick 02: SCONES Memory & Knowledge Hub."
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


class MemoryRecord(BaseModel):
    topic: str
    content: str
    category: str = "general"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0


class ErrorDistillationQuery(BaseModel):
    error_text: str
    service: Optional[str] = None


class ErrorDistillationSolution(BaseModel):
    root_cause: str
    prescribed_fix: str
    confidence: float = 1.0
