# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/stream_ingestion_sink.py"
# purpose: "ORM Model for Stream Ingestion Sink (ClickHouse/OLAP) (DNK-STREAM-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import Column, String, Integer, Boolean, DateTime, JSON

try:
    from apps.api.db.models.workspace import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class StreamIngestionSink(Base):
    """Represents an analytical / OLAP ingestion sink configuration."""
    __tablename__ = "stream_ingestion_sinks"

    id = Column(String(64), primary_key=True, default=lambda: f"snk_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    name = Column(String(128), nullable=False, index=True)
    sink_type = Column(String(32), default="CLICKHOUSE", nullable=False)  # CLICKHOUSE, BIGQUERY, S3, ELASTIC
    source_topic = Column(String(128), nullable=False, index=True)
    target_table = Column(String(128), nullable=False)
    batch_size = Column(Integer, default=1000, nullable=False)
    flush_interval_ms = Column(Integer, default=5000, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    sink_config = Column(JSON, default=dict)
    buffer_stats = Column(JSON, default=dict)  # {"buffered_count": N, "last_flush_at": iso, "total_flushed": N}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"snk_{uuid.uuid4().hex[:12]}"
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "sink_type", None) is None:
            self.sink_type = "CLICKHOUSE"
        if getattr(self, "batch_size", None) is None:
            self.batch_size = 1000
        if getattr(self, "flush_interval_ms", None) is None:
            self.flush_interval_ms = 5000
        if getattr(self, "is_active", None) is None:
            self.is_active = True
        if getattr(self, "sink_config", None) is None:
            self.sink_config = {}
        if getattr(self, "buffer_stats", None) is None:
            self.buffer_stats = {"buffered_count": 0, "total_flushed": 0}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "sink_type": self.sink_type,
            "source_topic": self.source_topic,
            "target_table": self.target_table,
            "batch_size": self.batch_size,
            "flush_interval_ms": self.flush_interval_ms,
            "is_active": self.is_active,
            "sink_config": self.sink_config or {},
            "buffer_stats": self.buffer_stats or {},
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else datetime.now(timezone.utc).isoformat(),
        }
