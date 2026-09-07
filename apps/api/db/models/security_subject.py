# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_security_subject"
# purpose: "ORM Model for Security Subject (User, Service Account, or Agent) (DNK-SECURITY-001 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON
from apps.api.db.models.workspace import Base


class SecuritySubjectModel(Base):
    __tablename__ = "security_subjects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(64), nullable=False, index=True)
    subject_type = Column(String(32), nullable=False, default="user")  # user, service, agent
    subject_identifier = Column(String(128), nullable=False, index=True)  # email, agent_id, service_name
    display_name = Column(String(128), nullable=False, default="Subject")
    status = Column(String(32), nullable=False, default="active")  # active, suspended, locked
    trust_score = Column(Float, nullable=False, default=1.0)  # 0.0 - 1.0 dynamic trust score
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    roles = Column(JSON, nullable=False, default=list)  # list of role_ids or names
    attributes = Column(JSON, nullable=False, default=dict)  # arbitrary subject attributes (department, clearance, etc.)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "subject_type": self.subject_type,
            "subject_identifier": self.subject_identifier,
            "display_name": self.display_name,
            "status": self.status,
            "trust_score": self.trust_score,
            "mfa_enabled": self.mfa_enabled,
            "roles": self.roles,
            "attributes": self.attributes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
