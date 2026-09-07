# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_workspace"
# purpose: "SQLAlchemy 2.0 ORM Declarative Models for DNK OS User Workspace Persistence"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Index,
    text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class WorkspaceModel(Base):
    __tablename__ = "workspaces"

    id = Column(String(128), primary_key=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    state = Column(String(64), nullable=False, default="ACTIVE")
    last_active = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    nodes = relationship("WorkspaceNodeModel", back_populates="workspace", cascade="all, delete-orphan")
    edges = relationship("WorkspaceEdgeModel", back_populates="workspace", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_workspaces_tenant_id", "tenant_id"),
        Index("ix_workspaces_tenant_state", "tenant_id", "state"),
    )


class WorkspaceNodeModel(Base):
    __tablename__ = "workspace_nodes"

    id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    node_id = Column(String(128), nullable=False)
    type = Column(String(64), nullable=False)
    label = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    workspace = relationship("WorkspaceModel", back_populates="nodes")

    __table_args__ = (
        Index("ix_workspace_nodes_ws_node", "workspace_id", "node_id", unique=True),
    )


class WorkspaceEdgeModel(Base):
    __tablename__ = "workspace_edges"

    id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(128), nullable=False)
    target = Column(String(128), nullable=False)
    type = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    workspace = relationship("WorkspaceModel", back_populates="edges")

    __table_args__ = (
        Index("ix_workspace_edges_ws_source_target", "workspace_id", "source", "target"),
    )


class WorkspacePromptModel(Base):
    __tablename__ = "workspace_prompts"

    prompt_id = Column(String(128), primary_key=True)
    task_id = Column(String(128), nullable=False, index=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    user_id = Column(String(128), nullable=False)
    prompt = Column(Text, nullable=False)
    target_node_id = Column(String(128), nullable=True)
    context_parameters = Column(JSON, nullable=True)
    status = Column(String(64), nullable=False, default="SUBMITTED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_workspace_prompts_ws_tenant", "workspace_id", "tenant_id"),
    )


class WorkspaceDiffModel(Base):
    __tablename__ = "workspace_diffs"

    diff_id = Column(String(128), primary_key=True)
    task_id = Column(String(128), nullable=False, index=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    status = Column(String(64), nullable=False, default="STAGED")
    staged_diff_hash = Column(String(128), nullable=False, index=True)
    preview_hash = Column(String(128), nullable=False)
    files = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_workspace_diffs_ws_tenant", "workspace_id", "tenant_id"),
    )


class WorkspaceApprovalModel(Base):
    __tablename__ = "workspace_approvals"

    approval_id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    staged_diff_hash = Column(String(128), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(64), nullable=False, default="PENDING")
    approval_signature = Column(String(128), nullable=False)
    created_by = Column(String(128), nullable=False)
    approved_by = Column(String(128), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(String(128), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_workspace_approvals_ws_status", "workspace_id", "status"),
        Index("ix_workspace_approvals_tenant", "tenant_id"),
    )


class WorkspaceSnapshotModel(Base):
    __tablename__ = "workspace_snapshots"

    snapshot_id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    pre_hash = Column(String(128), nullable=False)
    nodes_state = Column(JSON, nullable=False)
    edges_state = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False)
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_workspace_snapshots_ws_tenant", "workspace_id", "tenant_id"),
    )


class WorkspaceCommitModel(Base):
    __tablename__ = "workspace_commits"

    commit_id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    status = Column(String(64), nullable=False, default="COMMITTED")
    new_version = Column(Integer, nullable=False)
    diff_id = Column(String(128), nullable=True)
    idempotency_key = Column(String(255), nullable=False, index=True)
    committed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_workspace_commits_ws_idempotency", "workspace_id", "idempotency_key"),
    )


class WorkspaceAuditModel(Base):
    __tablename__ = "workspace_audit_trail"

    event_id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    actor = Column(String(128), nullable=False)
    action = Column(String(128), nullable=False)
    details = Column(JSON, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_workspace_audit_ws_tenant", "workspace_id", "tenant_id"),
        Index("ix_workspace_audit_timestamp", "timestamp"),
    )


class WorkspaceIdempotencyModel(Base):
    __tablename__ = "workspace_idempotency_cache"

    idempotency_key = Column(String(255), primary_key=True)
    workspace_id = Column(String(128), nullable=False, index=True)
    tenant_id = Column(String(128), nullable=False, index=True)
    response_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
