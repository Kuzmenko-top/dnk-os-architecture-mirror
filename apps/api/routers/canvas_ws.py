# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_canvas_ws"
# purpose: "FastAPI WebSocket router for Visual Canvas V2 real-time multi-user synchronization (cursors, OCC patches, locks, selection)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from apps.api.services.canvas_occ_sync import (
    CanvasOCCSyncManager,
    CanvasPatchOp,
    PatchOpType
)
from apps.api.routers.canvas_router import _get_occ

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ws/canvas", tags=["Canvas Real-Time WS"])


class CanvasWebSocketManager:
    """Manages active WebSocket connections, cursors, and event broadcasting per canvas session."""

    def __init__(self):
        # canvas_id -> list of (websocket, client_id, user_name, color)
        self.active_sessions: Dict[str, List[Dict[str, Any]]] = {}
        # canvas_id -> {client_id: {x, y, timestamp, user_name, color}}
        self.cursor_states: Dict[str, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, canvas_id: str, client_id: str, user_name: str = "Anonymous", color: str = "#3b82f6"):
        await websocket.accept()
        if canvas_id not in self.active_sessions:
            self.active_sessions[canvas_id] = []
            self.cursor_states[canvas_id] = {}

        client_info = {
            "ws": websocket,
            "client_id": client_id,
            "user_name": user_name,
            "color": color,
            "joined_at": time.time()
        }
        self.active_sessions[canvas_id].append(client_info)
        logger.info(f"Client {client_id} ({user_name}) connected to canvas {canvas_id}")

        # Broadcast user_joined event to peers
        await self.broadcast(
            canvas_id,
            {
                "event": "user_joined",
                "client_id": client_id,
                "user_name": user_name,
                "color": color,
                "active_collaborators_count": len(self.active_sessions[canvas_id])
            },
            exclude_client_id=client_id
        )

    def disconnect(self, websocket: WebSocket, canvas_id: str) -> Optional[str]:
        disconnected_client_id = None
        if canvas_id in self.active_sessions:
            remaining = []
            for item in self.active_sessions[canvas_id]:
                if item["ws"] == websocket:
                    disconnected_client_id = item["client_id"]
                else:
                    remaining.append(item)
            self.active_sessions[canvas_id] = remaining

            if disconnected_client_id and disconnected_client_id in self.cursor_states.get(canvas_id, {}):
                del self.cursor_states[canvas_id][disconnected_client_id]

            if not self.active_sessions[canvas_id]:
                del self.active_sessions[canvas_id]
                self.cursor_states.pop(canvas_id, None)

        # Release any OCC locks held by this client
        if disconnected_client_id:
            occ = _get_occ(canvas_id)
            occ.release_all_client_locks(disconnected_client_id)
            logger.info(f"Client {disconnected_client_id} disconnected from canvas {canvas_id}")

        return disconnected_client_id

    async def broadcast(self, canvas_id: str, payload: Dict[str, Any], exclude_client_id: Optional[str] = None):
        if canvas_id not in self.active_sessions:
            return

        raw_payload = json.dumps(payload)
        stale = []
        for item in self.active_sessions[canvas_id]:
            if exclude_client_id and item["client_id"] == exclude_client_id:
                continue
            try:
                await item["ws"].send_text(raw_payload)
            except Exception as e:
                logger.warning(f"Failed to send to client {item['client_id']}: {e}")
                stale.append(item["ws"])

        for ws in stale:
            self.disconnect(ws, canvas_id)


    async def broadcast_node_state(self, canvas_id: str, node_id: str, state: str, meta: Optional[Dict[str, Any]] = None):
        """Broadcasts real-time node state transitions (Active, Processing, Done, Failed) to live canvas clients."""
        await self.broadcast(
            canvas_id,
            {
                "event": "node_state_pulse",
                "node_id": node_id,
                "state": state,
                "meta": meta or {},
                "timestamp": time.time()
            }
        )


canvas_ws_manager = CanvasWebSocketManager()


