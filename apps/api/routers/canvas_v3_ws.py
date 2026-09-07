# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_canvas_v3_ws"
# purpose: "FastAPI WebSocket Multiplexer for Infinite Canvas V3: Real-Time Presence, Delta Cursors & Concurrency Locks (DNK-CANVAS-003 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import os
import json
import logging
import time
import asyncio
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from apps.api.services.canvas_collaboration_arbiter import CanvasCollaborationArbiter
from apps.api.logging.structured_logger import (
    structured_logger,
    get_trace_id,
    set_trace_id,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3/ws/canvas", tags=["Canvas V3 Real-Time WS"])

# Shared arbiter registry for WebSocket sessions
_WS_ARBITERS: Dict[str, CanvasCollaborationArbiter] = {}


def _get_ws_arbiter(canvas_id: str) -> CanvasCollaborationArbiter:
    if canvas_id not in _WS_ARBITERS:
        _WS_ARBITERS[canvas_id] = CanvasCollaborationArbiter(canvas_id=canvas_id)
    return _WS_ARBITERS[canvas_id]


class CanvasV3WebSocketManager:
    """Manages active WebSocket connections, multi-peer broadcasting and event multiplexing per canvas room."""

    def __init__(self):
        self.active_connections: Dict[str, List[Dict[str, Any]]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        canvas_id: str,
        user_id: str,
        user_name: str = "Anonymous",
        user_color: str = "#6366f1",
    ):
        await websocket.accept()
        if canvas_id not in self.active_connections:
            self.active_connections[canvas_id] = []

        trace_id = str(uuid.uuid4())
        client_info = {
            "ws": websocket,
            "user_id": user_id,
            "user_name": user_name,
            "user_color": user_color,
            "joined_at": time.time(),
            "trace_id": trace_id,
        }
        self.active_connections[canvas_id].append(client_info)

        # Welcome message to the connecting client
        await websocket.send_text(
            json.dumps({
                "type": "CONNECTED",
                "canvas_id": canvas_id,
                "user_id": user_id,
                "active_collaborators": len(self.active_connections[canvas_id]),
                "trace_id": trace_id,
            })
        )

        # Notify peers about new participant
        await self.broadcast_except(
            canvas_id=canvas_id,
            exclude_user_id=user_id,
            message={
                "type": "USER_JOINED",
                "event": "USER_JOINED",
                "canvas_id": canvas_id,
                "user_id": user_id,
                "user_name": user_name,
                "user_color": user_color,
                "timestamp": time.time(),
                "trace_id": trace_id,
            },
        )

    async def disconnect(self, websocket: WebSocket, canvas_id: str, user_id: str):
        trace_id = get_trace_id()
        if canvas_id in self.active_connections:
            for c in self.active_connections[canvas_id]:
                if c["ws"] == websocket:
                    trace_id = c.get("trace_id", trace_id)
                    break
            self.active_connections[canvas_id] = [
                c
                for c in self.active_connections[canvas_id]
                if c["ws"] != websocket and c["user_id"] != user_id
            ]
            structured_logger.info(
                f"WebSocket disconnected: user {user_id} from canvas {canvas_id}",
                event="DISCONNECT",
                canvas_id=canvas_id,
                user_id=user_id,
                trace_id=trace_id,
            )
            if not self.active_connections[canvas_id]:
                del self.active_connections[canvas_id]
            else:
                await self.broadcast(
                    canvas_id=canvas_id,
                    message={
                        "type": "USER_LEFT",
                        "event": "USER_LEFT",
                        "canvas_id": canvas_id,
                        "user_id": user_id,
                        "timestamp": time.time(),
                        "trace_id": trace_id,
                    },
                )

    async def broadcast(self, canvas_id: str, message: Dict[str, Any]):
        if canvas_id not in self.active_connections:
            return

        if "trace_id" not in message:
            message["trace_id"] = get_trace_id()

        payload_str = json.dumps(message)
        dead_connections = []
        for client in self.active_connections[canvas_id]:
            try:
                await client["ws"].send_text(payload_str)
            except Exception:
                dead_connections.append(client["ws"])

        for dead_ws in dead_connections:
            self.active_connections[canvas_id] = [
                c
                for c in self.active_connections[canvas_id]
                if c["ws"] != dead_ws
            ]

    async def broadcast_except(
        self, canvas_id: str, exclude_user_id: str, message: Dict[str, Any]
    ):
        if canvas_id not in self.active_connections:
            return

        if "trace_id" not in message:
            message["trace_id"] = get_trace_id()

        payload_str = json.dumps(message)
        dead_connections = []
        for client in self.active_connections[canvas_id]:
            if client["user_id"] == exclude_user_id:
                continue
            try:
                await client["ws"].send_text(payload_str)
            except Exception:
                dead_connections.append(client["ws"])

        for dead_ws in dead_connections:
            self.active_connections[canvas_id] = [
                c
                for c in self.active_connections[canvas_id]
                if c["ws"] != dead_ws
            ]


ws_manager = CanvasV3WebSocketManager()


@router.websocket("/{canvas_id}")
async def canvas_v3_websocket_endpoint(
    websocket: WebSocket,
    canvas_id: str,
    user_id: str = "guest_user",
    user_name: str = "Anonymous",
    user_color: str = "#6366f1",
):
    trace_id = str(uuid.uuid4())
    set_trace_id(trace_id)
    structured_logger.info(
        f"WebSocket connection request for canvas {canvas_id} by user {user_id}",
        event="CONNECT",
        canvas_id=canvas_id,
        user_id=user_id,
        trace_id=trace_id,
    )
    await ws_manager.connect(
        websocket=websocket,
        canvas_id=canvas_id,
        user_id=user_id,
        user_name=user_name,
        user_color=user_color,
    )
    arbiter = _get_ws_arbiter(canvas_id)

    try:
        while True:
            raw_text = await websocket.receive_text()
            try:
                data = json.loads(raw_text)
            except Exception as parse_err:
                structured_logger.error(
                    f"WebSocket invalid JSON received: {parse_err}",
                    event="ERROR",
                    canvas_id=canvas_id,
                    user_id=user_id,
                    trace_id=trace_id,
                )
                continue

            msg_trace_id = data.get("trace_id") or trace_id
            set_trace_id(msg_trace_id)
            event_type = data.get("action") or data.get("type") or data.get("event")
            structured_logger.info(
                f"WebSocket event: {event_type} on {canvas_id}",
                event="MESSAGE",
                canvas_id=canvas_id,
                user_id=user_id,
                event_type=event_type,
                trace_id=msg_trace_id,
            )

            if event_type == "PRESENCE_HEARTBEAT":
                presence = arbiter.record_presence_heartbeat(
                    user_id=user_id,
                    user_name=user_name,
                    user_color=user_color,
                    cursor_x=float(data.get("cursor_x", 0.0)),
                    cursor_y=float(data.get("cursor_y", 0.0)),
                    viewport_bounds=data.get("viewport_bounds") or data.get("viewport"),
                    selected_node_ids=data.get("selected_node_ids"),
                    active_tool=data.get("active_tool", "select"),
                )
                await websocket.send_text(
                    json.dumps({
                        "type": "PRESENCE_ACK",
                        "status": "ok",
                        "presence": presence,
                    })
                )
                await ws_manager.broadcast_except(
                    canvas_id=canvas_id,
                    exclude_user_id=user_id,
                    message={"type": "PRESENCE_UPDATE", "event": "PRESENCE_UPDATE", "presence": presence},
                )

            elif event_type == "CURSOR_STREAM":
                cursor_res = arbiter.process_cursor_event(
                    user_id=user_id,
                    event_type=data.get("cursor_event") or data.get("event_type", "move"),
                    x=float(data.get("x", 0.0)),
                    y=float(data.get("y", 0.0)),
                    payload=data.get("payload"),
                )
                await websocket.send_text(
                    json.dumps({
                        "type": "CURSOR_ACK",
                        "status": "ok",
                        "cursor": cursor_res,
                    })
                )
                await ws_manager.broadcast_except(
                    canvas_id=canvas_id,
                    exclude_user_id=user_id,
                    message={
                        "type": "CURSOR_DELTA",
                        "event": "CURSOR_DELTA",
                        "user_id": user_id,
                        "cursor": cursor_res,
                    },
                )

            elif event_type == "LOCK_ACQUIRE":
                node_id = data.get("node_id")
                ttl_sec = float(data.get("ttl_sec", 15.0))
                res = arbiter.acquire_node_lock(
                    node_id=node_id,
                    user_id=user_id,
                    user_name=user_name,
                    ttl_sec=ttl_sec,
                )
                await websocket.send_text(
                    json.dumps({
                        "type": "LOCK_RESULT",
                        "event": "LOCK_ACQUIRE_RESULT",
                        "node_id": node_id,
                        "success": res.get("success", False),
                        "result": res,
                    })
                )
                if res.get("success"):
                    await ws_manager.broadcast_except(
                        canvas_id=canvas_id,
                        exclude_user_id=user_id,
                        message={
                            "type": "NODE_LOCKED",
                            "event": "NODE_LOCKED",
                            "node_id": node_id,
                            "user_id": user_id,
                            "lock": res.get("lock"),
                        },
                    )

            elif event_type == "LOCK_RELEASE":
                node_id = data.get("node_id")
                released = arbiter.release_node_lock(
                    node_id=node_id, user_id=user_id
                )
                await websocket.send_text(
                    json.dumps({
                        "type": "LOCK_RELEASED",
                        "event": "LOCK_RELEASE_RESULT",
                        "node_id": node_id,
                        "success": released,
                        "released": released,
                    })
                )
                if released:
                    await ws_manager.broadcast_except(
                        canvas_id=canvas_id,
                        exclude_user_id=user_id,
                        message={"type": "NODE_UNLOCKED", "event": "NODE_UNLOCKED", "node_id": node_id},
                    )

            elif event_type in ("SWARM_COMMAND", "swarm_command", "TASK_COMMAND", "EXECUTE_COMMAND"):
                command_text = data.get("command") or data.get("payload", {}).get("command") or data.get("text", "")
                target_agent = data.get("target_agent") or data.get("payload", {}).get("target_agent", "gerych_prime")
                
                # Send immediate dispatch ack
                await websocket.send_text(
                    json.dumps({
                        "type": "SWARM_ACK",
                        "event": "SWARM_ACK",
                        "status": "queued",
                        "command": command_text,
                        "target_agent": target_agent,
                        "timestamp": time.time(),
                    })
                )
                
                # Stream thought & execution log
                await websocket.send_text(
                    json.dumps({
                        "type": "SWARM_THOUGHT",
                        "event": "SWARM_THOUGHT",
                        "agent": target_agent,
                        "thought": f"Analyzing task request: '{command_text}' via TaskDNA DAG...",
                        "timestamp": time.time(),
                    })
                )
                await websocket.send_text(
                    json.dumps({
                        "type": "SWARM_LOG",
                        "event": "SWARM_LOG",
                        "agent": target_agent,
                        "log": f"[{target_agent.upper()}] Dispatched: {command_text} -> Swarm Worker Active",
                        "timestamp": time.time(),
                    })
                )
                await websocket.send_text(
                    json.dumps({
                        "type": "SWARM_RESPONSE",
                        "event": "SWARM_RESPONSE",
                        "sender": f"{target_agent.replace('_', ' ').title()}",
                        "text": f"Прийнято до виконання! Завдання '{command_text}' додано до черги рою. Працюю...",
                        "timestamp": time.time(),
                    })
                )

            elif event_type == "PING":
                await websocket.send_text(
                    json.dumps({"type": "PONG", "event": "PONG", "timestamp": time.time()})
                )

            elif event_type in ("TASK_EXECUTE", "task_execute"):
                try:
                    from apps.api.routers.swarm_ws import handle_task_execution
                    asyncio.create_task(handle_task_execution(websocket, data))
                except Exception as e:
                    logger.error(f"Error invoking handle_task_execution: {e}")

            elif event_type in ("OBSIDIAN_SYNC_REQUEST", "obsidian_sync_request"):
                try:
                    from core.obsidian.export_canvas import (
                        export_canvas_bundle,
                        DEFAULT_VAULT_TASKFOREST_PATH,
                        validate_vault_path,
                    )
                    from core.obsidian.import_canvas import (
                        import_obsidian_folder,
                        import_canvas_and_markdown,
                    )

                    direction = str(data.get("direction") or data.get("action_type") or "export")
                    raw_target_dir = data.get("target_dir") or data.get("vault_path")
                    # Security: strictly validate target_dir against canonical Vault root to prevent path traversal
                    target_dir = str(validate_vault_path(raw_target_dir))
                    canvas_name = str(data.get("canvas_name") or f"canvas_{canvas_id}")

                    if direction == "export":
                        nodes = data.get("nodes", [])
                        edges = data.get("edges", [])
                        export_md = bool(data.get("export_individual_md", True))
                        link_file = bool(data.get("link_as_file_nodes", False))

                        res = export_canvas_bundle(
                            nodes=nodes,
                            edges=edges,
                            canvas_name=canvas_name,
                            output_dir=target_dir,
                            export_individual_md=export_md,
                            link_as_file_nodes=link_file,
                        )
                        await websocket.send_text(
                            json.dumps({
                                "type": "OBSIDIAN_SYNC_STATUS",
                                "event": "OBSIDIAN_SYNC_STATUS",
                                "status": "success",
                                "canvas_id": canvas_id,
                                "direction": "export",
                                "result": res,
                                "timestamp": time.time(),
                            })
                        )

                    elif direction == "import":
                        canvas_file_raw = data.get("canvas_path") or data.get("canvas_file")
                        canvas_file = None
                        if canvas_file_raw:
                            cf_p = Path(os.path.expanduser(str(canvas_file_raw)))
                            if not cf_p.is_absolute():
                                cf_p = Path(target_dir) / cf_p
                            canvas_file = str(validate_vault_path(cf_p.parent) / cf_p.name)

                        if not canvas_file and target_dir:
                            res = import_obsidian_folder(
                                folder_path=target_dir,
                                canvas_filename=data.get("canvas_filename"),
                                conflict_strategy=str(data.get("conflict_strategy", "last-write-wins")),
                            )
                        else:
                            res = import_canvas_and_markdown(
                                canvas_source=canvas_file,
                                markdown_sources=target_dir,
                                conflict_strategy=str(data.get("conflict_strategy", "last-write-wins")),
                            )
                        await websocket.send_text(
                            json.dumps({
                                "type": "OBSIDIAN_SYNC_STATUS",
                                "event": "OBSIDIAN_SYNC_STATUS",
                                "status": "success",
                                "canvas_id": canvas_id,
                                "direction": "import",
                                "nodes": res.get("nodes", []),
                                "edges": res.get("edges", []),
                                "result": res,
                                "timestamp": time.time(),
                            })
                        )

                    elif direction in ("sync", "both"):
                        nodes = data.get("nodes", [])
                        edges = data.get("edges", [])
                        if nodes:
                            export_canvas_bundle(
                                nodes=nodes,
                                edges=edges,
                                canvas_name=canvas_name,
                                output_dir=target_dir,
                            )
                        res = import_obsidian_folder(
                            folder_path=target_dir,
                            conflict_strategy=str(data.get("conflict_strategy", "last-write-wins")),
                        )
                        await websocket.send_text(
                            json.dumps({
                                "type": "OBSIDIAN_SYNC_STATUS",
                                "event": "OBSIDIAN_SYNC_STATUS",
                                "status": "success",
                                "canvas_id": canvas_id,
                                "direction": "sync",
                                "nodes": res.get("nodes", []),
                                "edges": res.get("edges", []),
                                "result": res,
                                "timestamp": time.time(),
                            })
                        )
                    else:
                        raise ValueError(f"Unsupported sync direction: {direction}")

                except Exception as sync_err:
                    logger.error(f"Error handling OBSIDIAN_SYNC_REQUEST: {sync_err}", exc_info=True)
                    await websocket.send_text(
                        json.dumps({
                            "type": "OBSIDIAN_SYNC_STATUS",
                            "event": "OBSIDIAN_SYNC_STATUS",
                            "status": "error",
                            "canvas_id": canvas_id,
                            "error": str(sync_err),
                            "timestamp": time.time(),
                        })
                    )

    except WebSocketDisconnect:
        await ws_manager.disconnect(
            websocket=websocket, canvas_id=canvas_id, user_id=user_id
        )
    except Exception as e:
        structured_logger.error(
            f"Error in Canvas V3 WebSocket for {user_id}: {e}",
            event="ERROR",
            canvas_id=canvas_id,
            user_id=user_id,
            trace_id=get_trace_id() or trace_id,
            error=str(e),
        )
        logger.error(f"Error in Canvas V3 WebSocket for {user_id}: {e}")
        await ws_manager.disconnect(
            websocket=websocket, canvas_id=canvas_id, user_id=user_id
        )


@router.websocket("")
@router.websocket("/")
async def canvas_v3_websocket_root_endpoint(
    websocket: WebSocket,
    canvas_id: str = "default_canvas",
    user_id: str = "guest_user",
    user_name: str = "Anonymous",
    user_color: str = "#6366f1",
):
    await canvas_v3_websocket_endpoint(
        websocket=websocket,
        canvas_id=canvas_id,
        user_id=user_id,
        user_name=user_name,
        user_color=user_color,
    )

