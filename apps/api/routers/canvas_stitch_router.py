# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/canvas_stitch_router.py"
# purpose: "FastAPI REST & WebSocket Router for Google Stitch Open Canvas, Screen DAG, DESIGN.md & Swarm Code Generation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import asyncio
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from core.adapters.dnk_stitch_adapter import (
    DNKStitchAdapter,
    ScreenNode,
    ScreenEdge,
    DesignSystemTokenSpec,
    CanvasProjectGraph,
    parse_design_md,
    validate_wcag_contrast,
    export_to_tailwind_v4,
    export_to_dtcg_json
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3/stitch", tags=["Google Stitch Open Canvas Engine"])

# Global shared adapter singleton
_adapter = DNKStitchAdapter()

class GenerateScreenRequest(BaseModel):
    project_id: str = "proj-main-001"
    prompt: str
    parent_screen_id: Optional[str] = None
    device_type: str = "mobile"
    template_vibe: Optional[str] = None

class LinkScreensRequest(BaseModel):
    project_id: str = "proj-main-001"
    source_screen_id: str
    target_screen_id: str
    trigger_selector: str = "#btn-cta"
    label: Optional[str] = "onClick"

class ParseDesignMdRequest(BaseModel):
    content: str

class ExportShopifyRequest(BaseModel):
    screen_id: str
    project_id: str = "proj-main-001"
    section_name: str = "stitch_hero_section"


class StitchWebSocketManager:
    """Manages active WebSocket connections for Stitch Open Canvas real-time collaboration & streaming."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, canvas_id: str = "default"):
        await websocket.accept()
        if canvas_id not in self.active_connections:
            self.active_connections[canvas_id] = []
        self.active_connections[canvas_id].append(websocket)
        await websocket.send_text(json.dumps({
            "type": "CONNECTED",
            "canvas_id": canvas_id,
            "status": "active",
            "message": "Stitch Real-Time Canvas WebSocket connected successfully"
        }))

    def disconnect(self, websocket: WebSocket, canvas_id: str = "default"):
        if canvas_id in self.active_connections and websocket in self.active_connections[canvas_id]:
            self.active_connections[canvas_id].remove(websocket)

    async def broadcast(self, message: Dict[str, Any], canvas_id: str = "default"):
        if canvas_id in self.active_connections:
            payload = json.dumps(message)
            dead_sockets = []
            for ws in self.active_connections[canvas_id]:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead_sockets.append(ws)
            for ws in dead_sockets:
                self.disconnect(ws, canvas_id)


_ws_manager = StitchWebSocketManager()


@router.websocket("/ws")
@router.websocket("/ws/{canvas_id}")
async def stitch_websocket_endpoint(websocket: WebSocket, canvas_id: str = "default"):
    """WebSocket endpoint for real-time Stitch DAG mutations, play mode dispatch, and Gemini streaming."""
    await _ws_manager.connect(websocket, canvas_id)
    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
            except Exception:
                continue

            event_type = data.get("type") or data.get("event")

            if event_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong", "timestamp": data.get("timestamp")}))
                continue

            # Real-time Screen generation request over WebSocket with multi-modal progress streaming
            if event_type == "generate_screen":
                prompt = data.get("prompt", "New Screen")
                project_id = data.get("project_id", "proj-main-001")
                parent_screen_id = data.get("parent_screen_id")
                device_type = data.get("device_type", "mobile")

                # Stream multi-step progress
                await websocket.send_text(json.dumps({
                    "type": "generation_progress",
                    "step": "analyzing_prompt",
                    "progress": 25,
                    "message": f"Analyzing UI intent: {prompt[:40]}..."
                }))
                await asyncio.sleep(0.05)

                await websocket.send_text(json.dumps({
                    "type": "generation_progress",
                    "step": "applying_tokens",
                    "progress": 60,
                    "message": "Harmonizing tokens with DESIGN.md..."
                }))
                await asyncio.sleep(0.05)

                screen = await _adapter.generate_screen(
                    project_id=project_id,
                    prompt=prompt,
                    parent_screen_id=parent_screen_id,
                    device_type=device_type
                )

                response_event = {
                    "type": "generation_completed",
                    "screen": screen.model_dump(),
                    "project_id": project_id
                }
                await _ws_manager.broadcast(response_event, canvas_id)

            # Broadcast DAG mutations across all connected canvas clients
            elif event_type in ["screen_added", "edge_linked", "token_updated", "timeline_keyframe_added", "prototype_navigated"]:
                await _ws_manager.broadcast(data, canvas_id)

            else:
                # Echo / broadcast generic payload
                await _ws_manager.broadcast({"type": "event_received", "payload": data}, canvas_id)

    except WebSocketDisconnect:
        _ws_manager.disconnect(websocket, canvas_id)
    except Exception as e:
        logger.warning(f"WebSocket error on canvas {canvas_id}: {e}")
        _ws_manager.disconnect(websocket, canvas_id)


@router.get("/projects")
async def list_projects():
    """Lists all canvas projects and their screen counts."""
    return await _adapter.list_projects()

@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Retrieves full Canvas Project Graph (Screens, Edges, Design System)."""
    proj = await _adapter.get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

@router.post("/screens/generate", response_model=ScreenNode)
async def generate_screen(req: GenerateScreenRequest):
    """Generates a new UI Screen Node and dynamically binds it to parent in the DAG."""
    try:
        screen = await _adapter.generate_screen(
            project_id=req.project_id,
            prompt=req.prompt,
            parent_screen_id=req.parent_screen_id,
            device_type=req.device_type
        )
        return screen
    except Exception as e:
        logger.error(f"Error generating screen: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/screens/link", response_model=ScreenEdge)
async def link_screens(req: LinkScreensRequest):
    """Creates an interactive transition link (Stitch edge) between two screens."""
    proj = await _adapter.get_project(req.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    
    edge_id = f"edge-{len(proj.edges) + 1:03d}"
    edge = ScreenEdge(
        id=edge_id,
        source_screen_id=req.source_screen_id,
        target_screen_id=req.target_screen_id,
        trigger_element_selector=req.trigger_selector,
        label=req.label
    )
    proj.edges.append(edge)
    return edge

@router.post("/design_system/parse")
async def parse_design_system_md(req: ParseDesignMdRequest):
    """Parses raw DESIGN.md content (YAML frontmatter + Markdown) into structured token specs."""
    try:
        parsed = parse_design_md(req.content)
        frontmatter = parsed.get("frontmatter", {})
        wcag_audit = validate_wcag_contrast(frontmatter)
        tailwind_css = export_to_tailwind_v4(frontmatter)
        dtcg_json = export_to_dtcg_json(frontmatter)
        return {
            "tokens": frontmatter,
            "markdown_rationale": parsed.get("markdown", ""),
            "wcag_linter": wcag_audit,
            "tailwind_v4_css": tailwind_css,
            "dtcg_json": dtcg_json
        }
    except Exception as e:
        logger.error(f"Error parsing DESIGN.md: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/export/shopify")
async def export_to_shopify_liquid(req: ExportShopifyRequest):
    """Transpiles a canvas ScreenNode into a native Shopify Liquid section."""
    proj = await _adapter.get_project(req.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    
    screen = next((s for s in proj.screens if s.id == req.screen_id), None)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    liquid_content = f"""{{% comment %}}
  Section: {req.section_name}
  Generated via DNK OS Google Stitch Engine
  Source Screen: {screen.title} ({screen.id})
{{% endcomment %}}

<section id="{req.section_name}-{{{{ section.id }}}}" class="dnk-stitch-section w-full max-w-7xl mx-auto px-4 py-12">
  <div class="stitch-container {screen.device_type}-frame">
    {screen.html_content}
  </div>
</section>

{{% schema %}}
{{
  "name": "{screen.title}",
  "tag": "section",
  "class": "section-stitch-generated",
  "settings": [
    {{
      "type": "text",
      "id": "heading",
      "label": "Heading",
      "default": "{screen.title}"
    }}
  ],
  "presets": [
    {{
      "name": "{screen.title}"
    }}
  ]
}}
{{% endschema %}}
"""
    return {
        "screen_id": screen.id,
        "section_name": req.section_name,
        "liquid_code": liquid_content
    }
