# --- DNK-MRH-HEADER ---
# mrh_id: "core/bricks/brick_06_web_api_shell/contracts/schemas.py"
# purpose: "Pydantic contract schemas for Brick 06: Command Center Web UI & API Gateway Shell."
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


class GatewayHealthResponse(BaseModel):
    status: str = "ok"
    version: str = "2.0.0"
    active_services: List[str] = Field(default_factory=list)
    uptime_seconds: float = 0.0


class APISessionToken(BaseModel):
    token: str
    user_id: str
    role: str = "admin"
    expires_at: int
