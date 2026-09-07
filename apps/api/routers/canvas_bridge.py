# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/canvas_bridge.py"
# purpose: "FastAPI REST endpoints for bidirectional Obsidian Canvas ↔ React Flow SSOT synchronization."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK Swarm (dnk_dev_fullstack & Gerych Prime)"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from core.orchestrator.visual_canvas_control import (
    DEFAULT_CONTROL_PANEL_PATH,
    VisualCanvasControlEngine,
    AGENT_BADGES,
    SWARM_WORKER_COLORS,
)
from core.occ_merge import OCCConcurrencyEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/canvas/bridge", tags=["Canvas Bridge"])
engine = VisualCanvasControlEngine()


class CanvasBridgeConnectionManager:
    """
    Manages active WebSocket connections for Canvas Bridge and Live Swarm HUD.
    Enables cross-connection broadcasting of swarm agent lifecycle events:
    - TASK_STARTED
    - TASK_PROGRESS
    - TASK_COMPLETED
    - TASK_FAILED
    """

    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._path_subscriptions: Dict[str, Set[WebSocket]] = {}
        self._total_events_broadcast: int = 0

    def get_stats(self) -> Dict[str, Any]:
        """Returns diagnostic statistics of active WebSocket connections and observed canvases."""
        return {
            "total_connections": len(self._connections),
            "subscribed_canvases_count": len(self._path_subscriptions),
            "subscribed_canvases": list(self._path_subscriptions.keys()),
            "canvas_connection_counts": {k: len(v) for k, v in self._path_subscriptions.items()},
            "total_events_broadcast": self._total_events_broadcast,
        }

    async def connect(self, websocket: WebSocket, canvas_path: str):
        self._connections.add(websocket)
        norm_path = os.path.normpath(canvas_path)
        if norm_path not in self._path_subscriptions:
            self._path_subscriptions[norm_path] = set()
        self._path_subscriptions[norm_path].add(websocket)

    def disconnect(self, websocket: WebSocket, canvas_path: str):
        self._connections.discard(websocket)
        norm_path = os.path.normpath(canvas_path)
        if norm_path in self._path_subscriptions:
            self._path_subscriptions[norm_path].discard(websocket)
            if not self._path_subscriptions[norm_path]:
                del self._path_subscriptions[norm_path]

    async def broadcast_swarm_event(self, event_data: Dict[str, Any], canvas_path: Optional[str] = None) -> int:
        """Broadcasts a SWARM_HUD event to relevant canvas subscribers or all connected clients."""
        payload = {
            "type": "SWARM_HUD_EVENT",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event_data,
        }
        targets: Set[WebSocket] = set()
        if canvas_path:
            norm_path = os.path.normpath(canvas_path)
            targets.update(self._path_subscriptions.get(norm_path, set()))
        if not targets:
            targets = set(self._connections)

        dead: List[WebSocket] = []
        sent_count = 0
        for ws in targets:
            try:
                await ws.send_json(payload)
                sent_count += 1
            except Exception:
                dead.append(ws)

        if sent_count > 0:
            self._total_events_broadcast += sent_count

        for ws in dead:
            self._connections.discard(ws)
            if canvas_path:
                norm_path = os.path.normpath(canvas_path)
                if norm_path in self._path_subscriptions:
                    self._path_subscriptions[norm_path].discard(ws)

        return sent_count


canvas_ws_manager = CanvasBridgeConnectionManager()


def format_swarm_hud_payload(
    task_id: str,
    event_type: str,
    assigned_agent: str,
    progress_pct: Optional[int] = None,
    message: Optional[str] = None,
    canvas_path: Optional[str] = None,
) -> Dict[str, Any]:
    norm_agent = assigned_agent.strip().lower()
    meta = SWARM_WORKER_COLORS.get(norm_agent, {
        "canvas_color": "5",
        "hex": "#3B82F6",
        "badge": AGENT_BADGES.get(norm_agent, f"🤖 {assigned_agent}"),
    })

    stage_map = {
        "TASK_STARTED": "in_progress",
        "TASK_PROGRESS": "in_progress",
        "TASK_COMPLETED": "completed",
        "TASK_FAILED": "failed",
    }
    stage = stage_map.get(event_type.upper(), "in_progress")

    progress_bar = None
    if progress_pct is not None:
        progress_bar = engine.render_progress_bar(progress_pct, 100)

    return {
        "task_id": task_id,
        "event_type": event_type.upper(),
        "stage": stage,
        "assigned_agent": assigned_agent,
        "agent_badge": meta.get("badge", f"🤖 {assigned_agent}"),
        "canvas_color": meta.get("canvas_color", "5"),
        "hex_color": meta.get("hex", "#3B82F6"),
        "progress_pct": progress_pct,
        "progress_bar": progress_bar,
        "message": message or f"Worker {assigned_agent} is {stage}",
        "canvas_path": canvas_path,
    }


