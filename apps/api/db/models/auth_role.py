# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/auth_role.py"
# purpose: "ORM Model representing an RBAC Role with inheritance & permissions in DNK OS."
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
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class RoleScope(str, Enum):
    SYSTEM = "SYSTEM"
    TENANT = "TENANT"
    WORKSPACE = "WORKSPACE"


class AuthRole(BaseModel):
    """Represents a security role containing permissions with hierarchical inheritance support."""
    
    id: str = Field(default_factory=lambda: f"role_{uuid.uuid4().hex[:10]}")
    name: str = Field(..., description="Role identifier (e.g. admin, developer, viewer, auditor)")
    display_name: str = Field(..., description="Human-readable role name")
    description: Optional[str] = Field(default=None)
    tenant_id: Optional[str] = Field(default=None, description="None for global system roles, tenant ID for custom tenant roles")
    scope: RoleScope = Field(default=RoleScope.TENANT)
    
    # Permissions & Inheritance
    permissions: List[str] = Field(default_factory=list, description="List of permission codes (e.g. 'batch:jobs:read')")
    inherited_roles: List[str] = Field(default_factory=list, description="List of parent role names inherited by this role")
    is_system_role: bool = Field(default=False, description="System default immutable roles")
    is_active: bool = Field(default=True, description="Whether the role is active")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def has_direct_permission(self, perm_code: str) -> bool:
        if "*" in self.permissions or perm_code in self.permissions:
            return True
        # Check wildcard prefixes e.g. "batch:*" matches "batch:jobs:read"
        for p in self.permissions:
            if p.endswith(":*") and perm_code.startswith(p[:-1]):
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "tenant_id": self.tenant_id,
            "scope": self.scope.value,
            "permissions": self.permissions,
            "inherited_roles": self.inherited_roles,
            "is_system_role": self.is_system_role,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
