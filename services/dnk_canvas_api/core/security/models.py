# --- DNK-MRH-HEADER ---
# mrh_id: "core/security/models.py"
# purpose: "SQLAlchemy models for security gates and agent timeline"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-13"
# --- END DNK-MRH-HEADER ---
"""SQLAlchemy models for security gates and timeline."""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Enum, String, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class SecurityApproval(Base):
    """Security approval binding model."""
    
    __tablename__ = 'security_approvals'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(PG_UUID(as_uuid=True), nullable=False)
    agent_id = Column(String(255), nullable=False)
    action_name = Column(String(255), nullable=False)
    args_hash = Column(String(64), nullable=False)  # SHA-256
    idempotency_key = Column(String(64), unique=True)
    status = Column(Enum('pending', 'approved', 'rejected', 'timeout_rejected', name='security_approval_status'), default='pending')
    approved_by = Column(String(255), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    timeout_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship to audit logs
    audit_logs = relationship("SecurityAuditLog", back_populates="approval")


class SecurityAuditLog(Base):
    """Security audit log model."""
    
    __tablename__ = 'security_audit_logs'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    approval_id = Column(PG_UUID(as_uuid=True), ForeignKey('security_approvals.id'), nullable=False)
    event_type = Column(String(50), nullable=False)  # approved, rejected, timeout_rejected
    event_payload = Column(JSONB, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship to approval
    approval = relationship("SecurityApproval", back_populates="audit_logs")


class TimelineEvent(Base):
    """Timeline event model for tracking agent actions."""
    
    __tablename__ = 'agent_timeline'
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id = Column(PG_UUID(as_uuid=True), nullable=False)
    agent_id = Column(String(255), nullable=False)
    event_type = Column(String(50), nullable=False)  # action_start, action_end, error
    status = Column(String(50), nullable=True)  # pending, success, failed
    action_name = Column(String(255), nullable=False)
    payload_json = Column(JSONB, nullable=True)
    idempotency_key = Column(String(64), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    
    __table_args__ = (
        Index('idx_timeline_run', 'run_id'),
        Index('idx_timeline_agent', 'agent_id'),
        Index('idx_timeline_timestamp', 'timestamp'),
        Index('idx_timeline_idempotency', 'idempotency_key'),
    )
