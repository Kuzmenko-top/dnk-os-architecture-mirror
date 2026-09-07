# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_workspace_membership_service"
# purpose: "Business logic service for Workspace Memberships and RBAC role checks, synced with AuthProvider"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from typing import List, Optional, Dict, Any
from fastapi import HTTPException

from apps.api.repositories.workspace_member_repository import WorkspaceMemberRepository
from apps.api.services.auth_provider import auth_provider

VALID_ROLES = {"admin", "developer", "viewer"}


class WorkspaceMembershipService:
    def __init__(self, member_repo: Optional[WorkspaceMemberRepository] = None):
        self.member_repo = member_repo or WorkspaceMemberRepository()

    async def add_member(
        self,
        workspace_id: str,
        actor_id: str,
        actor_role: str,
        target_user_id: str,
        role: str,
        invited_by: Optional[str] = None,
        status: str = "active"
    ) -> Dict[str, Any]:
        if actor_role.lower() != "admin":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Only Workspace Admins can add members"}
            )

        role = role.lower()
        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "INVALID_ROLE", "message": f"Role must be one of {list(VALID_ROLES)}"}
            )

        inviter = invited_by or actor_id
        res = await self.member_repo.add_member(
            workspace_id=workspace_id,
            user_id=target_user_id,
            role=role,
            invited_by=inviter,
            status=status
        )

        # Sync with AuthProvider
        user = auth_provider.get_user(target_user_id)
        if user:
            ws_list = set(user.get("workspaces", []))
            if status.lower() == "active":
                ws_list.add(workspace_id)
            else:
                ws_list.discard(workspace_id)
            auth_provider.update_user(target_user_id, workspaces=list(ws_list))
        else:
            actor_user = auth_provider.get_user(actor_id)
            tenant_id = actor_user.get("tenant_id", "tenant_corp_a") if actor_user else "tenant_corp_a"
            auth_provider.register_user(
                user_id=target_user_id,
                tenant_id=tenant_id,
                workspaces=[workspace_id] if status.lower() == "active" else [],
                roles=[role]
            )

        return res

    async def get_members(self, workspace_id: str) -> List[Dict[str, Any]]:
        return await self.member_repo.get_members(workspace_id)

    async def get_member(self, workspace_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.member_repo.get_member(workspace_id, user_id)

    async def update_member_role(
        self,
        workspace_id: str,
        actor_id: str,
        actor_role: str,
        target_user_id: str,
        new_role: str
    ) -> Dict[str, Any]:
        if actor_role.lower() != "admin":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Only Workspace Admins can update member roles"}
            )

        new_role = new_role.lower()
        if new_role not in VALID_ROLES:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "INVALID_ROLE", "message": f"Role must be one of {list(VALID_ROLES)}"}
            )

        updated = await self.member_repo.update_member_role(workspace_id, target_user_id, new_role)
        if not updated:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "MEMBER_NOT_FOUND", "message": f"User {target_user_id} is not a member of workspace {workspace_id}"}
            )

        # Sync role with AuthProvider
        user = auth_provider.get_user(target_user_id)
        if user:
            auth_provider.update_user(target_user_id, roles=[new_role])

        return updated

    async def remove_member(
        self,
        workspace_id: str,
        actor_id: str,
        actor_role: str,
        target_user_id: str
    ) -> Dict[str, Any]:
        if actor_role.lower() != "admin":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Only Workspace Admins can remove members"}
            )

        removed = await self.member_repo.remove_member(workspace_id, target_user_id)
        if not removed:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "MEMBER_NOT_FOUND", "message": f"User {target_user_id} is not a member of workspace {workspace_id}"}
            )

        # Sync removal with AuthProvider
        user = auth_provider.get_user(target_user_id)
        if user:
            ws_list = set(user.get("workspaces", []))
            ws_list.discard(workspace_id)
            auth_provider.update_user(target_user_id, workspaces=list(ws_list))

        return {"status": "success", "workspace_id": workspace_id, "user_id": target_user_id, "removed": True}


workspace_membership_service = WorkspaceMembershipService()