class SwarmHudEventRequest(BaseModel):
    task_id: str = Field(..., description="Target node or task ID on the canvas")
    event_type: str = Field(..., description="Lifecycle stage: TASK_STARTED, TASK_PROGRESS, TASK_COMPLETED, TASK_FAILED")
    assigned_agent: str = Field("gerych_builder", description="Assigned swarm worker role")
    canvas_path: Optional[str] = Field(None, description="Path to .canvas file, defaults to control panel")
    progress_pct: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage (0-100)")
    message: Optional[str] = Field(None, description="Live status or log message")
    update_canvas_disk: bool = Field(False, description="Whether to mutate and persist the node status/color to disk immediately")


class SwarmHudEventResponse(BaseModel):
    status: str
    event_type: str
    task_id: str
    assigned_agent: str
    agent_badge: str
    canvas_color: str
    hex_color: str
    progress_pct: Optional[int] = None
    progress_bar: Optional[str] = None
    message: Optional[str] = None
    clients_notified: int
    disk_updated: bool


class CanvasToFlowRequest(BaseModel):
    canvas_data: Dict[str, Any] = Field(..., description="Obsidian JSON Canvas data")


class FlowToCanvasRequest(BaseModel):
    flow_data: Dict[str, Any] = Field(..., description="React Flow data with nodes and edges")
    canvas_path: Optional[str] = Field(None, description="Optional relative file path to save in Obsidian Vault")


class CanvasMergeRequest(BaseModel):
    canvas_path: Optional[str] = Field(None, description="Relative file path of target Obsidian Canvas")
    base_flow: Optional[Dict[str, Any]] = Field(None, description="Base ancestor snapshot in React Flow schema")
    incoming_flow: Dict[str, Any] = Field(..., description="Incoming client mutation in React Flow schema")
    position_strategy: str = Field("last_write_wins", description="Strategy for position conflicts: 'shift', 'last_write_wins', 'first_write_wins'")


def _occ_merged_to_react_flow(merged_graph: Dict[str, Any]) -> Dict[str, Any]:
    nodes_raw = merged_graph.get("nodes", {})
    edges_raw = merged_graph.get("edges", [])

    if isinstance(nodes_raw, dict):
        nodes_list = list(nodes_raw.values())
    elif isinstance(nodes_raw, list):
        nodes_list = nodes_raw
    else:
        nodes_list = []

    flow_nodes = [
        {
            "id": str(n.get("id")),
            "type": n.get("type", "custom_node"),
            "position": n.get("position", {"x": 0.0, "y": 0.0}),
            "dimensions": n.get("dimensions", {"width": 380.0, "height": 240.0}),
            "data": n.get("data", {}),
        }
        for n in nodes_list
    ]

    flow_edges = [
        {
            "id": str(e.get("id", f"{e.get('source')}-{e.get('target')}")),
            "source": str(e.get("source")),
            "target": str(e.get("target")),
            "type": e.get("type", "default"),
            "animated": e.get("animated", False),
        }
        for e in (edges_raw if isinstance(edges_raw, list) else [])
    ]

    return {"nodes": flow_nodes, "edges": flow_edges}


class TriggerCheckRequest(BaseModel):
    canvas_path: Optional[str] = Field(None, description="Relative path to target canvas")


