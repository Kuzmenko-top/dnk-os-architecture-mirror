# --- DNK-MRH-HEADER ---
# mrh_id: "tests_workspace_test_workspace_realtime_collaboration"
# purpose: "Comprehensive E2E and integration tests for Real-Time Workspace Collaboration: WebSocket Sync, Presence, Cursors, Pessimistic Locking, and OCC Conflict Resolution"
# author: "DNK-e.com Maksym"
# license: "MIT"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import pytest
import asyncio
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from apps.api.main import app
from apps.api.services.auth_service import auth_service
from apps.api.services.auth_provider import auth_provider
from apps.api.services.workspace_lock_manager import workspace_lock_manager
from apps.api.services.workspace_service import workspace_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_collaboration_state():
    """Reset locks and workspace versions before each test."""
    asyncio.run(workspace_lock_manager.clear())
    auth_provider.register_user("usr_admin_001", "tenant_corp_a", ["ws_alpha", "ws_beta"], ["admin", "developer"])
    auth_provider.register_user("usr_dev_001", "tenant_corp_a", ["ws_alpha", "ws_beta"], ["developer"])
    if "ws_alpha" in workspace_service.WORKSPACES_DB:
        workspace_service.WORKSPACES_DB["ws_alpha"]["metadata"]["version"] = 1


def test_ws_auth_and_presence_lifecycle():
    # Register users in auth provider
    auth_provider.register_user("usr_user_a", "tenant_corp_a", ["ws_alpha"], ["admin"])
    auth_provider.register_user("usr_user_b", "tenant_corp_a", ["ws_alpha"], ["developer"])

    token_a = auth_service.generate_test_token(user_id="usr_user_a", tenant_id="tenant_corp_a", workspace_id="ws_alpha", roles=["admin"])
    token_b = auth_service.generate_test_token(user_id="usr_user_b", tenant_id="tenant_corp_a", workspace_id="ws_alpha", roles=["developer"])

    # 1. User A connects
    with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token_a}") as ws_a:
        # Check initial presence
        ws_a.send_json({"type": "workspace:presence"})
        pres_a = ws_a.receive_json()
        assert pres_a["type"] == "workspace:presence"
        assert len(pres_a["active_users"]) == 1
        assert pres_a["active_users"][0]["user_id"] == "usr_user_a"

        # 2. User B connects
        with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token_b}") as ws_b:
            # User A receives User B's join event broadcast
            join_event_b_on_a = ws_a.receive_json()
            assert join_event_b_on_a["type"] == "presence:join"
            assert join_event_b_on_a["user_id"] == "usr_user_b"
            assert len(join_event_b_on_a["active_users"]) == 2

            # User B requests presence list
            ws_b.send_json({"type": "workspace:presence"})
            pres_b = ws_b.receive_json()
            assert pres_b["type"] == "workspace:presence"
            active_uids = {u["user_id"] for u in pres_b["active_users"]}
            assert "usr_user_a" in active_uids
            assert "usr_user_b" in active_uids

        # 3. User B disconnected, User A receives presence:leave
        leave_event = ws_a.receive_json()
        assert leave_event["type"] == "presence:leave"
        assert leave_event["user_id"] == "usr_user_b"
        assert len(leave_event["active_users"]) == 1


def test_ws_cursor_tracking():
    token_a = auth_service.generate_test_token(user_id="usr_admin_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")
    token_b = auth_service.generate_test_token(user_id="usr_dev_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")

    with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token_a}") as ws_a:
        with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token_b}") as ws_b:
            ws_a.receive_json()  # join B broadcast on A

            # User A moves cursor
            cursor_payload = {"x": 250, "y": 420, "node_id": "node_hero_01"}
            ws_a.send_json({
                "type": "presence:cursor",
                "cursor": cursor_payload
            })

            # User B receives cursor position
            cursor_msg = ws_b.receive_json()
            assert cursor_msg["type"] == "presence:cursor"
            assert cursor_msg["user_id"] == "usr_admin_001"
            assert cursor_msg["cursor"]["x"] == 250
            assert cursor_msg["cursor"]["y"] == 420
            assert cursor_msg["cursor"]["node_id"] == "node_hero_01"


def test_ws_workspace_sync_event():
    token = auth_service.generate_test_token(user_id="usr_admin_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")
    with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token}") as ws:
        # Send sync request
        ws.send_json({"type": "workspace:sync"})
        sync_res = ws.receive_json()
        assert sync_res["type"] == "workspace:sync"
        assert sync_res["workspace_id"] == "ws_alpha"
        assert sync_res["version"] >= 1
        assert "state" in sync_res
        assert "active_users" in sync_res
        assert "active_locks" in sync_res


