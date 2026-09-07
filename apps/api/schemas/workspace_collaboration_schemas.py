# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_schemas_workspace_collaboration_schemas"
# purpose: "Pydantic schemas for Workspace Members, Invitations, RBAC, Context switching, Presence, and Locks with OCC"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WorkspaceMemberResponse(BaseModel):
    workspace_id: str
    user_id: str
    role: str
    invited_by: str
    invited_at: str
    status: str


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = Field(default="developer", description="Role: admin, developer, viewer")
    invited_by: Optional[str] = None
    status: str = Field(default="active", description="Status: active, inactive, suspended")


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(..., description="Role: admin, developer, viewer")


class WorkspaceMemberListResponse(BaseModel):
    workspace_id: str
    members: List[WorkspaceMemberResponse]
    total: int


class CreateInvitationRequest(BaseModel):
    email: str
    role: str = Field(default="developer", description="Role: admin, developer, viewer")
    expires_in_hours: int = Field(default=168, description="Expiration in hours (default 7 days)")


class WorkspaceInvitationResponse(BaseModel):
    invitation_id: str
    workspace_id: str
    email: str
    role: str
    invited_by: str
    invited_at: str
    expires_at: str
    status: str


class SwitchWorkspaceContextRequest(BaseModel):
    active_workspace_id: str
    expected_version: Optional[int] = Field(default=None, description="Expected version for OCC concurrency check")


class UserWorkspaceContextResponse(BaseModel):
    user_id: str
    active_workspace_id: Optional[str] = None
    last_switched_at: str
    version: int


class UserWorkspaceItem(BaseModel):
    workspace_id: str
    tenant_id: str
    name: str
    role: str
    status: str


class UserWorkspacesListResponse(BaseModel):
    user_id: str
    workspaces: List[UserWorkspaceItem]
    total: int


class WorkspaceActiveUser(BaseModel):
    user_id: str
    role: str
    joined_at: float
    cursor: Optional[Dict[str, Any]] = None
    connections_count: int = 1


class WorkspacePresenceResponse(BaseModel):
    workspace_id: str
    active_users: List[WorkspaceActiveUser]
    total: int


class WorkspaceLockItem(BaseModel):
    workspace_id: str
    section_id: str
    user_id: str
    locked_at: float
    expires_at: float
    ttl_seconds: int
    renewed: Optional[bool] = None


class WorkspaceLocksResponse(BaseModel):
    workspace_id: str
    locks: List[WorkspaceLockItem]
    total: int
