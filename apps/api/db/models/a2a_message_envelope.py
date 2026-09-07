# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_a2a_message_envelope"
# purpose: "ORM Model for Standardized A2A Wire Message Envelopes (DNK-A2A-004 Phase 1)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Integer, Float
from apps.api.db.models.workspace import Base


class A2AMessageEnvelope(Base):
    """Represents a discrete or streaming wire envelope transferred across the A2A mesh."""
    __tablename__ = "a2a_message_envelopes"

    id = Column(String(64), primary_key=True, default=lambda: f"env_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    trace_id = Column(String(64), nullable=False, index=True)
    span_id = Column(String(64), nullable=False)
    parent_span_id = Column(String(64), nullable=True)
    sender_agent_id = Column(String(64), nullable=False, index=True)
    recipient_agent_id = Column(String(64), nullable=False, index=True)
    protocol_pattern = Column(String(32), nullable=False, default="peer-to-peer")  # peer-to-peer, supervisor-worker, broadcast, pubsub
    method = Column(String(128), nullable=False, index=True)  # e.g. "task.delegate", "agent.cot_stream", "tool.execute"
    payload = Column(JSON, nullable=False, default=dict)
    headers = Column(JSON, nullable=False, default=dict)
    signature_hash = Column(String(128), nullable=True)  # HMAC-SHA256 signature
    status = Column(String(32), nullable=False, default="delivered")  # queued, in_transit, delivered, acked, failed, dead_letter
    delivery_attempts = Column(Integer, nullable=False, default=1)
    latency_ms = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id or "ws-default",
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "sender_agent_id": self.sender_agent_id,
            "recipient_agent_id": self.recipient_agent_id,
            "protocol_pattern": self.protocol_pattern or "peer-to-peer",
            "method": self.method,
            "payload": self.payload or {},
            "headers": self.headers or {},
            "signature_hash": self.signature_hash,
            "status": self.status or "delivered",
            "delivery_attempts": self.delivery_attempts if self.delivery_attempts is not None else 1,
            "latency_ms": self.latency_ms if self.latency_ms is not None else 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
