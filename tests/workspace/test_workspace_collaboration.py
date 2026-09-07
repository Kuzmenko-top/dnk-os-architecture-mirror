# --- DNK-MRH-HEADER ---
# mrh_id: "tests_workspace_test_workspace_collaboration"
# purpose: "Comprehensive unit and integration tests for Multi-Workspace Collaboration, RBAC, Invitations Flow, Context Switching, OCC, and RLS"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.services.auth_service import generate_test_token, auth_service
from apps.api.services.auth_provider import auth_provider
from apps.api.services.workspace_membership_service import WorkspaceMembershipService
from apps.api.services.workspace_invitation_service import WorkspaceInvitationService
from apps.api.services.user_workspace_context_service import UserWorkspaceContextService
from apps.api.repositories.workspace_member_repository import WorkspaceMemberRepository
from apps.api.repositories.workspace_invitation_repository import WorkspaceInvitationRepository
from apps.api.repositories.user_workspace_context_repository import UserWorkspaceContextRepository


@pytest.mark.asyncio
async def test_workspace_membership_crud_and_rbac():
    member_repo = WorkspaceMemberRepository()
    membership_service = WorkspaceMembershipService(member_repo=member_repo)

    # Seed initial admin
    await membership_service.add_member(
        workspace_id="ws_collab_01",
        actor_id="admin_01",
        actor_role="admin",
        target_user_id="admin_01",
        role="admin"
    )

    # 1. Admin adds developer
    member = await membership_service.add_member(
        workspace_id="ws_collab_01",
        actor_id="admin_01",
        actor_role="admin",
        target_user_id="dev_01",
        role="developer"
    )
    assert member["user_id"] == "dev_01"
    assert member["role"] == "developer"
    assert member["status"] == "active"

    # 2. Non-admin attempting to add member raises 403
    with pytest.raises(HTTPException) as exc_info:
        await membership_service.add_member(
            workspace_id="ws_collab_01",
            actor_id="dev_01",
            actor_role="developer",
            target_user_id="dev_02",
            role="viewer"
        )
    assert exc_info.value.status_code == 403

    # 3. List members
    members = await membership_service.get_members("ws_collab_01")
    assert len(members) == 2
    user_ids = {m["user_id"] for m in members}
    assert "admin_01" in user_ids
    assert "dev_01" in user_ids

    # 4. Admin updates member role
    updated = await membership_service.update_member_role(
        workspace_id="ws_collab_01",
        actor_id="admin_01",
        actor_role="admin",
        target_user_id="dev_01",
        new_role="viewer"
    )
    assert updated["role"] == "viewer"

    # 5. Non-admin updating role raises 403
    with pytest.raises(HTTPException) as exc_info:
        await membership_service.update_member_role(
            workspace_id="ws_collab_01",
            actor_id="dev_01",
            actor_role="viewer",
            target_user_id="admin_01",
            new_role="viewer"
        )
    assert exc_info.value.status_code == 403

    # 6. Admin removes member
    res = await membership_service.remove_member(
        workspace_id="ws_collab_01",
        actor_id="admin_01",
        actor_role="admin",
        target_user_id="dev_01"
    )
    assert res["removed"] is True

    members_after = await membership_service.get_members("ws_collab_01")
    assert len(members_after) == 1


@pytest.mark.asyncio
async def test_workspace_invitations_flow():
    inv_repo = WorkspaceInvitationRepository()
    mem_repo = WorkspaceMemberRepository()
    mem_service = WorkspaceMembershipService(member_repo=mem_repo)
    inv_service = WorkspaceInvitationService(invitation_repo=inv_repo, membership_service=mem_service)

    # 1. Admin creates invitation
    inv = await inv_service.create_invitation(
        workspace_id="ws_collab_02",
        actor_id="admin_01",
        actor_role="admin",
        email="newuser@corp.io",
        role="developer"
    )
    inv_id = inv["invitation_id"]
    assert inv["status"] == "pending"
    assert inv["email"] == "newuser@corp.io"

    # 2. Non-admin creating invitation raises 403
    with pytest.raises(HTTPException) as exc_info:
        await inv_service.create_invitation(
            workspace_id="ws_collab_02",
            actor_id="viewer_01",
            actor_role="viewer",
            email="another@corp.io"
        )
    assert exc_info.value.status_code == 403

    # 3. Accept invitation
    accept_res = await inv_service.accept_invitation(
        invitation_id=inv_id,
        user_id="usr_accepted_01"
    )
    assert accept_res["status"] == "accepted"
    assert accept_res["role"] == "developer"

    # Check member was added
    member = await mem_service.get_member("ws_collab_02", "usr_accepted_01")
    assert member is not None
    assert member["role"] == "developer"

    # 4. Trying to accept already accepted invitation raises 400
    with pytest.raises(HTTPException) as exc_info:
        await inv_service.accept_invitation(invitation_id=inv_id, user_id="usr_accepted_01")
    assert exc_info.value.status_code == 400

    # 5. Reject invitation
    inv2 = await inv_service.create_invitation(
        workspace_id="ws_collab_02",
        actor_id="admin_01",
        actor_role="admin",
        email="rejectuser@corp.io"
    )
    reject_res = await inv_service.reject_invitation(
        invitation_id=inv2["invitation_id"],
        user_id="usr_rejected_01"
    )
    assert reject_res["status"] == "rejected"


