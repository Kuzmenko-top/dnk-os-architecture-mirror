# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/auth_api_key.py"
# purpose: "ORM Model representing an API Key with scopes, rate limits and hashed secret in DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import hmac
import uuid
import secrets
import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ApiKeyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class AuthApiKey(BaseModel):
    """Represents a secret API key for programmatic / M2M access with scopes and rate limits."""
    
    id: str = Field(default_factory=lambda: f"key_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., description="Descriptive label e.g. 'Production Agent Key'")
    tenant_id: str = Field(..., description="Parent tenant ID")
    user_id: Optional[str] = Field(default=None, description="Associated user ID if creator is a user")
    
    # Key prefix and hashed secret
    prefix: str = Field(..., description="First 8 characters of key for identification e.g. 'dnk_live_...'")
    key_hash: str = Field(..., description="SHA-256 hash of the full secret token")
    
    # Permissions & Scopes
    scopes: List[str] = Field(default_factory=lambda: ["read"], description="Allowed permission scopes e.g. ['batch:*', 'stream:read']")
    status: ApiKeyStatus = Field(default=ApiKeyStatus.ACTIVE)
    rate_limit_rpm: int = Field(default=600, description="Rate limit requests per minute for this key")
    allowed_ips: List[str] = Field(default_factory=list, description="Optional IP whitelist for this key")
    
    # Expiration & Tracking
    expires_at: Optional[datetime] = Field(default=None, description="Optional key expiration timestamp")
    last_used_at: Optional[datetime] = Field(default=None)
    last_used_ip: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def generate_key_pair(prefix_name: str = "dnk_live") -> tuple[str, str, str]:
        """
        Generate (full_secret_token, key_prefix, key_hash).
        The raw secret is only displayed once to the user upon creation.
        """
        random_entropy = secrets.token_urlsafe(32)
        full_token = f"{prefix_name}_{random_entropy}"
        prefix = full_token[:12]
        key_hash = hashlib.sha256(full_token.encode("utf-8")).hexdigest()
        return full_token, prefix, key_hash

    def verify_token(self, plain_token: str) -> bool:
        """Constant-time verification of raw token against stored hash."""
        if self.status != ApiKeyStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        computed_hash = hashlib.sha256(plain_token.encode("utf-8")).hexdigest()
        return hmac.compare_digest(computed_hash, self.key_hash)

    def verify_key(self, plain_token: str) -> bool:
        return self.verify_token(plain_token)

    def record_usage(self, client_ip: Optional[str] = None) -> None:
        self.last_used_at = datetime.now(timezone.utc)
        self.last_used_ip = client_ip

    def is_valid(self) -> bool:
        if self.status != ApiKeyStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def revoke(self) -> None:
        self.status = ApiKeyStatus.REVOKED
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "prefix": self.prefix,
            "scopes": self.scopes,
            "status": self.status.value,
            "rate_limit_rpm": self.rate_limit_rpm,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "last_used_ip": self.last_used_ip,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
