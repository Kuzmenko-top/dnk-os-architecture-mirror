# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/models/trace_metric_aggregation.py"
# purpose: "ORM Model for Trace Metric Aggregation & Latency Percentiles (DNK-OBSERVE-001)"
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
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON

try:
    from apps.api.db.models.workspace import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


class TraceMetricAggregation(Base):
    """Represents pre-aggregated latency metrics, error rates, and throughput computed from trace spans."""
    __tablename__ = "trace_metric_aggregations"

    id = Column(String(64), primary_key=True, default=lambda: f"tma_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, index=True, default="ws-default")
    service_name = Column(String(128), nullable=False, index=True)
    operation = Column(String(255), nullable=False, index=True)
    time_bucket = Column(DateTime, nullable=False, index=True)
    call_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    error_rate = Column(Float, default=0.0, nullable=False)
    p50_ms = Column(Float, default=0.0, nullable=False)
    p95_ms = Column(Float, default=0.0, nullable=False)
    p99_ms = Column(Float, default=0.0, nullable=False)
    min_ms = Column(Float, default=0.0, nullable=False)
    max_ms = Column(Float, default=0.0, nullable=False)
    avg_ms = Column(Float, default=0.0, nullable=False)
    metadata_info = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        if getattr(self, "id", None) is None:
            self.id = f"tma_{uuid.uuid4().hex[:12]}"
        if getattr(self, "workspace_id", None) is None:
            self.workspace_id = "ws-default"
        if getattr(self, "call_count", None) is None:
            self.call_count = 0
        if getattr(self, "error_count", None) is None:
            self.error_count = 0
        if getattr(self, "error_rate", None) is None:
            self.error_rate = (self.error_count / self.call_count) if self.call_count > 0 else 0.0
        if getattr(self, "metadata_info", None) is None:
            self.metadata_info = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "service_name": self.service_name,
            "operation": self.operation,
            "time_bucket": self.time_bucket.isoformat() if self.time_bucket else datetime.now(timezone.utc).isoformat(),
            "call_count": self.call_count,
            "error_count": self.error_count,
            "error_rate": self.error_rate,
            "p50_ms": self.p50_ms,
            "p95_ms": self.p95_ms,
            "p99_ms": self.p99_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "avg_ms": self.avg_ms,
            "metadata_info": self.metadata_info or {},
            "created_at": self.created_at.isoformat() if self.created_at else datetime.now(timezone.utc).isoformat(),
        }
