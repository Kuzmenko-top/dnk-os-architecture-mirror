# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-TEST-PHASE4-WS"
# purpose: "E2E WebSocket streaming tests for Capacity Analytics (DNK-ANALYTICS-005 Phase 4)"
# canonical_source: true
# alters_files: ["tests/analytics/test_capacity_phase4_ws.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-PHASE4"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import json
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.routers.capacity_analytics_ws import ws_manager

client = TestClient(app)


def test_capacity_websocket_handshake_and_ping():
    """Test connecting to /api/v1/capacity/ws/{workspace_id} and ping-pong interaction."""
    with client.websocket_connect("/api/v1/capacity/ws/ws-test-100") as websocket:
        # 1. Receive initial connection handshake
        data = websocket.receive_text()
        msg = json.loads(data)
        assert msg["event"] == "connected"
        assert msg["workspace_id"] == "ws-test-100"

        # 2. Send ping action
        websocket.send_text(json.dumps({"action": "ping"}))
        pong_data = websocket.receive_text()
        pong = json.loads(pong_data)
        assert pong["event"] == "pong"
        assert pong["workspace_id"] == "ws-test-100"

        # 3. Send subscribe_cluster action
        websocket.send_text(json.dumps({"action": "subscribe_cluster", "cluster_id": "cluster-aws-euc1"}))
        sub_data = websocket.receive_text()
        sub = json.loads(sub_data)
        assert sub["event"] == "subscribed"
        assert sub["cluster_id"] == "cluster-aws-euc1"


@pytest.mark.asyncio
async def test_capacity_websocket_broadcast():
    """Test broadcasting events through the ws_manager to active WebSocket connections."""
    with client.websocket_connect("/api/v1/capacity/ws/ws-test-200") as websocket:
        # Handshake
        init_data = websocket.receive_text()
        assert json.loads(init_data)["event"] == "connected"

        # Trigger broadcast to workspace
        await ws_manager.broadcast_event(
            workspace_id="ws-test-200",
            event_type="anomaly_alert",
            data={"alert_id": "alert_123", "severity": "critical", "message": "Spike in queue depth"}
        )

        bcast_data = websocket.receive_text()
        bcast = json.loads(bcast_data)
        assert bcast["event"] == "anomaly_alert"
        assert bcast["data"]["alert_id"] == "alert_123"
        assert bcast["data"]["severity"] == "critical"
