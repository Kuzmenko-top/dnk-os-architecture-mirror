# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_workspace_invitation_service"
# purpose: "Business logic service for Workspace Invitations lifecycle (create, accept, reject, expire)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from fastapi import HTTPException

from apps.api.repositories.workspace_invitation_repository import WorkspaceInvitationRepository
from apps.api.services.workspace_membership_service import WorkspaceMembershipService, workspace_membership_service

VALID_ROLES = {"admin", "developer", "viewer"}


class WorkspaceInvitationService:
    def __init__(
        self,
        invitation_repo: Optional[WorkspaceInvitationRepository] = None,
        membership_service: Optional[WorkspaceMembershipService] = None
    ):
        self.invitation_repo = invitation_repo or WorkspaceInvitationRepository()
        self.membership_service = membership_service or workspace_membership_service

    async def create_invitation(
        self,
        workspace_id: str,
        actor_id: str,
        actor_role: str,
        email: str,
        role: str = "developer",
        expires_in_hours: int = 168
    ) -> Dict[str, Any]:
        if actor_role.lower() != "admin":
            raise HTTPException(
                status_code=403,
                detail={"error_code": "INSUFFICIENT_PERMISSIONS", "message": "Only Workspace Admins can create invitations"}
            )

        role = role.lower()
        if role not in VALID_ROLES:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "INVALID_ROLE", "message": f"Role must be one of {list(VALID_ROLES)}"}
            )

        invitation_id = f"inv_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=expires_in_hours)

        return await self.invitation_repo.create_invitation(
            invitation_id=invitation_id,
            workspace_id=workspace_id,
            email=email,
            role=role,
            invited_by=actor_id,
            expires_at=expires_at
        )

    async def accept_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        inv = await self.invitation_repo.get_invitation(invitation_id)
        if not inv:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "INVITATION_NOT_FOUND", "message": f"Invitation {invitation_id} not found"}
            )

        if inv["status"].lower() != "pending":
            raise HTTPException(
                status_code=400,
                detail={"error_code": "INVITATION_NOT_PENDING", "message": f"Invitation status is already {inv['status']}"}
            )

        now = datetime.now(timezone.utc)
        exp_str = inv["expires_at"]
        if isinstance(exp_str, str):
            expires_at = datetime.fromisoformat(exp_str.replace("Z", "+00:00"))
        else:
            expires_at = exp_str

        if expires_at < now:
            await self.invitation_repo.update_invitation_status(invitation_id, "expired")
            raise HTTPException(
                status_code=400,
                detail={"error_code": "INVITATION_EXPIRED", "message": "Invitation has expired"}
            )

        # Add member to workspace
        await self.membership_service.add_member(
            workspace_id=inv["workspace_id"],
            actor_id=inv["invited_by"],
            actor_role="admin",
            target_user_id=user_id,
            role=inv["role"],
            invited_by=inv["invited_by"],
            status="active"
        )

        # Update invitation status
        updated_inv = await self.invitation_repo.update_invitation_status(invitation_id, "accepted")
        return {
            "status": "accepted",
            "workspace_id": inv["workspace_id"],
            "user_id": user_id,
            "role": inv["role"],
            "invitation": updated_inv
        }

    async def reject_invitation(
        self,
        invitation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        inv = await self.invitation_repo.get_invitation(invitation_id)
        if not inv:
            raise HTTPException(
                status_code=404,
                detail={"error_code": "INVITATION_NOT_FOUND", "message": f"Invitation {invitation_id} not found"}
            )

        if inv["status"].lower() != "pending":
            raise HTTPException(
                status_code=400,
                detail={"error_code": "INVITATION_NOT_PENDING", "message": f"Invitation status is already {inv['status']}"}
            )

        updated_inv = await self.invitation_repo.update_invitation_status(invitation_id, "rejected")
        return {
            "status": "rejected",
            "workspace_id": inv["workspace_id"],
            "user_id": user_id,
            "invitation": updated_inv
        }

    async def list_invitations(self, workspace_id: str) -> List[Dict[str, Any]]:
        return await self.invitation_repo.list_invitations(workspace_id)


workspace_invitation_service = WorkspaceInvitationService()
