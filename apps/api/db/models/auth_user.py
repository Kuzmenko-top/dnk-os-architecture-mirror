# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/auth_user.py"
# purpose: "ORM Model representing an Authenticated User in DNK OS Multi-Tenant System."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import uuid
import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class UserAccountStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INVITED = "INVITED"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class UserAuthProvider(str, Enum):
    LOCAL = "LOCAL"
    GOOGLE = "GOOGLE"
    GITHUB = "GITHUB"
    OIDC = "OIDC"
    SAML = "SAML"


class AuthUser(BaseModel):
    """Represents a user account bound to a specific tenant with credentials, roles, and status."""
    
    id: str = Field(default_factory=lambda: f"usr_{uuid.uuid4().hex[:12]}")
    tenant_id: str = Field(..., description="Parent tenant ID for strict multi-tenant isolation")
    email: str = Field(..., description="Unique email address within the tenant")
    display_name: str = Field(..., description="Full name or display pseudonym")
    
    # Credentials & Security
    password_hash: Optional[str] = Field(default=None, description="Hashed password for LOCAL provider")
    salt: Optional[str] = Field(default=None, description="Cryptographic salt for local password hashing")
    provider: UserAuthProvider = Field(default=UserAuthProvider.LOCAL)
    provider_user_id: Optional[str] = Field(default=None, description="External provider subject ID")
    
    # Status & MFA
    status: UserAccountStatus = Field(default=UserAccountStatus.ACTIVE)
    mfa_enabled: bool = Field(default=False)
    mfa_secret: Optional[str] = Field(default=None)
    email_verified: bool = Field(default=False)
    
    # Roles & Scopes
    roles: List[str] = Field(default_factory=lambda: ["viewer"], description="List of assigned role names/IDs")
    custom_permissions: List[str] = Field(default_factory=list, description="Directly assigned permission codes")
    is_superadmin: bool = Field(default=False, description="Global superadmin status across tenants")
    
    # Security tracking
    failed_login_attempts: int = Field(default=0)
    login_count: int = Field(default=0)
    last_login_at: Optional[datetime] = Field(default=None)
    last_login_ip: Optional[str] = Field(default=None)
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @property
    def direct_permissions(self) -> List[str]:
        return self.custom_permissions

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
        """Generate SHA-256 password hash with salt."""
        s = salt or uuid.uuid4().hex
        computed = hashlib.sha256(f"{password}:{s}".encode("utf-8")).hexdigest()
        return computed, s

    def set_password(self, password: str) -> None:
        self.password_hash, self.salt = self.hash_password(password)

    def record_failed_login(self) -> None:
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.status = UserAccountStatus.SUSPENDED

    def verify_password(self, password: str) -> bool:
        """Verify given plain password against stored hash and salt."""
        if not self.password_hash or not self.salt:
            return False
        computed = hashlib.sha256(f"{password}:{self.salt}".encode("utf-8")).hexdigest()
        return computed == self.password_hash

    def is_active(self) -> bool:
        return self.status == UserAccountStatus.ACTIVE

    def record_login(self) -> None:
        self.last_login_at = datetime.now(timezone.utc)
        self.login_count += 1

    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "email": self.email,
            "display_name": self.display_name,
            "provider": self.provider.value,
            "provider_user_id": self.provider_user_id,
            "status": self.status.value,
            "mfa_enabled": self.mfa_enabled,
            "email_verified": self.email_verified,
            "roles": self.roles,
            "custom_permissions": self.custom_permissions,
            "failed_login_attempts": self.failed_login_attempts,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "last_login_ip": self.last_login_ip,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_secrets:
            data["password_hash"] = self.password_hash
            data["salt"] = self.salt
            data["mfa_secret"] = self.mfa_secret
        return data
