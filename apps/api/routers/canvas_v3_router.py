# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_canvas_v3_router"
# purpose: "FastAPI REST Router for Infinite Canvas V3: Spatial Indexing, Node Locking, AI Subflow Synthesis & Time-Travel Snapshots (DNK-CANVAS-003 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Dict, List, Any, Optional, Tuple
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from apps.api.services.canvas_spatial_index_engine import CanvasSpatialIndexEngine
from apps.api.services.canvas_collaboration_arbiter import CanvasCollaborationArbiter
from apps.api.services.canvas_ai_node_weaver import CanvasAINodeWeaver
from apps.api.services.canvas_history_time_travel_engine import (
    CanvasHistoryTimeTravelEngine,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3/canvas", tags=["Canvas V3 Multi-User & AI"])

# Global in-memory state registries per canvas_id
_SPATIAL_ENGINES: Dict[str, CanvasSpatialIndexEngine] = {}
_ARBITERS: Dict[str, CanvasCollaborationArbiter] = {}
_WEAVERS: Dict[str, CanvasAINodeWeaver] = {}
_TIME_TRAVEL_ENGINES: Dict[str, CanvasHistoryTimeTravelEngine] = {}


def _get_spatial_engine(canvas_id: str) -> CanvasSpatialIndexEngine:
    if canvas_id not in _SPATIAL_ENGINES:
        _SPATIAL_ENGINES[canvas_id] = CanvasSpatialIndexEngine(canvas_id=canvas_id)
    return _SPATIAL_ENGINES[canvas_id]


def _get_arbiter(canvas_id: str) -> CanvasCollaborationArbiter:
    if canvas_id not in _ARBITERS:
        _ARBITERS[canvas_id] = CanvasCollaborationArbiter(canvas_id=canvas_id)
    return _ARBITERS[canvas_id]


def _get_weaver() -> CanvasAINodeWeaver:
    return CanvasAINodeWeaver()


def _get_time_travel_engine(canvas_id: str) -> CanvasHistoryTimeTravelEngine:
    if canvas_id not in _TIME_TRAVEL_ENGINES:
        _TIME_TRAVEL_ENGINES[canvas_id] = CanvasHistoryTimeTravelEngine(
            canvas_id=canvas_id
        )
    return _TIME_TRAVEL_ENGINES[canvas_id]


# --- Request & Response Schemas ---


class ViewportQueryRequest(BaseModel):
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    lod_filter: Optional[int] = None
    group_id_filter: Optional[str] = None


class NearestNeighborsRequest(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    k: int = 5
    max_distance: float = 1000.0


class NodeIndexItem(BaseModel):
    node_id: str
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    lod_level: int = 0
    group_id: Optional[str] = None


class NodeIndexRequest(BaseModel):
    nodes: List[NodeIndexItem]


class LockAcquireRequest(BaseModel):
    node_id: str
    user_id: str
    user_name: str = "Anonymous"
    lock_ttl_sec: float = 15.0
    ttl_sec: Optional[float] = None


class LockReleaseRequest(BaseModel):
    node_id: str
    user_id: str


class PresenceHeartbeatRequest(BaseModel):
    user_id: str
    user_name: str
    user_color: str
    cursor_x: float
    cursor_y: float
    viewport_bounds: Optional[Dict[str, float]] = None
    viewport: Optional[Dict[str, Any]] = None
    selected_node_ids: Optional[List[str]] = None
    active_tool: str = "select"


class CursorEventRequest(BaseModel):
    user_id: str
    event_type: str = "move"
    x: float
    y: float
    payload: Optional[Dict[str, Any]] = None


class AIGenerateSubflowRequest(BaseModel):
    prompt: str
    context_nodes: Optional[List[Dict[str, Any]]] = None
    target_origin: Optional[Tuple[float, float]] = None
    auto_group: bool = True
    group_title: Optional[str] = None


class SemanticGroupCreateRequest(BaseModel):
    title: str
    nodes: List[Dict[str, Any]]
    color: str = "#6366f1"
    padding: float = 30.0


class SnapshotCreateRequest(BaseModel):
    author_id: str
    state_data: Dict[str, Any]
    snapshot_tag: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BranchCreateRequest(BaseModel):
    branch_name: str
    from_snapshot_id: Optional[str] = None


class BranchMergeRequest(BaseModel):
    source_branch: str
    target_branch: str = "main"
    strategy: str = "theirs"


# --- REST Endpoints ---

# 1. Spatial Indexing Endpoints
@router.post("/{canvas_id}/spatial/index")
async def bulk_index_nodes(canvas_id: str, req: NodeIndexRequest):
    engine = _get_spatial_engine(canvas_id)
    items = [n.model_dump() for n in req.nodes]
    indexed_count = engine.bulk_index_nodes(items)
    return {
        "canvas_id": canvas_id,
        "indexed_count": indexed_count,
        "total_indexed": len(engine.items),
    }


@router.post("/{canvas_id}/spatial/query")
async def query_viewport_nodes(canvas_id: str, req: ViewportQueryRequest):
    engine = _get_spatial_engine(canvas_id)
    viewport = (req.min_x, req.min_y, req.max_x, req.max_y)
    results = engine.query_viewport(
        viewport_bbox=viewport,
        lod_filter=req.lod_filter,
        group_id=req.group_id_filter,
    )
    return {
        "canvas_id": canvas_id,
        "viewport": viewport,
        "total_visible_nodes": len(results),
        "nodes": results,
    }


@router.post("/{canvas_id}/spatial/nearest")
async def find_nearest_nodes(
    canvas_id: str,
    req: Optional[NearestNeighborsRequest] = None,
    x: Optional[float] = Query(None),
    y: Optional[float] = Query(None),
    k: int = Query(5),
    max_distance: float = Query(1000.0),
):
    target_x = x if x is not None else (req.x if req and req.x is not None else 0.0)
    target_y = y if y is not None else (req.y if req and req.y is not None else 0.0)
    target_k = k if req is None or req.k == 5 else req.k
    target_dist = max_distance if req is None or req.max_distance == 1000.0 else req.max_distance

    engine = _get_spatial_engine(canvas_id)
    results = engine.find_nearest_neighbors(
        x=target_x, y=target_y, k=target_k, max_distance=target_dist
    )
    return {
        "canvas_id": canvas_id,
        "query_point": {"x": target_x, "y": target_y},
        "total_neighbors": len(results),
        "neighbors": results,
        "results": results,
    }


# 2. Multi-User Lock & Collaboration Endpoints
@router.post("/{canvas_id}/lock/acquire")
async def acquire_node_lock(canvas_id: str, req: LockAcquireRequest):
    arbiter = _get_arbiter(canvas_id)
    effective_ttl = req.ttl_sec if req.ttl_sec is not None else req.lock_ttl_sec
    res = arbiter.acquire_node_lock(
        node_id=req.node_id,
        user_id=req.user_id,
        user_name=req.user_name,
        ttl_sec=effective_ttl,
    )
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Node {req.node_id} is locked by {res.get('locked_by', {}).get('user_name', 'another user')}",
        )
    return res


@router.post("/{canvas_id}/lock/release")
async def release_node_lock(canvas_id: str, req: LockReleaseRequest):
    arbiter = _get_arbiter(canvas_id)
    success = arbiter.release_node_lock(
        node_id=req.node_id, user_id=req.user_id
    )
    return {
        "canvas_id": canvas_id,
        "node_id": req.node_id,
        "success": success,
        "released": success,
    }


@router.get("/{canvas_id}/lock/list")
async def list_node_locks(canvas_id: str):
    arbiter = _get_arbiter(canvas_id)
    locks = arbiter.get_locked_nodes()
    return {"canvas_id": canvas_id, "locks": locks, "total_locks": len(locks)}


@router.post("/{canvas_id}/presence/heartbeat")
async def record_presence(canvas_id: str, req: PresenceHeartbeatRequest):
    arbiter = _get_arbiter(canvas_id)
    bounds = req.viewport_bounds or (
        {"min_x": float(req.viewport.get("x", 0)), "min_y": float(req.viewport.get("y", 0))}
        if req.viewport else None
    )
    presence = arbiter.record_presence_heartbeat(
        user_id=req.user_id,
        user_name=req.user_name,
        user_color=req.user_color,
        cursor_x=req.cursor_x,
        cursor_y=req.cursor_y,
        viewport_bounds=bounds,
        selected_node_ids=req.selected_node_ids,
        active_tool=req.active_tool,
    )
    return {"canvas_id": canvas_id, "success": True, "presence": presence}


@router.get("/{canvas_id}/presence/active")
async def list_active_presences(
    canvas_id: str, timeout_sec: float = Query(30.0)
):
    arbiter = _get_arbiter(canvas_id)
    presences = arbiter.get_active_presences(timeout_sec=timeout_sec)
    return {
        "canvas_id": canvas_id,
        "presences": presences,
        "active_count": len(presences),
    }


@router.post("/{canvas_id}/cursor/event")
async def record_cursor_event(canvas_id: str, req: CursorEventRequest):
    arbiter = _get_arbiter(canvas_id)
    res = arbiter.process_cursor_event(
        user_id=req.user_id,
        event_type=req.event_type,
        x=req.x,
        y=req.y,
        payload=req.payload,
    )
    return {"canvas_id": canvas_id, "success": True, "cursor_event": res}


# 3. AI Node Weaver & Semantic Groups Endpoints
@router.post("/{canvas_id}/ai/generate-subflow")
async def generate_ai_subflow(canvas_id: str, req: AIGenerateSubflowRequest):
    weaver = _get_weaver()
    result = weaver.synthesize_subflow(
        canvas_id=canvas_id,
        prompt=req.prompt,
        context_nodes=req.context_nodes,
        target_origin=req.target_origin,
        auto_group=req.auto_group,
    )
    if req.group_title and result.get("group"):
        result["group"]["title"] = req.group_title
    return result


@router.post("/{canvas_id}/ai/create-group")
async def create_semantic_group(canvas_id: str, req: SemanticGroupCreateRequest):
    weaver = _get_weaver()
    group = weaver.create_semantic_group(
        canvas_id=canvas_id,
        title=req.title,
        nodes=req.nodes,
        color=req.color,
        padding=req.padding,
    )
    return group


# 4. History Time-Travel Snapshots, Undo/Redo & Branching
@router.post("/{canvas_id}/history/snapshot")
async def create_history_snapshot(canvas_id: str, req: SnapshotCreateRequest):
    engine = _get_time_travel_engine(canvas_id)
    snapshot = engine.record_snapshot(
        author_id=req.author_id,
        state_data=req.state_data,
        snapshot_tag=req.snapshot_tag,
    )
    return snapshot


@router.get("/{canvas_id}/history/list")
async def list_history_snapshots(canvas_id: str):
    engine = _get_time_travel_engine(canvas_id)
    snapshots = engine.list_history()
    return {
        "canvas_id": canvas_id,
        "active_branch": engine.active_branch,
        "current_cursor": engine.current_cursor,
        "total_snapshots": len(snapshots),
        "snapshots": snapshots,
    }


@router.post("/{canvas_id}/history/undo")
async def undo_history_state(canvas_id: str):
    engine = _get_time_travel_engine(canvas_id)
    restored = engine.undo()
    if restored is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot undo: already at the earliest state.",
        )
    return {
        "canvas_id": canvas_id,
        "current_cursor": engine.current_cursor,
        "restored_state": restored,
    }


@router.post("/{canvas_id}/history/redo")
async def redo_history_state(canvas_id: str):
    engine = _get_time_travel_engine(canvas_id)
    restored = engine.redo()
    if restored is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot redo: already at the latest state.",
        )
    return {
        "canvas_id": canvas_id,
        "current_cursor": engine.current_cursor,
        "restored_state": restored,
    }


@router.post("/{canvas_id}/history/branch")
async def create_canvas_branch(canvas_id: str, req: BranchCreateRequest):
    engine = _get_time_travel_engine(canvas_id)
    res = engine.create_branch(
        branch_name=req.branch_name, from_snapshot_id=req.from_snapshot_id
    )
    return res


@router.post("/{canvas_id}/history/merge")
async def merge_canvas_branches(canvas_id: str, req: BranchMergeRequest):
    engine = _get_time_travel_engine(canvas_id)
    res = engine.merge_branch(
        source_branch=req.source_branch,
        target_branch=req.target_branch,
        strategy=req.strategy,
    )
    return res
