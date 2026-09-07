# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_a2a_stream_session"
# purpose: "ORM Model for Real-Time SSE/gRPC Streaming Sessions in A2A Mesh (DNK-A2A-004 Phase 1)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Integer, Float, Boolean
from apps.api.db.models.workspace import Base


class A2AStreamSession(Base):
    """Tracks active and historical real-time streaming channels for CoT, tool execution, and token flows."""
    __tablename__ = "a2a_stream_sessions"

    id = Column(String(64), primary_key=True, default=lambda: f"stream_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    session_token = Column(String(128), nullable=False, unique=True, index=True)
    sender_agent_id = Column(String(64), nullable=False, index=True)
    receiver_agent_id = Column(String(64), nullable=False, index=True)
    stream_type = Column(String(32), nullable=False, default="cot_stream")  # cot_stream, token_stream, tool_call_stream, artifact_stream
    status = Column(String(32), nullable=False, default="open", index=True)  # open, active, paused, closed, error
    backpressure_window_size = Column(Integer, nullable=False, default=50)
    messages_streamed = Column(Integer, nullable=False, default=0)
    bytes_streamed = Column(Float, nullable=False, default=0.0)
    error_message = Column(String(512), nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    opened_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    closed_at = Column(DateTime, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id or "ws-default",
            "session_token": self.session_token,
            "sender_agent_id": self.sender_agent_id,
            "receiver_agent_id": self.receiver_agent_id,
            "stream_type": self.stream_type or "cot_stream",
            "status": self.status or "open",
            "backpressure_window_size": self.backpressure_window_size if self.backpressure_window_size is not None else 50,
            "messages_streamed": self.messages_streamed if self.messages_streamed is not None else 0,
            "bytes_streamed": self.bytes_streamed if self.bytes_streamed is not None else 0.0,
            "error_message": self.error_message,
            "metadata": self.metadata_json or {},
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }
