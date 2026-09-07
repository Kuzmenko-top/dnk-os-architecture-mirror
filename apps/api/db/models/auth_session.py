# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/auth_session.py"
# purpose: "ORM Model representing an Authenticated User Session with device fingerprinting in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class AuthSession(BaseModel):
    """Represents an active user session with device fingerprinting and refresh token linkage."""
    
    id: str = Field(default_factory=lambda: f"sess_{uuid.uuid4().hex[:14]}")
    tenant_id: str = Field(..., description="Parent tenant ID")
    user_id: str = Field(..., description="User ID owning the session")
    
    status: SessionStatus = Field(default=SessionStatus.ACTIVE)
    refresh_token_hash: Optional[str] = Field(default=None, description="Hash of current refresh token")
    
    # Device & Client Fingerprinting
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    device_fingerprint: Optional[str] = Field(default=None, description="SHA-256 fingerprint of device attributes")
    
    # Expiry & Activity
    expires_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7), description="Session expiration timestamp")
    last_active_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_valid(self) -> bool:
        if self.status != SessionStatus.ACTIVE:
            return False
        if datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def touch(self) -> None:
        self.last_active_at = datetime.now(timezone.utc)

    def revoke(self) -> None:
        self.status = SessionStatus.REVOKED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_fingerprint": self.device_fingerprint,
            "expires_at": self.expires_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
