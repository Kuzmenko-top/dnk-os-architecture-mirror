# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-MODEL-QUEUE-METRIC"
# purpose: "Queue Metric ORM Model for Task Queue Depth and Latency Analytics"
# canonical_source: true
# alters_files: ["apps/api/db/models/queue_metric.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, Float, Integer
from apps.api.db.models.workspace import Base


class QueueMetric(Base):
    """Represents real-time telemetry and throughput metrics for task queues."""
    __tablename__ = "queue_metrics"

    id = Column(String(64), primary_key=True, default=lambda: f"qm_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    queue_name = Column(String(128), nullable=False, default="default_task_queue", index=True)
    queue_depth = Column(Integer, nullable=False, default=0)
    incoming_rate_tps = Column(Float, nullable=False, default=0.0)
    processing_rate_tps = Column(Float, nullable=False, default=0.0)
    avg_wait_time_ms = Column(Float, nullable=False, default=0.0)
    p95_latency_ms = Column(Float, nullable=False, default=0.0)
    dead_letter_count = Column(Integer, nullable=False, default=0)
    active_workers = Column(Integer, nullable=False, default=0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "queue_name": self.queue_name,
            "queue_depth": int(self.queue_depth or 0),
            "incoming_rate_tps": float(self.incoming_rate_tps or 0.0),
            "processing_rate_tps": float(self.processing_rate_tps or 0.0),
            "avg_wait_time_ms": float(self.avg_wait_time_ms or 0.0),
            "p95_latency_ms": float(self.p95_latency_ms or 0.0),
            "dead_letter_count": int(self.dead_letter_count or 0),
            "active_workers": int(self.active_workers or 0),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
