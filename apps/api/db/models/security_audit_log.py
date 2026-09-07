# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_security_audit_log"
# purpose: "ORM Model for Cryptographically Chained Immutable Security Audit Logs (DNK-SECURITY-001 Phase 1)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, JSON
from apps.api.db.models.workspace import Base


class SecurityAuditLogModel(Base):
    __tablename__ = "security_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String(64), nullable=False, index=True)
    subject_id = Column(String(64), nullable=False, index=True)
    subject_type = Column(String(32), nullable=False, default="user")
    action = Column(String(64), nullable=False, index=True)
    resource = Column(String(128), nullable=False, index=True)
    decision = Column(String(16), nullable=False, default="ALLOWED")  # ALLOWED or DENIED
    reason = Column(String(255), nullable=False, default="")
    policy_id = Column(String(36), nullable=True)

    # Request Context Snapshot
    ip_address = Column(String(45), nullable=False, default="127.0.0.1")
    geo_country = Column(String(8), nullable=True)
    user_agent = Column(String(255), nullable=True)
    trust_score = Column(Float, nullable=False, default=1.0)
    extra_context = Column(JSON, nullable=False, default=dict)

    # Cryptographic Chain Validation
    prev_hash = Column(String(64), nullable=False, default="0" * 64)
    current_hash = Column(String(64), nullable=False, index=True)

    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "subject_id": self.subject_id,
            "subject_type": self.subject_type,
            "action": self.action,
            "resource": self.resource,
            "decision": self.decision,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "ip_address": self.ip_address,
            "geo_country": self.geo_country,
            "user_agent": self.user_agent,
            "trust_score": self.trust_score,
            "extra_context": self.extra_context,
            "prev_hash": self.prev_hash,
            "current_hash": self.current_hash,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