def test_ws_pessimistic_locking_and_conflicts():
    token_a = auth_service.generate_test_token(user_id="usr_admin_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")
    token_b = auth_service.generate_test_token(user_id="usr_dev_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")

    with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token_a}") as ws_a:
        with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token_b}") as ws_b:
            ws_a.receive_json()  # join B on A

            # 1. User A acquires lock on node_hero_01
            ws_a.send_json({
                "type": "workspace:lock",
                "action": "acquire",
                "section_id": "node_hero_01",
                "ttl_seconds": 30
            })

            # Both ws_a and ws_b receive lock broadcast
            lock_a = ws_a.receive_json()
            assert lock_a["type"] == "workspace:lock"
            assert lock_a["action"] == "acquired"
            assert lock_a["section_id"] == "node_hero_01"
            assert lock_a["user_id"] == "usr_admin_001"

            lock_b = ws_b.receive_json()
            assert lock_b["type"] == "workspace:lock"
            assert lock_b["action"] == "acquired"
            assert lock_b["section_id"] == "node_hero_01"

            # 2. User B attempts to acquire lock on the same section -> receives conflict
            ws_b.send_json({
                "type": "workspace:lock",
                "action": "acquire",
                "section_id": "node_hero_01"
            })
            conflict_res = ws_b.receive_json()
            assert conflict_res["type"] == "workspace:conflict"
            assert conflict_res["error_code"] == "SECTION_ALREADY_LOCKED"
            assert conflict_res["conflict"]["locked_by"] == "usr_admin_001"

            # 3. User B attempts mutation on locked section -> receives conflict
            ws_b.send_json({
                "type": "workspace:mutation",
                "mutation": {
                    "section_id": "node_hero_01",
                    "action": "update_text",
                    "content": "Unauthorized changes"
                }
            })
            mutation_conflict = ws_b.receive_json()
            assert mutation_conflict["type"] == "workspace:conflict"
            assert mutation_conflict["error_code"] == "SECTION_LOCKED_BY_ANOTHER_USER"

            # 4. User A releases the lock
            ws_a.send_json({
                "type": "workspace:lock",
                "action": "release",
                "section_id": "node_hero_01"
            })

            release_a = ws_a.receive_json()
            assert release_a["type"] == "workspace:lock"
            assert release_a["action"] == "released"

            release_b = ws_b.receive_json()
            assert release_b["type"] == "workspace:lock"
            assert release_b["action"] == "released"

            # 5. User B can now acquire the lock
            ws_b.send_json({
                "type": "workspace:lock",
                "action": "acquire",
                "section_id": "node_hero_01"
            })
            acquired_by_b = ws_b.receive_json()
            assert acquired_by_b["type"] == "workspace:lock"
            assert acquired_by_b["action"] == "acquired"
            assert acquired_by_b["user_id"] == "usr_dev_001"


def test_ws_optimistic_occ_mutation_and_conflicts():
    token_a = auth_service.generate_test_token(user_id="usr_admin_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")
    token_b = auth_service.generate_test_token(user_id="usr_dev_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")

    with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token_a}") as ws_a:
        with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token_b}") as ws_b:
            ws_a.receive_json()  # join B on A

            # 1. User A applies mutation with expected_version = 1
            ws_a.send_json({
                "type": "workspace:mutation",
                "expected_version": 1,
                "mutation": {
                    "node_id": "node_product_grid_01",
                    "action": "reorder_items",
                    "items": ["p1", "p2", "p3"]
                }
            })

            # Both receive mutation broadcast with new version = 2
            mut_a = ws_a.receive_json()
            assert mut_a["type"] == "workspace:mutation"
            assert mut_a["version"] == 2
            assert mut_a["actor_id"] == "usr_admin_001"

            mut_b = ws_b.receive_json()
            assert mut_b["type"] == "workspace:mutation"
            assert mut_b["version"] == 2

            # 2. User B submits stale mutation with expected_version = 1 (current is 2)
            ws_b.send_json({
                "type": "workspace:mutation",
                "expected_version": 1,
                "mutation": {
                    "node_id": "node_product_grid_01",
                    "action": "change_columns",
                    "columns": 4
                }
            })

            # User B receives OCC collision conflict
            occ_conflict = ws_b.receive_json()
            assert occ_conflict["type"] == "workspace:conflict"
            assert occ_conflict["error_code"] == "OCC_VERSION_MISMATCH"
            assert occ_conflict["expected_version"] == 1
            assert occ_conflict["current_version"] == 2

            # 3. User B adapts to version 2 and re-submits with expected_version = 2
            ws_b.send_json({
                "type": "workspace:mutation",
                "expected_version": 2,
                "mutation": {
                    "node_id": "node_product_grid_01",
                    "action": "change_columns",
                    "columns": 4
                }
            })

            mut2_a = ws_a.receive_json()
            mut2_b = ws_b.receive_json()
            assert mut2_b["type"] == "workspace:mutation"
            assert mut2_b["version"] == 3
            assert mut2_b["actor_id"] == "usr_dev_001"


def test_ws_disconnect_auto_releases_held_locks():
    token_a = auth_service.generate_test_token(user_id="usr_admin_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")
    token_b = auth_service.generate_test_token(user_id="usr_dev_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")

    with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token_b}") as ws_b:
        with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token_a}") as ws_a:
            ws_b.receive_json()  # join A on B

            # User A acquires lock on node_header_01
            ws_a.send_json({
                "type": "workspace:lock",
                "action": "acquire",
                "section_id": "node_header_01"
            })
            ws_a.receive_json()  # lock ack on A
            ws_b.receive_json()  # lock ack on B

        # User A disconnects by exiting context manager
        # User B receives presence leave with auto-released locks
        leave_msg = ws_b.receive_json()
        assert leave_msg["type"] == "presence:leave"
        assert leave_msg["user_id"] == "usr_admin_001"
        assert "node_header_01" in leave_msg.get("released_locks", [])

        # Verify locks in lock manager are indeed freed
        locks_after = asyncio.run(workspace_lock_manager.get_locks("ws_alpha"))
        assert len(locks_after) == 0


def test_rest_presence_and_locks_endpoints():
    token = auth_service.generate_test_token(user_id="usr_admin_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha", roles=["admin"])
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": "tenant_corp_a",
        "X-Workspace-Id": "ws_alpha"
    }

    # 1. Check REST presence
    resp = client.get("/api/v1/workspaces/ws_alpha/presence", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "active_users" in data
    assert "total" in data

    # 2. Check REST locks
    resp = client.get("/api/v1/workspaces/ws_alpha/locks", headers=headers)
    assert resp.status_code == 200
    lock_data = resp.json()
    assert "locks" in lock_data
    assert "total" in lock_data
