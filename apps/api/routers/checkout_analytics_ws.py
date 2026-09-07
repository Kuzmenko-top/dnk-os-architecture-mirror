# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_checkout_analytics_ws"
# purpose: "WebSocket Manager for Real-Time Checkout Conversion & AOV Streaming (DNK-ECOM-006 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
from typing import Dict, List, Set, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

ws_router = APIRouter(tags=["Checkout Real-Time Analytics WebSocket"])
router = ws_router


class CheckoutAnalyticsWSManager:
    """
    Manages real-time WebSocket connections and streams conversion events / AOV updates.
    """

    def __init__(self):
        self._active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, shop_domain: str, websocket: WebSocket):
        await websocket.accept()
        if shop_domain not in self._active_connections:
            self._active_connections[shop_domain] = set()
        self._active_connections[shop_domain].add(websocket)

    def disconnect(self, shop_domain: str, websocket: WebSocket):
        if shop_domain in self._active_connections:
            self._active_connections[shop_domain].discard(websocket)
            if not self._active_connections[shop_domain]:
                del self._active_connections[shop_domain]

    async def broadcast_event(self, shop_domain: str, event_data: Dict[str, Any]):
        """
        Broadcast live conversion event or metrics update to all connected dashboard clients.
        """
        connections = self._active_connections.get(shop_domain, set())
        stale_conns = []
        for ws in list(connections):
            try:
                await ws.send_json(event_data)
            except Exception:
                stale_conns.append(ws)

        for ws in stale_conns:
            self.disconnect(shop_domain, ws)


checkout_ws_manager = CheckoutAnalyticsWSManager()


@ws_router.websocket("/api/v1/ecom/analytics/ws/{shop_domain}")
async def checkout_analytics_websocket_endpoint(websocket: WebSocket, shop_domain: str):
    await checkout_ws_manager.connect(shop_domain, websocket)
    try:
        await websocket.send_json({
            "type": "CONNECTION_ESTABLISHED",
            "shop_domain": shop_domain,
            "status": "connected",
        })
        while True:
            data = await websocket.receive_json()
            # Echo or process client ping/command
            if data.get("action") == "ping":
                await websocket.send_json({"type": "PONG", "status": "active"})
            elif data.get("action") == "subscribe_live_events":
                await websocket.send_json({
                    "type": "SUBSCRIPTION_CONFIRMED",
                    "channel": "conversion_stream",
                    "shop_domain": shop_domain,
                })
    except WebSocketDisconnect:
        checkout_ws_manager.disconnect(shop_domain, websocket)
    except Exception:
        checkout_ws_manager.disconnect(shop_domain, websocket)
