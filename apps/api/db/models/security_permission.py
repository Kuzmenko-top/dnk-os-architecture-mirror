# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_security_permission"
# purpose: "ORM Model for Atomic Security Permissions (DNK-SECURITY-001 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from apps.api.db.models.workspace import Base


class SecurityPermissionModel(Base):
    __tablename__ = "security_permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource = Column(String(64), nullable=False, index=True)  # e.g., "canvas", "shopify", "media", "system"
    action = Column(String(32), nullable=False, index=True)  # e.g., "read", "write", "delete", "execute", "admin"
    permission_key = Column(String(128), unique=True, nullable=False, index=True)  # e.g., "canvas:write"
    description = Column(String(255), nullable=False, default="")
    is_system = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "resource": self.resource,
            "action": self.action,
            "permission_key": self.permission_key,
            "description": self.description,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
