# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/whiteboard_router.py"
# purpose: "FastAPI REST API router for SOTA Whiteboard scene persistence and OCC synchronization."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from core.canvas.whiteboard_service import (
    whiteboard_service,
    WhiteboardScene,
    WhiteboardElement,
)

router = APIRouter(prefix="/api/v1/whiteboard", tags=["Whiteboard SOTA"])


@router.get("/scenes/{scene_id}", response_model=WhiteboardScene)
async def get_whiteboard_scene(scene_id: str, workspace_id: str = "ws-alpha-001"):
    try:
        return whiteboard_service.get_scene(scene_id, workspace_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/scenes", response_model=WhiteboardScene)
async def save_whiteboard_scene(scene: WhiteboardScene):
    try:
        return whiteboard_service.save_scene(scene)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
