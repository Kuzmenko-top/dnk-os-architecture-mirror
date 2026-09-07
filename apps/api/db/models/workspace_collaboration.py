# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_models_workspace_collaboration"
# purpose: "SQLAlchemy ORM models for Workspace Members, Workspace Invitations, and User Workspace Context"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    CheckConstraint
)

from apps.api.db.models.workspace import Base


class WorkspaceMemberModel(Base):
    __tablename__ = "workspace_members"

    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    user_id = Column(String(128), primary_key=True, nullable=False)
    role = Column(String(32), nullable=False, default="developer")
    invited_by = Column(String(128), nullable=False)
    invited_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    status = Column(String(32), nullable=False, default="active")

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'developer', 'viewer')", name="check_workspace_member_role"),
        CheckConstraint("status IN ('active', 'inactive', 'suspended')", name="check_workspace_member_status"),
        Index("ix_workspace_members_user_id", "user_id"),
        Index("ix_workspace_members_workspace_role", "workspace_id", "role"),
    )


class WorkspaceInvitationModel(Base):
    __tablename__ = "workspace_invitations"

    invitation_id = Column(String(128), primary_key=True, nullable=False)
    workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role = Column(String(32), nullable=False, default="developer")
    invited_by = Column(String(128), nullable=False)
    invited_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(32), nullable=False, default="pending")

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'developer', 'viewer')", name="check_workspace_invitation_role"),
        CheckConstraint("status IN ('pending', 'accepted', 'rejected', 'expired')", name="check_workspace_invitation_status"),
        UniqueConstraint("workspace_id", "email", "invited_at", name="uq_workspace_email_invited"),
        Index("ix_workspace_invitations_status", "status"),
    )


class UserWorkspaceContextModel(Base):
    __tablename__ = "user_workspace_context"

    user_id = Column(String(128), primary_key=True, nullable=False)
    active_workspace_id = Column(String(128), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    last_switched_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    version = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        Index("ix_user_workspace_context_active_ws", "active_workspace_id"),
    )