@pytest.mark.asyncio
async def test_user_workspace_context_switching_and_occ():
    ctx_repo = UserWorkspaceContextRepository()
    mem_repo = WorkspaceMemberRepository()
    context_service = UserWorkspaceContextService(context_repo=ctx_repo, member_repo=mem_repo)

    # Register user in two workspaces
    await mem_repo.add_member("ws_ctx_a", "usr_ctx_01", "developer", "admin_01")
    await mem_repo.add_member("ws_ctx_b", "usr_ctx_01", "developer", "admin_01")

    # 1. Switch to ws_ctx_a
    ctx1 = await context_service.switch_active_workspace(
        user_id="usr_ctx_01",
        active_workspace_id="ws_ctx_a"
    )
    assert ctx1["active_workspace_id"] == "ws_ctx_a"
    assert ctx1["version"] == 1

    # 2. OCC valid update with expected_version = 1
    ctx2 = await context_service.switch_active_workspace(
        user_id="usr_ctx_01",
        active_workspace_id="ws_ctx_b",
        expected_version=1
    )
    assert ctx2["active_workspace_id"] == "ws_ctx_b"
    assert ctx2["version"] == 2

    # 3. OCC stale update with expected_version = 1 (current is 2) raises 409 OCC_CONFLICT
    with pytest.raises(HTTPException) as exc_info:
        await context_service.switch_active_workspace(
            user_id="usr_ctx_01",
            active_workspace_id="ws_ctx_a",
            expected_version=1
        )
    assert exc_info.value.status_code == 409

    # 4. Attempting to switch to an unauthorized workspace raises 403
    with pytest.raises(HTTPException) as exc_info:
        await context_service.switch_active_workspace(
            user_id="usr_ctx_01",
            active_workspace_id="ws_forbidden_999"
        )
    assert exc_info.value.status_code == 403


def test_api_routes_integration():
    client = TestClient(app)

    # Register test user in auth_provider
    auth_provider.register_user(
        user_id="usr_test_api",
        tenant_id="tenant_corp_a",
        workspaces=["ws_alpha"],
        roles=["admin"]
    )

    token = generate_test_token(
        user_id="usr_test_api",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha",
        roles=["admin"]
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": "tenant_corp_a",
        "X-Workspace-Id": "ws_alpha"
    }

    # 1. Add member
    resp = client.post(
        "/api/v1/workspaces/ws_alpha/members",
        headers=headers,
        json={"user_id": "usr_new_member", "role": "developer"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["user_id"] == "usr_new_member"
    assert data["role"] == "developer"

    # 2. List members
    resp = client.get("/api/v1/workspaces/ws_alpha/members", headers=headers)
    assert resp.status_code == 200
    list_data = resp.json()
    assert list_data["total"] >= 1

    # 3. Create invitation
    resp = client.post(
        "/api/v1/workspaces/ws_alpha/invitations",
        headers=headers,
        json={"email": "invitee@corp.io", "role": "developer"}
    )
    assert resp.status_code == 200
    inv_data = resp.json()
    inv_id = inv_data["invitation_id"]

    # 4. Accept invitation
    resp = client.post(f"/api/v1/workspaces/invitations/{inv_id}/accept", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"

    # 5. Switch workspace context
    resp = client.post(
        "/api/v1/users/me/workspace-context",
        headers=headers,
        json={"active_workspace_id": "ws_alpha"}
    )
    assert resp.status_code == 200
    ctx_data = resp.json()
    assert ctx_data["active_workspace_id"] == "ws_alpha"

    # 6. List user workspaces
    resp = client.get("/api/v1/users/me/workspaces", headers=headers)
    assert resp.status_code == 200
    ws_list = resp.json()
    assert ws_list["total"] >= 1

    # 7. Delete member
    resp = client.delete("/api/v1/workspaces/ws_alpha/members/usr_new_member", headers=headers)
    assert resp.status_code == 200
