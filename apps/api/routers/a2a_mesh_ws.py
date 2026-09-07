# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-A2A-003-ROUTER-MESH-WS"
# purpose: "FastAPI WebSocket Telemetry and Event Router for A2A Mesh Swarm"
# canonical_source: true
# alters_files: ["apps/api/routers/a2a_mesh_ws.py"]
# triggers_tasks: ["DNK-A2A-003-MVP"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from apps.api.routers.a2a_mesh_router import get_mesh_services

router = APIRouter(tags=["A2A Mesh Telemetry WebSocket"])


class A2AMeshConnectionManager:
    """Manages WebSocket connections and broadcasts real-time mesh telemetry."""

    def __init__(self):
        self._active_connections: Set[WebSocket] = set()
        self._event_subscribers: Set[WebSocket] = set()

    async def connect_telemetry(self, websocket: WebSocket):
        await websocket.accept()
        self._active_connections.add(websocket)

    async def connect_events(self, websocket: WebSocket):
        await websocket.accept()
        self._event_subscribers.add(websocket)

    def disconnect_telemetry(self, websocket: WebSocket):
        self._active_connections.discard(websocket)

    def disconnect_events(self, websocket: WebSocket):
        self._event_subscribers.discard(websocket)

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]):
        """Broadcast an event to all subscribed WebSocket clients."""
        payload = {
            "type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data,
        }
        dead_conns = []
        for ws in self._event_subscribers:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_conns.append(ws)

        for ws in dead_conns:
            self._event_subscribers.discard(ws)

    async def broadcast_telemetry(self, payload: Dict[str, Any]):
        """Broadcast telemetry packet to all connected clients."""
        dead_conns = []
        for ws in self._active_connections:
            try:
                await ws.send_json(payload)
            except Exception:
                dead_conns.append(ws)

        for ws in dead_conns:
            self._active_connections.discard(ws)


ws_manager = A2AMeshConnectionManager()


async def _telemetry_handler(websocket: WebSocket):
    await ws_manager.connect_telemetry(websocket)
    services = get_mesh_services()
    load_rebalancer = services["load_rebalancer"]
    negotiator = services["negotiator"]
    auction_engine = services["auction_engine"]

    try:
        while True:
            health = load_rebalancer.evaluate_mesh_health()
            agents = negotiator.list_agents()
            auctions = auction_engine._auctions.values()

            telemetry_packet = {
                "type": "mesh_telemetry",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "mesh_health": health,
                "agents_count": len(agents),
                "active_auctions_count": len([a for a in auctions if getattr(a, "status", "") == "open"]),
                "nodes": [
                    {
                        "agent_id": getattr(a, "id", str(getattr(a, "agent_id", ""))),
                        "agent_name": getattr(a, "agent_name", ""),
                        "role": getattr(a, "role", "worker"),
                        "cpu_utilization": getattr(a, "cpu_utilization", 0.0),
                        "memory_utilization": getattr(a, "memory_utilization", 0.0),
                        "reputation_score": getattr(a, "reputation_score", 1.0),
                        "status": getattr(a, "status", "online"),
                    }
                    for a in agents
                ],
            }

            await websocket.send_json(telemetry_packet)
            await asyncio.sleep(1.0)
    except (WebSocketDisconnect, Exception):
        ws_manager.disconnect_telemetry(websocket)


async def _events_handler(websocket: WebSocket):
    await ws_manager.connect_events(websocket)
    try:
        await websocket.send_json({
            "type": "connection_established",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Subscribed to A2A Mesh Event Bus",
        })

        while True:
            data = await websocket.receive_text()
            try:
                parsed = json.loads(data)
                if parsed.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now(timezone.utc).isoformat()})
            except Exception:
                pass
    except (WebSocketDisconnect, Exception):
        ws_manager.disconnect_events(websocket)


@router.websocket("/a2a/mesh/ws/telemetry")
@router.websocket("/ws/telemetry")
async def websocket_mesh_telemetry(websocket: WebSocket):
    await _telemetry_handler(websocket)


@router.websocket("/a2a/mesh/ws/events")
@router.websocket("/ws/events")
async def websocket_mesh_events(websocket: WebSocket):
    await _events_handler(websocket)