@router.websocket("/{canvas_id}")
async def canvas_realtime_sync_ws(
    websocket: WebSocket,
    canvas_id: str,
    client_id: Optional[str] = None,
    user_name: Optional[str] = "Collaborator",
    color: Optional[str] = "#3b82f6"
):
    actual_client_id = client_id or f"client_{int(time.time()*1000)}"
    await canvas_ws_manager.connect(websocket, canvas_id, actual_client_id, user_name=user_name or "Collaborator", color=color or "#3b82f6")

    occ = _get_occ(canvas_id)

    # Send initial connection handshake & full OCC snapshot
    snapshot = occ.get_snapshot()
    await websocket.send_text(json.dumps({
        "event": "handshake_ack",
        "canvas_id": canvas_id,
        "client_id": actual_client_id,
        "current_version": occ.current_version,
        "snapshot": snapshot,
        "active_cursors": canvas_ws_manager.cursor_states.get(canvas_id, {})
    }))

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                msg = json.loads(raw_text)
            except Exception:
                await websocket.send_text(json.dumps({"event": "error", "message": "Invalid JSON format"}))
                continue

            action = msg.get("action") or msg.get("type")

            if action == "ping":
                await websocket.send_text(json.dumps({"event": "pong", "timestamp": time.time()}))

            elif action in ("TASK_EXECUTE", "task_execute"):
                try:
                    from apps.api.routers.swarm_ws import handle_task_execution
                    asyncio.create_task(handle_task_execution(websocket, msg))
                except Exception as e:
                    logger.error(f"Error handling TASK_EXECUTE in canvas_ws: {e}")

            elif action == "cursor_move":
                x = float(msg.get("x", 0.0))
                y = float(msg.get("y", 0.0))
                cursor_data = {
                    "client_id": actual_client_id,
                    "user_name": user_name,
                    "color": color,
                    "x": x,
                    "y": y,
                    "timestamp": time.time()
                }
                canvas_ws_manager.cursor_states.setdefault(canvas_id, {})[actual_client_id] = cursor_data
                await canvas_ws_manager.broadcast(
                    canvas_id,
                    {"event": "cursor_updated", "cursor": cursor_data},
                    exclude_client_id=actual_client_id
                )

            elif action == "acquire_lock":
                node_id = msg.get("node_id")
                timeout_sec = float(msg.get("timeout_seconds", 30.0))
                success, err = occ.acquire_lock(node_id, actual_client_id, timeout_seconds=timeout_sec)
                await websocket.send_text(json.dumps({
                    "event": "lock_response",
                    "node_id": node_id,
                    "success": success,
                    "error": err
                }))
                if success:
                    await canvas_ws_manager.broadcast(
                        canvas_id,
                        {
                            "event": "node_locked",
                            "node_id": node_id,
                            "locked_by": actual_client_id,
                            "expires_at": time.time() + timeout_sec
                        },
                        exclude_client_id=actual_client_id
                    )

            elif action == "release_lock":
                node_id = msg.get("node_id")
                success = occ.release_lock(node_id, actual_client_id)
                await websocket.send_text(json.dumps({
                    "event": "release_lock_response",
                    "node_id": node_id,
                    "success": success
                }))
                if success:
                    await canvas_ws_manager.broadcast(
                        canvas_id,
                        {"event": "node_unlocked", "node_id": node_id, "released_by": actual_client_id},
                        exclude_client_id=actual_client_id
                    )

            elif action == "apply_patch":
                patch_dict = msg.get("patch", {})
                op_type_str = str(patch_dict.get("op_type", "")).upper()
                try:
                    op_type = PatchOpType(op_type_str)
                except ValueError:
                    await websocket.send_text(json.dumps({
                        "event": "patch_rejected",
                        "error": f"Unknown op_type '{op_type_str}'"
                    }))
                    continue

                patch = CanvasPatchOp(
                    op_type=op_type,
                    client_id=actual_client_id,
                    base_version=int(patch_dict.get("base_version", occ.current_version)),
                    payload=patch_dict.get("payload", {})
                )
                success, new_ver, conflict, err = occ.apply_patch(patch)

                if success:
                    ack_event = {
                        "event": "patch_applied",
                        "patch_id": patch.patch_id,
                        "version": new_ver,
                        "patch": patch.to_dict()
                    }
                    # Send ack to sender
                    await websocket.send_text(json.dumps(ack_event))
                    # Broadcast patch to all other collaborators
                    await canvas_ws_manager.broadcast(
                        canvas_id,
                        {
                            "event": "remote_patch",
                            "version": new_ver,
                            "patch": patch.to_dict()
                        },
                        exclude_client_id=actual_client_id
                    )
                else:
                    await websocket.send_text(json.dumps({
                        "event": "patch_rejected",
                        "error": err,
                        "conflict": conflict,
                        "current_version": occ.current_version
                    }))

            elif action == "node_state_pulse":
                node_id = msg.get("node_id")
                state = msg.get("state", "Active")
                meta = msg.get("meta", {})
                await canvas_ws_manager.broadcast_node_state(canvas_id, node_id, state, meta)

            elif action == "selection_change":
                selected_node_ids = msg.get("selected_node_ids", [])
                await canvas_ws_manager.broadcast(
                    canvas_id,
                    {
                        "event": "remote_selection",
                        "client_id": actual_client_id,
                        "selected_node_ids": selected_node_ids
                    },
                    exclude_client_id=actual_client_id
                )

    except WebSocketDisconnect:
        disconnected_id = canvas_ws_manager.disconnect(websocket, canvas_id)
        if disconnected_id:
            await canvas_ws_manager.broadcast(
                canvas_id,
                {
                    "event": "user_left",
                    "client_id": disconnected_id,
                    "active_collaborators_count": len(canvas_ws_manager.active_sessions.get(canvas_id, []))
                }
            )
