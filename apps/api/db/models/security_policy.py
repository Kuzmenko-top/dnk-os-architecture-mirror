# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_security_policy"
# purpose: "ORM Model for Dynamic RBAC/ABAC Security Policies (DNK-SECURITY-001 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON
from apps.api.db.models.workspace import Base


class SecurityPolicyModel(Base):
    __tablename__ = "security_policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(64), nullable=False, index=True)
    policy_name = Column(String(128), nullable=False, index=True)
    description = Column(String(255), nullable=False, default="")
    effect = Column(String(16), nullable=False, default="ALLOW")  # ALLOW or DENY
    priority = Column(Integer, nullable=False, default=100)  # Lower number = higher priority (evaluated first)
    is_active = Column(Boolean, nullable=False, default=True)

    # Subject conditions
    subject_roles = Column(JSON, nullable=False, default=list)  # Target roles or ["*"]
    subject_types = Column(JSON, nullable=False, default=list)  # ["user", "service", "agent"]
    min_trust_score = Column(JSON, nullable=True)  # float or None

    # Target resources & actions
    resource_patterns = Column(JSON, nullable=False, default=list)  # e.g., ["canvas:*", "api:v3:canvas"]
    action_patterns = Column(JSON, nullable=False, default=list)  # e.g., ["read", "write", "*"]

    # ABAC Context rules
    ip_allowlist = Column(JSON, nullable=False, default=list)  # CIDRs or exact IPs (empty means any)
    ip_denylist = Column(JSON, nullable=False, default=list)
    allowed_geo_countries = Column(JSON, nullable=False, default=list)  # e.g., ["UA", "US", "DE"]
    time_window_start_utc = Column(String(8), nullable=True)  # "08:00:00"
    time_window_end_utc = Column(String(8), nullable=True)  # "20:00:00"
    require_mfa = Column(Boolean, nullable=False, default=False)
    max_velocity_rpm = Column(Integer, nullable=True)  # Max requests per minute

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "policy_name": self.policy_name,
            "description": self.description,
            "effect": self.effect,
            "priority": self.priority,
            "is_active": self.is_active,
            "subject_roles": self.subject_roles,
            "subject_types": self.subject_types,
            "min_trust_score": self.min_trust_score,
            "resource_patterns": self.resource_patterns,
            "action_patterns": self.action_patterns,
            "ip_allowlist": self.ip_allowlist,
            "ip_denylist": self.ip_denylist,
            "allowed_geo_countries": self.allowed_geo_countries,
            "time_window_start_utc": self.time_window_start_utc,
            "time_window_end_utc": self.time_window_end_utc,
            "require_mfa": self.require_mfa,
            "max_velocity_rpm": self.max_velocity_rpm,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
