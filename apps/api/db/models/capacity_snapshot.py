# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-MODEL-CAPACITY-SNAPSHOT"
# purpose: "Capacity Snapshot ORM Model for Telemetry and Node Metric Tracking"
# canonical_source: true
# alters_files: ["apps/api/db/models/capacity_snapshot.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer
from apps.api.db.models.workspace import Base


class CapacitySnapshot(Base):
    """Represents a point-in-time telemetry snapshot of cluster and node capacity."""
    __tablename__ = "capacity_snapshots"

    id = Column(String(64), primary_key=True, default=lambda: f"cap_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    cluster_id = Column(String(64), nullable=False, default="default-cluster", index=True)
    node_id = Column(String(64), nullable=False, default="node-master", index=True)
    cpu_utilization_pct = Column(Float, nullable=False, default=0.0)
    memory_utilization_pct = Column(Float, nullable=False, default=0.0)
    gpu_utilization_pct = Column(Float, nullable=False, default=0.0)
    network_iops_mbps = Column(Float, nullable=False, default=0.0)
    active_agents_count = Column(Integer, nullable=False, default=0)
    queue_depth = Column(Integer, nullable=False, default=0)
    token_throughput_tps = Column(Float, nullable=False, default=0.0)
    metrics_payload = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "cluster_id": self.cluster_id,
            "node_id": self.node_id,
            "cpu_utilization_pct": float(self.cpu_utilization_pct or 0.0),
            "memory_utilization_pct": float(self.memory_utilization_pct or 0.0),
            "gpu_utilization_pct": float(self.gpu_utilization_pct or 0.0),
            "network_iops_mbps": float(self.network_iops_mbps or 0.0),
            "active_agents_count": int(self.active_agents_count or 0),
            "queue_depth": int(self.queue_depth or 0),
            "token_throughput_tps": float(self.token_throughput_tps or 0.0),
            "metrics_payload": self.metrics_payload or {},
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
