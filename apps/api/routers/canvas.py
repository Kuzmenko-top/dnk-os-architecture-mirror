# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_canvas"
# purpose: "Canvas router endpoints for CRUD operations"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from uuid import uuid4

from apps.api.database import get_canvas, set_canvas

router = APIRouter()

class CanvasCreate(BaseModel):
    name: str
    elements: Optional[Dict[str, Any]] = Field(default_factory=dict)
    app_state: Optional[Dict[str, Any]] = Field(default_factory=dict)

class CanvasUpdate(BaseModel):
    name: Optional[str] = None
    elements: Optional[Dict[str, Any]] = None
    app_state: Optional[Dict[str, Any]] = None

@router.post("/canvas", status_code=201)
async def create_canvas(payload: CanvasCreate):
    canvas_id = str(uuid4())
    canvas = {
        "id": canvas_id,
        "name": payload.name,
        "elements": payload.elements or {},
        "app_state": payload.app_state or {}
    }
    set_canvas(canvas_id, canvas)
    return canvas

@router.get("/canvas/{canvas_id}")
async def fetch_canvas(canvas_id: str):
    canvas = get_canvas(canvas_id)
    if not canvas:
        if canvas_id == "default-canvas-id":
            canvas = {
                "id": "default-canvas-id",
                "name": "First E2E Test Workflow: Event Trigger -> A2A Agent -> Batch Task",
                "elements": {
                    "nodes": [
                        {"id": "node-1", "name": "Event Trigger (orders.created)", "type": "TriggerNode", "state": "Active", "config": {"topic": "orders.created", "source": "dnk_stream"}, "x": 100, "y": 150},
                        {"id": "node-2", "name": "A2A Agent (order-processor)", "type": "AgentNode", "state": "Queued", "config": {"agent": "order-processor", "role": "orchestrator", "timeout_s": 60}, "x": 350, "y": 150},
                        {"id": "node-3", "name": "Batch Task (fulfill_and_notify)", "type": "BatchTaskNode", "state": "Queued", "config": {"batch_size": 50, "action": "fulfill_order"}, "x": 600, "y": 150}
                    ],
                    "edges": [
                        {"id": "edge-1-2", "source": "node-1", "target": "node-2"},
                        {"id": "edge-2-3", "source": "node-2", "target": "node-3"}
                    ]
                },
                "app_state": {"status": "ready", "version": "1.0.0"}
            }
            set_canvas(canvas_id, canvas)
            return canvas
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas

@router.put("/canvas/{canvas_id}")
async def update_canvas(canvas_id: str, payload: CanvasUpdate):
    canvas = get_canvas(canvas_id)
    if not canvas:
        canvas = {
            "id": canvas_id,
            "name": payload.name or "My Canvas",
            "elements": payload.elements or {},
            "app_state": payload.app_state or {}
        }
    else:
        if payload.name is not None:
            canvas["name"] = payload.name
        if payload.elements is not None:
            canvas["elements"] = payload.elements
        if payload.app_state is not None:
            canvas["app_state"] = payload.app_state
        
    set_canvas(canvas_id, canvas)
    return canvas
