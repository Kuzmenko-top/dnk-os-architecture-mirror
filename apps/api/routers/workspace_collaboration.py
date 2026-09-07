# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_workspace_collaboration"
# purpose: "FastAPI router for Multi-Workspace Collaboration, Memberships, Invitations, User Workspace Context switching, Presence, and Locks"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException

from apps.api.middleware.tenant_authorization import require_tenant_and_workspace
from apps.api.schemas.workspace_collaboration_schemas import (
    AddMemberRequest,
    UpdateMemberRoleRequest,
    WorkspaceMemberResponse,
    WorkspaceMemberListResponse,
    CreateInvitationRequest,
    WorkspaceInvitationResponse,
    SwitchWorkspaceContextRequest,
    UserWorkspaceContextResponse,
    UserWorkspacesListResponse,
    WorkspacePresenceResponse,
    WorkspaceLocksResponse
)
from apps.api.services.workspace_membership_service import workspace_membership_service
from apps.api.services.workspace_invitation_service import workspace_invitation_service
from apps.api.services.user_workspace_context_service import user_workspace_context_service
from apps.api.services.workspace_collaboration_hub import workspace_collaboration_hub
from apps.api.services.workspace_lock_manager import workspace_lock_manager

router = APIRouter(tags=["Multi-Workspace Collaboration"])


# 1. Members Endpoints
@router.post("/api/v1/workspaces/{workspace_id}/members", response_model=WorkspaceMemberResponse)
async def add_workspace_member(
    workspace_id: str,
    body: AddMemberRequest,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return await workspace_membership_service.add_member(
        workspace_id=workspace_id,
        actor_id=auth_info["user_id"],
        actor_role=auth_info.get("role", "developer"),
        target_user_id=body.user_id,
        role=body.role,
        invited_by=body.invited_by or auth_info["user_id"],
        status=body.status
    )


@router.get("/api/v1/workspaces/{workspace_id}/members", response_model=WorkspaceMemberListResponse)
async def list_workspace_members(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    members = await workspace_membership_service.get_members(workspace_id)
    return {
        "workspace_id": workspace_id,
        "members": members,
        "total": len(members)
    }


@router.delete("/api/v1/workspaces/{workspace_id}/members/{user_id}")
async def remove_workspace_member(
    workspace_id: str,
    user_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return await workspace_membership_service.remove_member(
        workspace_id=workspace_id,
        actor_id=auth_info["user_id"],
        actor_role=auth_info.get("role", "developer"),
        target_user_id=user_id
    )


# 2. Invitations Endpoints
@router.post("/api/v1/workspaces/{workspace_id}/invitations", response_model=WorkspaceInvitationResponse)
async def create_workspace_invitation(
    workspace_id: str,
    body: CreateInvitationRequest,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return await workspace_invitation_service.create_invitation(
        workspace_id=workspace_id,
        actor_id=auth_info["user_id"],
        actor_role=auth_info.get("role", "developer"),
        email=body.email,
        role=body.role,
        expires_in_hours=body.expires_in_hours
    )


@router.post("/api/v1/workspaces/invitations/{invitation_id}/accept")
async def accept_workspace_invitation(
    invitation_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return await workspace_invitation_service.accept_invitation(
        invitation_id=invitation_id,
        user_id=auth_info["user_id"]
    )


@router.post("/api/v1/workspaces/invitations/{invitation_id}/reject")
async def reject_workspace_invitation(
    invitation_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return await workspace_invitation_service.reject_invitation(
        invitation_id=invitation_id,
        user_id=auth_info["user_id"]
    )


# 3. User Workspace Context & List Endpoints
@router.post("/api/v1/users/me/workspace-context", response_model=UserWorkspaceContextResponse)
async def switch_user_workspace_context(
    body: SwitchWorkspaceContextRequest,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    return await user_workspace_context_service.switch_active_workspace(
        user_id=auth_info["user_id"],
        active_workspace_id=body.active_workspace_id,
        expected_version=body.expected_version
    )


@router.get("/api/v1/users/me/workspaces", response_model=UserWorkspacesListResponse)
async def list_user_workspaces(
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    workspaces = await user_workspace_context_service.list_user_workspaces(auth_info["user_id"])
    return {
        "user_id": auth_info["user_id"],
        "workspaces": workspaces,
        "total": len(workspaces)
    }


# 4. Presence & Locks Inspection Endpoints
@router.get("/api/v1/workspaces/{workspace_id}/presence", response_model=WorkspacePresenceResponse)
async def get_workspace_presence(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    active_users = await workspace_collaboration_hub.get_active_users(workspace_id)
    return {
        "workspace_id": workspace_id,
        "active_users": active_users,
        "total": len(active_users)
    }


@router.get("/api/v1/workspaces/{workspace_id}/locks", response_model=WorkspaceLocksResponse)
async def get_workspace_locks(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace)
):
    locks = await workspace_lock_manager.get_locks(workspace_id)
    return {
        "workspace_id": workspace_id,
        "locks": locks,
        "total": len(locks)
    }
