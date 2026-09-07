# --- DNK-MRH-HEADER ---
# mrh_id: "core_models_security"
# purpose: "Security Policy and Gate Decision models for Gate Security framework"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel

@dataclass
class GateDecision:
    allowed: bool
    reason: str
    expiry: Optional[int] = None  # TTL in seconds
    approval_run_id: Optional[UUID] = None  # якщо потрібен manual approval

class SecurityPolicy(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    action_patterns: List[str]  # наприклад, ["file.write", "db.delete"]
    conditions: Dict[str, Any]  # наприклад, {"max_file_size": 1024*1024}
    require_approval: bool = False
    created_at: int
    updated_at: int