def _read_canvas(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Canvas file not found at: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_canvas(data: Dict[str, Any], path: str) -> str:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


@router.get("/obsidian")
async def get_obsidian_as_react_flow(
    canvas_path: str = Query(str(DEFAULT_CONTROL_PANEL_PATH), description="Path to .canvas file")
) -> Dict[str, Any]:
    """
    Loads an Obsidian Canvas file from disk and translates it into React Flow format.
    """
    try:
        canvas_data = _read_canvas(canvas_path)
        react_flow_data = engine.canvas_to_react_flow(canvas_data)
        return {
            "status": "success",
            "canvas_path": canvas_path,
            "react_flow": react_flow_data,
            "node_count": len(react_flow_data.get("nodes", [])),
            "edge_count": len(react_flow_data.get("edges", [])),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to load obsidian canvas at '{canvas_path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to load and convert canvas: {str(e)}")


@router.post("/react-flow-to-canvas")
async def save_react_flow_to_obsidian(payload: FlowToCanvasRequest) -> Dict[str, Any]:
    """
    Converts React Flow format into Obsidian JSON Canvas and saves it to disk.
    """
    try:
        target_path = payload.canvas_path or str(DEFAULT_CONTROL_PANEL_PATH)
        canvas_data = engine.react_flow_to_canvas(payload.flow_data)
        saved_path = _write_canvas(canvas_data, target_path)
        return {
            "status": "success",
            "canvas_path": saved_path,
            "node_count": len(canvas_data.get("nodes", [])),
            "edge_count": len(canvas_data.get("edges", [])),
        }
    except Exception as e:
        logger.error(f"Failed to save react flow to obsidian: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save canvas: {str(e)}")


@router.post("/convert/canvas-to-flow")
async def convert_canvas_to_flow_in_memory(payload: CanvasToFlowRequest) -> Dict[str, Any]:
    """
    In-memory transformation from Obsidian Canvas to React Flow.
    """
    try:
        react_flow_data = engine.canvas_to_react_flow(payload.canvas_data)
        return {
            "status": "success",
            "react_flow": react_flow_data,
        }
    except Exception as e:
        logger.error(f"In-memory conversion error (canvas -> flow): {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Conversion error: {str(e)}")


@router.post("/convert/flow-to-canvas")
async def convert_flow_to_canvas_in_memory(payload: FlowToCanvasRequest) -> Dict[str, Any]:
    """
    In-memory transformation from React Flow to Obsidian Canvas.
    """
    try:
        canvas_data = engine.react_flow_to_canvas(payload.flow_data)
        return {
            "status": "success",
            "canvas": canvas_data,
        }
    except Exception as e:
        logger.error(f"In-memory conversion error (flow -> canvas): {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Conversion error: {str(e)}")


@router.post("/trigger-check")
async def check_and_execute_triggers(payload: Optional[TriggerCheckRequest] = None) -> Dict[str, Any]:
    """
    Polls the canvas for interactive checkboxes (- [x] Run Tests, - [x] Dispatch Worker)
    and executes them.
    """
    target_path = payload.canvas_path if payload and payload.canvas_path else str(DEFAULT_CONTROL_PANEL_PATH)
    try:
        result = engine.poll_and_execute_canvas_triggers(target_path)
        return {
            "status": "success",
            "canvas_path": target_path,
            "result": result,
        }
    except Exception as e:
        logger.error(f"Trigger check error on '{target_path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Trigger execution error: {str(e)}")


@router.post("/merge")
async def merge_canvas_state(payload: CanvasMergeRequest) -> Dict[str, Any]:
    """
    OCC 3-Way Structural Graph Mutation Resolver for Canvas Bridge.
    Merges incoming React Flow mutation with current disk Obsidian Canvas state against base snapshot.
    Resolves concurrent edits between React Flow and Obsidian Canvas without data loss.
    """
    target_path = payload.canvas_path or str(DEFAULT_CONTROL_PANEL_PATH)
    try:
        if not os.path.exists(target_path):
            raise HTTPException(status_code=404, detail=f"Canvas file not found: {target_path}")

        current_canvas = _read_canvas(target_path)
        theirs_flow = engine.canvas_to_react_flow(current_canvas)
        base_flow = payload.base_flow or theirs_flow

        merge_result = OCCConcurrencyEngine.merge_graph_state(
            base_state=base_flow,
            current_state=theirs_flow,
            incoming_state=payload.incoming_flow,
            position_strategy=payload.position_strategy,
        )

        final_react_flow = _occ_merged_to_react_flow(merge_result.merged_graph)
        canvas_data = engine.react_flow_to_canvas(final_react_flow)
        _write_canvas(canvas_data, target_path)

        return {
            "status": merge_result.status,
            "canvas_path": target_path,
            "has_unresolved_conflicts": merge_result.has_unresolved_conflicts,
            "applied_mutations": merge_result.applied_mutations,
            "conflicts": [c.to_dict() for c in merge_result.conflicts],
            "react_flow": final_react_flow,
            "node_count": len(final_react_flow["nodes"]),
            "edge_count": len(final_react_flow["edges"]),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCC 3-Way Merge failed on '{target_path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OCC merge failed: {str(e)}")


@router.post("/events/swarm", response_model=SwarmHudEventResponse)
@router.post("/swarm-hud", response_model=SwarmHudEventResponse)
async def publish_swarm_hud_event(request: SwarmHudEventRequest):
    """
    Publishes a Swarm Worker lifecycle event to the Live Swarm HUD.
    Broadcasts real-time worker status (TASK_STARTED, TASK_PROGRESS, TASK_COMPLETED, TASK_FAILED)
    with agent badge, canvas color-coding, and progress bar to all connected Canvas WebSocket clients.
    Optionally mutates the target node on disk in the Obsidian .canvas file.
    """
    canvas_path = request.canvas_path or str(DEFAULT_CONTROL_PANEL_PATH)
    event_payload = format_swarm_hud_payload(
        task_id=request.task_id,
        event_type=request.event_type,
        assigned_agent=request.assigned_agent,
        progress_pct=request.progress_pct,
        message=request.message,
        canvas_path=canvas_path,
    )

    disk_updated = False
    if request.update_canvas_disk and os.path.exists(canvas_path):
        try:
            notes_str = f"{event_payload['agent_badge']}: {event_payload['message']}"
            if event_payload["progress_bar"]:
                notes_str += f" {event_payload['progress_bar']}"
            engine.update_node_stage(
                node_id=request.task_id,
                new_stage=event_payload["stage"],
                canvas_path=canvas_path,
                notes=notes_str,
            )
            disk_updated = True
        except Exception as e:
            logger.warning(f"Could not update node on disk: {e}")

    notified = await canvas_ws_manager.broadcast_swarm_event(event_payload, canvas_path=canvas_path)

    return SwarmHudEventResponse(
        status="broadcasted",
        event_type=event_payload["event_type"],
        task_id=event_payload["task_id"],
        assigned_agent=event_payload["assigned_agent"],
        agent_badge=event_payload["agent_badge"],
        canvas_color=event_payload["canvas_color"],
        hex_color=event_payload["hex_color"],
        progress_pct=event_payload["progress_pct"],
        progress_bar=event_payload["progress_bar"],
        message=event_payload["message"],
        clients_notified=notified,
        disk_updated=disk_updated,
    )


@router.websocket("/ws")
async def websocket_canvas_stream(
    websocket: WebSocket,
    canvas_path: str = Query(str(DEFAULT_CONTROL_PANEL_PATH), description="Path to .canvas file")
):
    """
    Real-time bidirectional WebSocket stream for Obsidian Canvas ↔ React Flow sync.
    Pushes initial canvas state, accepts updates, trigger executions, and ping/pong.
    Includes reactive FileWatcher that pushes CANVAS_UPDATE when the file is modified on disk.
    Also acts as the real-time Live Swarm HUD event stream for agent activities.
    """
    await websocket.accept()
    await canvas_ws_manager.connect(websocket, canvas_path)

    last_mtime = os.path.getmtime(canvas_path) if os.path.exists(canvas_path) else None

    # Send initial canvas state
    try:
        if os.path.exists(canvas_path):
            raw = _read_canvas(canvas_path)
            flow = engine.canvas_to_react_flow(raw)
            await websocket.send_json({
                "type": "INITIAL_STATE",
                "canvas_path": canvas_path,
                "react_flow": flow,
                "node_count": len(flow.get("nodes", [])),
                "edge_count": len(flow.get("edges", [])),
            })
        else:
            await websocket.send_json({
                "type": "ERROR",
                "message": f"Canvas file not found: {canvas_path}"
            })
    except Exception as e:
        await websocket.send_json({"type": "ERROR", "message": str(e)})

    async def file_watcher():
        nonlocal last_mtime
        try:
            while True:
                await asyncio.sleep(0.5)
                if os.path.exists(canvas_path):
                    current_mtime = os.path.getmtime(canvas_path)
                    if last_mtime is None or current_mtime > last_mtime:
                        last_mtime = current_mtime
                        try:
                            raw = _read_canvas(canvas_path)
                            flow = engine.canvas_to_react_flow(raw)
                            await websocket.send_json({
                                "type": "CANVAS_UPDATE",
                                "source": "file_watcher",
                                "canvas_path": canvas_path,
                                "react_flow": flow,
                            })
                        except Exception as err:
                            logger.warning(f"File watcher read error: {err}")
        except asyncio.CancelledError:
            pass
        except Exception as err:
            logger.warning(f"File watcher exception: {err}")

    watcher_task = asyncio.create_task(file_watcher())

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            if action == "ping":
                await websocket.send_json({"type": "PONG", "status": "ok"})
            elif action == "refresh":
                if os.path.exists(canvas_path):
                    raw = _read_canvas(canvas_path)
                    flow = engine.canvas_to_react_flow(raw)
                    last_mtime = os.path.getmtime(canvas_path)
                    await websocket.send_json({
                        "type": "CANVAS_UPDATE",
                        "canvas_path": canvas_path,
                        "react_flow": flow,
                    })
                else:
                    await websocket.send_json({
                        "type": "ERROR",
                        "message": f"Canvas file not found: {canvas_path}"
                    })
            elif action == "trigger_check":
                result = engine.poll_and_execute_canvas_triggers(canvas_path)
                raw = _read_canvas(canvas_path) if os.path.exists(canvas_path) else {}
                flow = engine.canvas_to_react_flow(raw) if raw else {"nodes": [], "edges": []}
                if os.path.exists(canvas_path):
                    last_mtime = os.path.getmtime(canvas_path)
                await websocket.send_json({
                    "type": "TRIGGER_EXECUTED",
                    "canvas_path": canvas_path,
                    "result": result,
                    "react_flow": flow,
                })
            elif action in ("update", "merge"):
                react_flow = data.get("react_flow") or data.get("incoming_flow", {})
                base_flow = data.get("base_flow")
                pos_strat = data.get("position_strategy", "last_write_wins")

                if base_flow and os.path.exists(canvas_path):
                    current_canvas = _read_canvas(canvas_path)
                    theirs_flow = engine.canvas_to_react_flow(current_canvas)
                    merge_result = OCCConcurrencyEngine.merge_graph_state(
                        base_state=base_flow,
                        current_state=theirs_flow,
                        incoming_state=react_flow,
                        position_strategy=pos_strat,
                    )
                    final_flow = _occ_merged_to_react_flow(merge_result.merged_graph)
                    canvas_data = engine.react_flow_to_canvas(final_flow)
                    _write_canvas(canvas_data, canvas_path)
                    if os.path.exists(canvas_path):
                        last_mtime = os.path.getmtime(canvas_path)
                    await websocket.send_json({
                        "type": "MERGED",
                        "canvas_path": canvas_path,
                        "status": merge_result.status,
                        "react_flow": final_flow,
                        "has_unresolved_conflicts": merge_result.has_unresolved_conflicts,
                        "conflicts": [c.to_dict() for c in merge_result.conflicts],
                        "applied_mutations": merge_result.applied_mutations,
                    })
                else:
                    canvas_data = engine.react_flow_to_canvas(react_flow)
                    _write_canvas(canvas_data, canvas_path)
                    if os.path.exists(canvas_path):
                        last_mtime = os.path.getmtime(canvas_path)
                    await websocket.send_json({
                        "type": "SAVED",
                        "canvas_path": canvas_path,
                        "status": "success",
                    })
            elif action == "swarm_event":
                task_id = data.get("task_id", "unknown_task")
                event_type = data.get("event_type", "TASK_PROGRESS")
                assigned_agent = data.get("assigned_agent", "gerych_builder")
                progress_pct = data.get("progress_pct")
                msg = data.get("message")
                update_disk = data.get("update_canvas_disk", False)

                event_payload = format_swarm_hud_payload(
                    task_id=task_id,
                    event_type=event_type,
                    assigned_agent=assigned_agent,
                    progress_pct=progress_pct,
                    message=msg,
                    canvas_path=canvas_path,
                )

                if update_disk and os.path.exists(canvas_path):
                    try:
                        notes_str = f"{event_payload['agent_badge']}: {event_payload['message']}"
                        if event_payload["progress_bar"]:
                            notes_str += f" {event_payload['progress_bar']}"
                        engine.update_node_stage(
                            node_id=task_id,
                            new_stage=event_payload["stage"],
                            canvas_path=canvas_path,
                            notes=notes_str,
                        )
                        last_mtime = os.path.getmtime(canvas_path)
                    except Exception as e:
                        logger.warning(f"Could not update node on disk from ws: {e}")

                sent = await canvas_ws_manager.broadcast_swarm_event(event_payload, canvas_path=canvas_path)
                await websocket.send_json({
                    "type": "SWARM_EVENT_ACK",
                    "status": "broadcasted",
                    "task_id": task_id,
                    "event_type": event_type,
                    "clients_notified": sent,
                })
            else:
                await websocket.send_json({
                    "type": "UNKNOWN_ACTION",
                    "action": action
                })
    except WebSocketDisconnect:
        logger.info(f"Canvas bridge WebSocket disconnected for {canvas_path}")
    except Exception as e:
        logger.warning(f"Canvas bridge WebSocket error for {canvas_path}: {e}")
    finally:
        canvas_ws_manager.disconnect(websocket, canvas_path)
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            pass

