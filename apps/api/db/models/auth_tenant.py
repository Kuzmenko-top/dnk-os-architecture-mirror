# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/auth_tenant.py"
# purpose: "ORM Model representing an isolated Multi-Tenant Organization in DNK OS."
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


class TenantStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PROVISIONING = "PROVISIONING"
    ARCHIVED = "ARCHIVED"


class TenantTier(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"
    CUSTOM = "CUSTOM"


class AuthTenant(BaseModel):
    """Represents an isolated tenant organization within DNK OS with quotas, tiers, and settings."""
    
    id: str = Field(default_factory=lambda: f"tenant_{uuid.uuid4().hex[:12]}")
    name: str = Field(..., description="Organization or workspace name")
    slug: str = Field(..., description="Unique URL slug for tenant routing")
    status: TenantStatus = Field(default=TenantStatus.ACTIVE)
    tier: TenantTier = Field(default=TenantTier.PRO)
    
    # Quotas & Limits
    max_users: int = Field(default=50, description="Maximum concurrent users")
    max_api_keys: int = Field(default=20, description="Maximum API keys")
    max_storage_gb: int = Field(default=100, description="Storage quota in GB")
    rate_limit_rpm: int = Field(default=1000, description="Rate limit requests per minute")
    
    # Metadata & Custom Attributes
    domains: List[str] = Field(default_factory=list, description="Associated custom domains")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary tenant metadata")
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE

    def update_status(self, new_status: TenantStatus) -> None:
        self.status = new_status
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "status": self.status.value,
            "tier": self.tier.value,
            "max_users": self.max_users,
            "max_api_keys": self.max_api_keys,
            "max_storage_gb": self.max_storage_gb,
            "rate_limit_rpm": self.rate_limit_rpm,
            "domains": self.domains,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
