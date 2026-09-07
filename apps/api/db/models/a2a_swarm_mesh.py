# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-MODEL-SWARM"
# purpose: "A2A Swarm Mesh Topology ORM Model"
# canonical_source: true
# alters_files: ["apps/api/db/models/a2a_swarm_mesh.py"]
# triggers_tasks: ["DNK-A2A-003-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from sqlalchemy import Column, String, DateTime, JSON, Integer, Float
from apps.api.db.models.workspace import Base


class A2ASwarmMesh(Base):
    """Represents a logical swarm cluster topology and configuration."""
    __tablename__ = "a2a_swarm_meshes"

    id = Column(String(64), primary_key=True, default=lambda: f"mesh_{uuid.uuid4().hex[:12]}")
    workspace_id = Column(String(64), nullable=False, default="ws-default", index=True)
    mesh_name = Column(String(128), nullable=False, index=True)
    topology_type = Column(String(64), nullable=False, default="mesh")  # mesh, star, hierarchical
    leader_agent_id = Column(String(64), nullable=True)
    active_nodes_count = Column(Integer, nullable=False, default=0)
    quorum_percentage = Column(Float, nullable=False, default=66.6)
    consensus_strategy = Column(String(64), nullable=False, default="raft_quorum")  # raft_quorum, pbft_weighted
    topology_metadata = Column(JSON, nullable=False, default=dict)
    status = Column(String(32), nullable=False, default="healthy")  # healthy, degraded, partition
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "workspace_id": self.workspace_id,
            "mesh_name": self.mesh_name,
            "topology_type": self.topology_type or "mesh",
            "leader_agent_id": self.leader_agent_id,
            "active_nodes_count": self.active_nodes_count if self.active_nodes_count is not None else 0,
            "quorum_percentage": self.quorum_percentage if self.quorum_percentage is not None else 66.6,
            "consensus_strategy": self.consensus_strategy or "raft_quorum",
            "topology_metadata": self.topology_metadata or {},
            "status": self.status or "healthy",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
