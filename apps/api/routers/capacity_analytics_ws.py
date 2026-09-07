# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ANALYTICS-005-ROUTER-CAPACITY-WS"
# purpose: "FastAPI WebSocket Router for Real-time Capacity Telemetry & Anomaly Live Streaming"
# canonical_source: true
# alters_files: ["apps/api/routers/capacity_analytics_ws.py"]
# triggers_tasks: ["DNK-ANALYTICS-005-PHASE4"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import json
import logging
from typing import Dict, List, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/capacity/ws", tags=["Capacity WebSocket Stream"])


class CapacityWebSocketManager:
    """Manages active WebSocket connections for capacity telemetry and real-time anomaly alerts."""

    def __init__(self):
        # Connections mapped by workspace_id: {workspace_id: [WebSocket, ...]}
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, workspace_id: str):
        """Accept connection and register under workspace_id."""
        await websocket.accept()
        if workspace_id not in self.active_connections:
            self.active_connections[workspace_id] = []
        self.active_connections[workspace_id].append(websocket)
        logger.info(f"WebSocket client connected to capacity stream for workspace '{workspace_id}'")

    def disconnect(self, websocket: WebSocket, workspace_id: str):
        """Unregister a disconnected WebSocket client."""
        if workspace_id in self.active_connections:
            if websocket in self.active_connections[workspace_id]:
                self.active_connections[workspace_id].remove(websocket)
            if not self.active_connections[workspace_id]:
                del self.active_connections[workspace_id]
        logger.info(f"WebSocket client disconnected from capacity stream for workspace '{workspace_id}'")

    async def broadcast_event(self, workspace_id: str, event_type: str, data: Dict[str, Any]):
        """Broadcast a structured JSON payload to all clients connected to a specific workspace."""
        payload = json.dumps({"event": event_type, "data": data})
        if workspace_id in self.active_connections:
            stale_connections = []
            for ws in list(self.active_connections[workspace_id]):
                try:
                    await ws.send_text(payload)
                except Exception as e:
                    logger.warning(f"Error broadcasting to WS client: {e}")
                    stale_connections.append(ws)

            for stale in stale_connections:
                self.disconnect(stale, workspace_id)

    async def broadcast_global(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event payload to all connected clients across all workspaces."""
        payload = json.dumps({"event": event_type, "data": data})
        for ws_id, connections in list(self.active_connections.items()):
            stale_connections = []
            for ws in list(connections):
                try:
                    await ws.send_text(payload)
                except Exception as e:
                    logger.warning(f"Error in global WS broadcast: {e}")
                    stale_connections.append(ws)

            for stale in stale_connections:
                self.disconnect(stale, ws_id)


ws_manager = CapacityWebSocketManager()


@router.websocket("/{workspace_id}")
async def capacity_websocket_endpoint(websocket: WebSocket, workspace_id: str):
    """Real-time capacity telemetry, anomaly alert and scaling WebSocket stream."""
    await ws_manager.connect(websocket, workspace_id)
    try:
        # Send initial connection handshake confirmation
        handshake_payload = json.dumps({
            "event": "connected",
            "message": f"Connected to Capacity Analytics Live Stream for workspace {workspace_id}",
            "workspace_id": workspace_id,
        })
        await websocket.send_text(handshake_payload)

        while True:
            # Listen for client ping / subscriptions
            raw_data = await websocket.receive_text()
            try:
                msg = json.loads(raw_data)
                action = msg.get("action")
                if action == "ping":
                    await websocket.send_text(json.dumps({"event": "pong", "workspace_id": workspace_id}))
                elif action == "subscribe_cluster":
                    cluster_id = msg.get("cluster_id", "default")
                    await websocket.send_text(json.dumps({
                        "event": "subscribed",
                        "cluster_id": cluster_id,
                        "status": "active"
                    }))
            except Exception:
                await websocket.send_text(json.dumps({"event": "ack", "received": raw_data}))

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, workspace_id)
    except Exception as e:
        logger.error(f"WebSocket error in capacity stream: {e}")
        ws_manager.disconnect(websocket, workspace_id)
