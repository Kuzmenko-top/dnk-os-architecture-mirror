# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_workspace_analytics_api"
# purpose: "Comprehensive test suite for Workspace Analytics REST endpoints and Real-time WebSocket live stream"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import pytest
from starlette.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from apps.api.db.analytics_storage import MetricType, analytics_storage
from apps.api.main import app
from apps.api.services.auth_service import auth_service
from apps.api.services.workspace_analytics_service import workspace_analytics_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_storage():
    analytics_storage.clear()
    yield
    analytics_storage.clear()


def test_api_workspace_activity_endpoint():
    token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Record some sample activity
    client.post(
        "/api/workspace/ws_alpha/prompt",
        json={"prompt": "Generate analytics UI"},
        headers=headers,
    )

    response = client.get(
        "/api/v1/analytics/workspaces/ws_alpha/activity?hours=12",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workspace_id"] == "ws_alpha"
    assert "start" in data
    assert "end" in data
    assert isinstance(data["activity"], list)


def test_api_workspace_users_endpoint():
    token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Inject user activity directly via storage
    import asyncio
    asyncio.run(workspace_analytics_service.record_user_activity(
        user_id="usr_admin_001",
        event_type="login",
        workspace_id="ws_alpha"
    ))

    response = client.get(
        "/api/v1/analytics/workspaces/ws_alpha/users",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workspace_id"] == "ws_alpha"
    assert len(data["users"]) == 1
    assert data["users"][0]["data"]["user_id"] == "usr_admin_001"


def test_api_workspace_performance_endpoint():
    token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )
    headers = {"Authorization": f"Bearer {token}"}

    import asyncio
    async def seed_perf():
        for lat in [10.0, 20.0, 30.0, 40.0, 50.0]:
            await workspace_analytics_service.record_performance_metric(
                endpoint="/api/v1/workspaces",
                latency_ms=lat,
                workspace_id="ws_alpha"
            )
    asyncio.run(seed_perf())

    response = client.get(
        "/api/v1/analytics/workspaces/ws_alpha/performance",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workspace_id"] == "ws_alpha"
    perf = data["performance"]
    assert "/api/v1/workspaces" in perf
    endpoint_stats = perf["/api/v1/workspaces"]
    assert endpoint_stats["count"] == 5
    assert endpoint_stats["avg"] == 30.0
    assert endpoint_stats["p50"] == 30.0


def test_api_workspace_errors_endpoint():
    token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )
    headers = {"Authorization": f"Bearer {token}"}

    import asyncio
    asyncio.run(workspace_analytics_service.record_error_metric(
        error_type="VALIDATION_ERROR",
        status_code=422,
        message="Invalid payload",
        workspace_id="ws_alpha"
    ))

    response = client.get(
        "/api/v1/analytics/workspaces/ws_alpha/errors",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["workspace_id"] == "ws_alpha"
    assert len(data["errors"]) == 1
    assert data["errors"][0]["data"]["error_type"] == "VALIDATION_ERROR"
    assert data["errors"][0]["data"]["status_code"] == 422


def test_api_user_me_activity_endpoint():
    token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )
    headers = {"Authorization": f"Bearer {token}"}

    import asyncio
    async def seed_users():
        await workspace_analytics_service.record_user_activity("usr_admin_001", event_type="upload_file", workspace_id="ws_alpha")
        await workspace_analytics_service.record_user_activity("usr_other_002", event_type="delete_file", workspace_id="ws_alpha")
    asyncio.run(seed_users())

    response = client.get(
        "/api/v1/analytics/users/me/activity",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "usr_admin_001"
    assert len(data["activity"]) == 1
    assert data["activity"][0]["data"]["event_type"] == "upload_file"


def test_api_unauthorized_endpoints():
    response = client.get("/api/v1/analytics/workspaces/ws_alpha/activity")
    assert response.status_code == 401

    # Cross-tenant token attempting to access ws_alpha
    token = auth_service.generate_test_token(
        user_id="usr_viewer_002",
        tenant_id="tenant_corp_b",
        workspace_id="ws_alpha"
    )
    response = client.get(
        "/api/v1/analytics/workspaces/ws_alpha/activity",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403


# ==============================================================================
# WebSocket Live Stream Tests
# ==============================================================================

def test_ws_live_metrics_unauthenticated_rejected():
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/api/v1/analytics/workspaces/ws_alpha/live"):
            pass
    assert excinfo.value.code == 4401


def test_ws_live_metrics_non_member_rejected():
    token = auth_service.generate_test_token(
        user_id="usr_viewer_002",
        tenant_id="tenant_corp_b",
        workspace_id="ws_alpha"
    )
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/api/v1/analytics/workspaces/ws_alpha/live?token={token}"):
            pass
    assert excinfo.value.code == 4403


def test_ws_live_metrics_streaming_and_ping():
    token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )

    import asyncio
    asyncio.run(workspace_analytics_service.record_workspace_activity("ws_alpha", "event:init"))
    asyncio.run(workspace_analytics_service.record_performance_metric("/api/v1/test", latency_ms=45.2, workspace_id="ws_alpha"))

    with client.websocket_connect(f"/api/v1/analytics/workspaces/ws_alpha/live?token={token}") as websocket:
        # First message should be immediate metrics update
        msg = websocket.receive_json()
        assert msg["type"] == "metrics_update"
        assert msg["workspace_id"] == "ws_alpha"
        assert "timestamp" in msg
        assert msg["activity_count"] >= 1
        assert "performance" in msg
        assert msg["performance"]["avg_latency"] == 45.2
        assert msg["performance"]["error_count"] == 0

        # Send ping and receive pong
        websocket.send_json({"type": "ping"})
        pong = websocket.receive_json()
        assert pong["type"] == "pong"
        assert "timestamp" in pong
