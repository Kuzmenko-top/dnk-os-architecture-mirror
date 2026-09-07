# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/auth_permission.py"
# purpose: "ORM Model representing a granular RBAC/ABAC permission in DNK OS."
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


class PermissionAction(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    ADMIN = "ADMIN"
    ALL = "*"


class AuthPermission(BaseModel):
    """Represents a fine-grained permission defining resource and allowable action."""
    
    id: str = Field(default_factory=lambda: f"perm_{uuid.uuid4().hex[:10]}")
    code: str = Field(..., description="Unique dot/colon notation code e.g. 'stream:events:read' or 'batch:jobs:create'")
    resource: str = Field(..., description="Resource name e.g. 'stream', 'observe', 'batch', 'auth'")
    action: PermissionAction = Field(default=PermissionAction.READ)
    description: Optional[str] = Field(default=None)
    
    # ABAC Condition Constraints
    conditions: Dict[str, Any] = Field(default_factory=dict, description="ABAC attribute constraints e.g. {'ip_whitelist': ['10.0.0.0/8']}")
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def matches(self, target_code: str) -> bool:
        if self.code == "*" or self.code == target_code:
            return True
        if self.code.endswith(":*") and target_code.startswith(self.code[:-1]):
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "resource": self.resource,
            "action": self.action.value,
            "description": self.description,
            "conditions": self.conditions,
            "created_at": self.created_at.isoformat(),
        }
