# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_security_token_revocation"
# purpose: "ORM Model for JWT/Token Revocation Blacklist and Token Rotation (DNK-SECURITY-001 Phase 1)"
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


class SecurityTokenRevocationModel(Base):
    __tablename__ = "security_token_revocations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    token_jti = Column(String(128), unique=True, nullable=False, index=True)
    subject_id = Column(String(64), nullable=False, index=True)
    token_type = Column(String(32), nullable=False, default="access")  # access, refresh, api_key
    revocation_reason = Column(String(255), nullable=False, default="User logout / Security trigger")
    is_revoked = Column(Boolean, nullable=False, default=True)
    revoked_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "token_jti": self.token_jti,
            "subject_id": self.subject_id,
            "token_type": self.token_type,
            "revocation_reason": self.revocation_reason,
            "is_revoked": self.is_revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
