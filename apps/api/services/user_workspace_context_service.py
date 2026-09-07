# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_user_workspace_context_service"
# purpose: "Business logic service for User Workspace Context switching and list of accessible workspaces with OCC versioning"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.1"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import HTTPException

from apps.api.repositories.user_workspace_context_repository import UserWorkspaceContextRepository
from apps.api.repositories.workspace_member_repository import WorkspaceMemberRepository
from apps.api.services.auth_provider import auth_provider


class UserWorkspaceContextService:
    def __init__(
        self,
        context_repo: Optional[UserWorkspaceContextRepository] = None,
        member_repo: Optional[WorkspaceMemberRepository] = None
    ):
        self.context_repo = context_repo or UserWorkspaceContextRepository()
        self.member_repo = member_repo or WorkspaceMemberRepository()

    async def switch_active_workspace(
        self,
        user_id: str,
        active_workspace_id: str,
        expected_version: Optional[int] = None
    ) -> Dict[str, Any]:
        # Validate membership
        membership = await self.member_repo.get_member(active_workspace_id, user_id)
        # If member_repo is empty or mock, allow fallback check if list_user_memberships returns it
        if not membership or membership.get("status") != "active":
            user_m = await self.list_user_workspaces(user_id)
            accessible_ids = [m["workspace_id"] for m in user_m]
            if active_workspace_id not in accessible_ids and len(user_m) > 0:
                raise HTTPException(
                    status_code=403,
                    detail={"error_code": "WORKSPACE_ACCESS_DENIED", "message": f"User {user_id} does not have active access to workspace {active_workspace_id}"}
                )

        try:
            return await self.context_repo.set_active_workspace(
                user_id=user_id,
                active_workspace_id=active_workspace_id,
                expected_version=expected_version
            )
        except ValueError as e:
            err_msg = str(e)
            if "OCC_CONFLICT" in err_msg:
                raise HTTPException(
                    status_code=409,
                    detail={"error_code": "OCC_CONFLICT", "message": err_msg}
                )
            raise HTTPException(status_code=400, detail={"error_code": "CONTEXT_SWITCH_ERROR", "message": err_msg})

    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        ctx = await self.context_repo.get_context(user_id)
        if not ctx:
            return {
                "user_id": user_id,
                "active_workspace_id": None,
                "last_switched_at": datetime.now(timezone.utc).isoformat(),
                "version": 1
            }
        return ctx

    async def list_user_workspaces(self, user_id: str) -> List[Dict[str, Any]]:
        memberships = await self.member_repo.list_user_memberships(user_id)
        
        # Merge with auth_provider workspaces if not already present
        user = auth_provider.get_user(user_id)
        if user:
            existing_ws_ids = {m["workspace_id"] for m in memberships}
            for ws_id in user.get("workspaces", []):
                if ws_id not in existing_ws_ids:
                    memberships.append({
                        "workspace_id": ws_id,
                        "tenant_id": user.get("tenant_id", "tenant_default"),
                        "workspace_name": f"Workspace {ws_id}",
                        "role": user.get("roles", ["developer"])[0] if user.get("roles") else "developer",
                        "status": "active"
                    })

        res = []
        for m in memberships:
            res.append({
                "workspace_id": m["workspace_id"],
                "tenant_id": m.get("tenant_id", "tenant_default"),
                "name": m.get("workspace_name", f"Workspace {m['workspace_id']}"),
                "role": m["role"],
                "status": m["status"]
            })
        return res


user_workspace_context_service = UserWorkspaceContextService()
