# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_workspace_analytics_integration"
# purpose: "Integration test suite for full analytics pipeline, REST API endpoints and WebSocket live stream"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import pytest
from datetime import datetime, timedelta, timezone
from apps.api.db.analytics_storage import analytics_storage
from apps.api.services.workspace_analytics_service import workspace_analytics_service, MetricType


@pytest.fixture(autouse=True)
def clean_storage():
    analytics_storage.clear()
    yield
    analytics_storage.clear()


@pytest.mark.asyncio
async def test_full_analytics_pipeline():
    """Test full analytics pipeline: record → query → aggregate"""
    workspace_id = "ws_alpha"
    user_id = "user_001"
    
    # Record workspace activity
    await workspace_analytics_service.record_workspace_activity(
        workspace_id,
        "prompt_submitted",
        {"prompt_id": "prm_001"}
    )
    
    # Record user activity
    await workspace_analytics_service.record_user_activity(
        user_id,
        "login",
        workspace_id
    )
    
    # Record performance metric
    await workspace_analytics_service.record_performance_metric(
        "/api/v1/workspaces/ws_alpha/prompts",
        latency_ms=150.5,
        db_latency_ms=50.2,
        redis_latency_ms=10.1
    )
    
    # Record error metric
    await workspace_analytics_service.record_error_metric(
        "OCC_VERSION_MISMATCH",
        409,
        workspace_id
    )
    
    # Query activity
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=1)
    activity = await workspace_analytics_service.get_workspace_activity(
        workspace_id,
        start,
        end
    )
    assert len(activity) > 0
    assert any(a["data"]["event_type"] == "prompt_submitted" for a in activity)
    
    # Query performance percentiles
    percentiles = await workspace_analytics_service.get_performance_percentiles(
        "/api/v1/workspaces/ws_alpha/prompts",
        start,
        end
    )
    assert "p50" in percentiles
    assert "p95" in percentiles
    assert "p99" in percentiles
    assert percentiles["p50"] > 0


@pytest.mark.asyncio
async def test_analytics_api_endpoints():
    """Test analytics API endpoints"""
    from starlette.testclient import TestClient
    from apps.api.main import app
    from apps.api.services.auth_service import auth_service
    
    client = TestClient(app)
    
    # Generate test token
    token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test activity endpoint
    resp = client.get(
        "/api/v1/analytics/workspaces/ws_alpha/activity?hours=24",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "activity" in data
    assert "start" in data
    assert "end" in data
    
    # Test performance endpoint
    resp = client.get(
        "/api/v1/analytics/workspaces/ws_alpha/performance?hours=24",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "performance" in data
    
    # Test errors endpoint
    resp = client.get(
        "/api/v1/analytics/workspaces/ws_alpha/errors?hours=24",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "errors" in data
    
    # Test users endpoint
    resp = client.get(
        "/api/v1/analytics/workspaces/ws_alpha/users?hours=24",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    
    # Test user me endpoint
    resp = client.get(
        "/api/v1/analytics/users/me/activity?hours=24",
        headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "activity" in data


@pytest.mark.asyncio
async def test_analytics_websocket_live_stream():
    """Test WebSocket live metrics streaming"""
    from starlette.testclient import TestClient
    from apps.api.main import app
    from apps.api.services.auth_service import auth_service
    
    client = TestClient(app)
    
    # Generate test token
    token = auth_service.generate_test_token(
        user_id="usr_admin_001",
        tenant_id="tenant_corp_a",
        workspace_id="ws_alpha"
    )
    
    # Connect to WebSocket
    with client.websocket_connect(
        f"/api/v1/analytics/workspaces/ws_alpha/live?token={token}"
    ) as websocket:
        # Receive metrics update
        data = websocket.receive_json()
        assert data["type"] == "metrics_update"
        assert "workspace_id" in data
        assert "timestamp" in data
        assert "activity_count" in data
        assert "performance" in data
