# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_security_role"
# purpose: "ORM Model for Security Role and Permission Hierarchy (DNK-SECURITY-001 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from apps.api.db.models.workspace import Base


class SecurityRoleModel(Base):
    __tablename__ = "security_roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(64), nullable=False, index=True)
    role_name = Column(String(64), nullable=False, index=True)  # e.g., "admin", "editor", "agent_worker"
    description = Column(String(255), nullable=False, default="")
    is_system_role = Column(Boolean, nullable=False, default=False)
    parent_role_id = Column(String(36), nullable=True)  # hierarchical inheritance
    permissions = Column(JSON, nullable=False, default=list)  # list of permission strings (e.g., ["canvas:read", "canvas:write"])
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "role_name": self.role_name,
            "description": self.description,
            "is_system_role": self.is_system_role,
            "parent_role_id": self.parent_role_id,
            "permissions": self.permissions,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
