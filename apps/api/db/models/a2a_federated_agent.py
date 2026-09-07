# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_a2a_federated_agent"
# purpose: "ORM Model for Federated & External Agent Node Registration in A2A Mesh (DNK-A2A-004 Phase 1)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Float, Boolean
from apps.api.db.models.workspace import Base


class A2AFederatedAgent(Base):
    """Represents an external or internal federated agent node connected to the cross-platform A2A mesh."""
    __tablename__ = "a2a_federated_agents"

    id = Column(String(64), primary_key=True, default=lambda: f"fed_agent_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    agent_name = Column(String(128), nullable=False, index=True)
    platform = Column(String(64), nullable=False, default="custom")  # e.g. "autogpt", "crewai", "langgraph", "claude_code", "opencode", "hermes"
    protocol_version = Column(String(32), nullable=False, default="a2a/v2")
    api_endpoint = Column(String(256), nullable=False)
    streaming_endpoint = Column(String(256), nullable=True)
    auth_token_hash = Column(String(128), nullable=True)  # SHA-256 hash of auth token
    public_key = Column(String(512), nullable=True)
    trust_tier = Column(String(32), nullable=False, default="tier-2")  # tier-0 (kernel), tier-1 (verified), tier-2 (standard), tier-3 (sandboxed)
    capabilities = Column(JSON, nullable=False, default=list)  # list of capability keys e.g. ["code_generation", "web_search"]
    status = Column(String(32), nullable=False, default="active", index=True)  # active, degraded, offline, blacklisted
    max_concurrency = Column(Float, nullable=False, default=5.0)
    current_load = Column(Float, nullable=False, default=0.0)
    reputation_score = Column(Float, nullable=False, default=1.0)
    metadata_json = Column(JSON, nullable=False, default=dict)
    last_heartbeat_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id or "ws-default",
            "agent_name": self.agent_name,
            "platform": self.platform or "custom",
            "protocol_version": self.protocol_version or "a2a/v2",
            "api_endpoint": self.api_endpoint,
            "streaming_endpoint": self.streaming_endpoint,
            "auth_token_hash": self.auth_token_hash,
            "public_key": self.public_key,
            "trust_tier": self.trust_tier or "tier-2",
            "capabilities": self.capabilities or [],
            "status": self.status or "active",
            "max_concurrency": self.max_concurrency if self.max_concurrency is not None else 5.0,
            "current_load": self.current_load if self.current_load is not None else 0.0,
            "reputation_score": self.reputation_score if self.reputation_score is not None else 1.0,
            "metadata": self.metadata_json or {},
            "last_heartbeat_at": self.last_heartbeat_at.isoformat() if self.last_heartbeat_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
