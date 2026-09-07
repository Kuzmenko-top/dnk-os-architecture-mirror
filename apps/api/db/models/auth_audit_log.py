# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/auth_audit_log.py"
# purpose: "ORM Model representing an Immutable Security & Authorization Audit Log entry in DNK OS."
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
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    USER_LOGIN_SUCCESS = "USER_LOGIN_SUCCESS"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    USER_LOGOUT = "USER_LOGOUT"
    TOKEN_ISSUED = "TOKEN_ISSUED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    API_KEY_CREATED = "API_KEY_CREATED"
    API_KEY_REVOKED = "API_KEY_REVOKED"
    ROLE_ASSIGNED = "ROLE_ASSIGNED"
    ROLE_REVOKED = "ROLE_REVOKED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    TENANT_PROVISIONED = "TENANT_PROVISIONED"
    TENANT_UPDATED = "TENANT_UPDATED"
    SECURITY_ALERT = "SECURITY_ALERT"


class AuditSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AuthAuditLog(BaseModel):
    """Represents a tamper-evident, append-only security audit record."""
    
    id: str = Field(default_factory=lambda: f"audit_{uuid.uuid4().hex[:14]}")
    tenant_id: str = Field(..., description="Tenant ID where event occurred")
    actor_id: str = Field(..., description="User ID, API Key ID, or Agent ID initiating action")
    actor_type: str = Field(default="user", description="'user', 'agent', 'api_key', or 'system'")
    
    event_type: AuditEventType = Field(..., description="Categorized security event type")
    severity: AuditSeverity = Field(default=AuditSeverity.INFO)
    resource: Optional[str] = Field(default=None, description="Target resource affected")
    action: Optional[str] = Field(default=None, description="Action attempted")
    
    ip_address: Optional[str] = Field(default=None)
    user_agent: Optional[str] = Field(default=None)
    trace_id: Optional[str] = Field(default=None, description="W3C Trace ID if executed within trace context")
    
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured contextual event metadata")
    checksum: Optional[str] = Field(default=None, description="Cryptographic tamper-evident hash of event content")
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_checksum(self) -> str:
        """Calculate tamper-evident SHA-256 hash across immutable audit payload."""
        payload = f"{self.id}|{self.tenant_id}|{self.actor_id}|{self.event_type.value}|{self.timestamp.isoformat()}|{json.dumps(self.details, sort_keys=True)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def seal(self) -> None:
        """Seal the log record with tamper-evident checksum."""
        self.checksum = self.compute_checksum()

    def verify_integrity(self) -> bool:
        """Verify that record has not been altered."""
        if not self.checksum:
            return False
        return self.compute_checksum() == self.checksum

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "resource": self.resource,
            "action": self.action,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "trace_id": self.trace_id,
            "details": self.details,
            "checksum": self.checksum,
            "timestamp": self.timestamp.isoformat(),
        }
