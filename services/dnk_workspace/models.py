# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_workspace/models.py"
# purpose: "SQLAlchemy models for DNK OS Workspace service database persistence, matching exactly with Alembic schema."
# canonical_source: true
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, Integer, Text, ForeignKey, BigInteger, UniqueConstraint, DateTime, JSON, Float, Index, text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(128), primary_key=True)
    tenant_id = Column(String(128), nullable=False)
    name = Column(String(255), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    state = Column(String(64), nullable=False, default="ACTIVE")
    last_active = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    nodes = relationship("WorkspaceNode", back_populates="workspace", cascade="all, delete-orphan")
    edges = relationship("WorkspaceEdge", back_populates="workspace", cascade="all, delete-orphan")
    prompts = relationship("WorkspacePrompt", back_populates="workspace", cascade="all, delete-orphan")
    diffs = relationship("WorkspaceDiff", back_populates="workspace", cascade="all, delete-orphan")
    approvals = relationship("WorkspaceApproval", back_populates="workspace", cascade="all, delete-orphan")
    snapshots = relationship("WorkspaceSnapshot", back_populates="workspace", cascade="all, delete-orphan")
    commits = relationship("WorkspaceCommit", back_populates="workspace", cascade="all, delete-orphan")
    audit_trail = relationship("WorkspaceAuditTrail", back_populates="workspace", cascade="all, delete-orphan")


class WorkspaceNode(Base):
    __tablename__ = "workspace_nodes"

    id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    node_id = Column(String(128), nullable=False)
    type = Column(String(64), nullable=False)
    label = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)
    data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    workspace = relationship("Workspace", back_populates="nodes")


class WorkspaceEdge(Base):
    __tablename__ = "workspace_edges"

    id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(128), nullable=False)
    target = Column(String(128), nullable=False)
    type = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    workspace = relationship("Workspace", back_populates="edges")


class WorkspacePrompt(Base):
    __tablename__ = "workspace_prompts"

    prompt_id = Column(String(128), primary_key=True)
    task_id = Column(String(128), nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(128), nullable=False)
    user_id = Column(String(128), nullable=False)
    prompt = Column(Text, nullable=False)
    target_node_id = Column(String(128), nullable=True)
    context_parameters = Column(JSON, nullable=False, default=dict)
    status = Column(String(64), nullable=False, default="SUBMITTED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    workspace = relationship("Workspace", back_populates="prompts")


class WorkspaceDiff(Base):
    __tablename__ = "workspace_diffs"

    diff_id = Column(String(128), primary_key=True)
    task_id = Column(String(128), nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(128), nullable=False)
    status = Column(String(64), nullable=False, default="STAGED")
    staged_diff_hash = Column(String(128), nullable=False)
    preview_hash = Column(String(128), nullable=False)
    files = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    workspace = relationship("Workspace", back_populates="diffs")


class WorkspaceApproval(Base):
    __tablename__ = "workspace_approvals"

    approval_id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(128), nullable=False)
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

    workspace = relationship("Workspace", back_populates="approvals")


class WorkspaceSnapshot(Base):
    __tablename__ = "workspace_snapshots"

    snapshot_id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(128), nullable=False)
    pre_hash = Column(String(128), nullable=False)
    nodes_state = Column(JSON, nullable=False)
    edges_state = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False)
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    workspace = relationship("Workspace", back_populates="snapshots")


class WorkspaceCommit(Base):
    __tablename__ = "workspace_commits"

    commit_id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(128), nullable=False)
    status = Column(String(64), nullable=False, default="COMMITTED")
    new_version = Column(Integer, nullable=False)
    diff_id = Column(String(128), nullable=True)
    idempotency_key = Column(String(255), nullable=False)
    committed_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    workspace = relationship("Workspace", back_populates="commits")


class WorkspaceAuditTrail(Base):
    __tablename__ = "workspace_audit_trail"

    event_id = Column(String(128), primary_key=True)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(String(128), nullable=False)
    actor = Column(String(128), nullable=False)
    action = Column(String(128), nullable=False)
    details = Column(JSON, nullable=False, default=dict)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    workspace = relationship("Workspace", back_populates="audit_trail")


class WorkspaceIdempotencyCache(Base):
    __tablename__ = "workspace_idempotency_cache"

    idempotency_key = Column(String(255), primary_key=True)
    workspace_id = Column(String(128), nullable=False)
    tenant_id = Column(String(128), nullable=False)
    response_data = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    user_id = Column(String(128), primary_key=True, nullable=False)
    role = Column(String(32), nullable=False, default="developer")
    invited_by = Column(String(128), nullable=False)
    invited_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    status = Column(String(32), nullable=False, default="active")


class WorkspaceInvitation(Base):
    __tablename__ = "workspace_invitations"

    invitation_id = Column(String(128), primary_key=True, nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="developer")
    invited_by = Column(String(128), nullable=False)
    invited_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(32), nullable=False, default="pending")


class UserWorkspaceContext(Base):
    __tablename__ = "user_workspace_context"

    user_id = Column(String(128), primary_key=True, nullable=False)
    active_workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    last_switched_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    version = Column(Integer, nullable=False, default=1)
