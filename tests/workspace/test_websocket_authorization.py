# --- DNK-MRH-HEADER ---
# mrh_id: "tests_workspace_test_websocket_authorization"
# purpose: "Automated test suite verifying WebSocket authentication, workspace topic authorization, and security disconnects"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-23"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from apps.api.main import app
from apps.api.services.auth_service import auth_service

client = TestClient(app)


def test_ws_unauthenticated_connection_rejected():
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws/workspaces/ws_alpha"):
            pass
    assert excinfo.value.code == 4401


def test_ws_non_member_workspace_rejected():
    # User belonging to tenant_corp_b attempting to access ws_alpha (tenant_corp_a)
    token = auth_service.generate_test_token(user_id="usr_viewer_002", tenant_id="tenant_corp_b", workspace_id="ws_alpha")
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token}"):
            pass
    assert excinfo.value.code == 4403


def test_ws_authorized_subscription_accepted():
    token = auth_service.generate_test_token(user_id="usr_admin_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")
    with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token}") as websocket:
        websocket.send_json({"type": "subscribe", "topic": "workspace:ws_alpha"})
        response = websocket.receive_json()
        assert response["type"] == "subscribed"
        assert response["topic"] == "workspace:ws_alpha"


def test_ws_unauthorized_topic_subscription_denied():
    token = auth_service.generate_test_token(user_id="usr_admin_001", tenant_id="tenant_corp_a", workspace_id="ws_alpha")
    with client.websocket_connect(f"/ws/workspaces/ws_alpha?token={token}") as websocket:
        websocket.send_json({"type": "subscribe", "topic": "workspace:ws_forbidden"})
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert response["error_code"] == "UNAUTHORIZED_TOPIC"
