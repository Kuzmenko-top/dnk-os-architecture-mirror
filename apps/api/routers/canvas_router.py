# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_canvas_router"
# purpose: "Visual Canvas V2 REST router for Canvas, Node, Edge, Component CRUD, Generative UI synthesis, and Auto-Layout (DNK-CANVAS-002 Phase 4)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import uuid
import time
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from apps.api.schemas.workflow_dag_schemas import (
    WorkflowDAG,
    WorkflowExecuteRequest,
    WorkflowExecutionSummary
)
from apps.api.services.canvas_execution_engine import (
    get_canvas_execution_engine,
    CanvasExecutionEngine
)
from apps.api.services.canvas_reburn_templates import (
    get_template_registry,
    WorkflowTemplateMetadata
)
from apps.api.services.canvas_graph_engine import (
    CanvasGraphEngine,
    Point,
    Rect,
    CanvasSpatialMath
)
from apps.api.services.canvas_occ_sync import (
    CanvasOCCSyncManager,
    CanvasPatchOp,
    PatchOpType
)
from apps.api.services.canvas_generative_ui_engine import (
    CanvasGenerativeUIEngine,
    GeneratedComponent
)
from apps.api.services.canvas_component_sandbox import (
    CanvasComponentSandbox,
    SandboxSecurityConfig
)

router = APIRouter(prefix="/api/v1/canvas", tags=["Visual Canvas V2"])

# In-memory stores for active canvas sessions and engines
_canvas_store: Dict[str, Dict[str, Any]] = {}
_graph_engines: Dict[str, CanvasGraphEngine] = {}
_occ_managers: Dict[str, CanvasOCCSyncManager] = {}
_sandbox = CanvasComponentSandbox()
_components_catalog: Dict[str, Dict[str, Any]] = {}


# --- Pydantic Schemas ---

class CreateCanvasRequest(BaseModel):
    name: str = Field(..., description="Canvas name")
    workspace_id: str = Field("ws-alpha-001", description="Workspace ID")
    viewport_x: float = Field(0.0)
    viewport_y: float = Field(0.0)
    zoom: float = Field(1.0)
    snap_to_grid: bool = Field(True)
    grid_size: int = Field(20)
    background_color: str = Field("#0f172a")


class UpdateCanvasRequest(BaseModel):
    name: Optional[str] = None
    viewport_x: Optional[float] = None
    viewport_y: Optional[float] = None
    zoom: Optional[float] = None
    snap_to_grid: Optional[bool] = None
    grid_size: Optional[int] = None
    background_color: Optional[str] = None


class AddNodeRequest(BaseModel):
    id: Optional[str] = None
    node_type: str = Field("component")
    title: str = Field("Untitled Node")
    x: float = Field(0.0)
    y: float = Field(0.0)
    width: float = Field(240.0)
    height: float = Field(160.0)
    data: Dict[str, Any] = Field(default_factory=dict)
    style: Dict[str, Any] = Field(default_factory=dict)
    component_id: Optional[str] = None


class MoveNodeRequest(BaseModel):
    x: float
    y: float


class MoveBatchRequest(BaseModel):
    node_ids: List[str]
    delta_x: float
    delta_y: float


class AddEdgeRequest(BaseModel):
    id: Optional[str] = None
    source_node_id: str
    target_node_id: str
    source_port: str = "output"
    target_port: str = "input"
    edge_type: str = "smart_bezier"
    label: Optional[str] = None
    allow_cycles: bool = False


class GenUISynthesisRequest(BaseModel):
    prompt: str = Field(..., description="Natural language prompt for component")
    framework: str = Field("react", description="Target framework: react, vue, svelte")
    category: Optional[str] = None


class AutoLayoutRequest(BaseModel):
    layout_type: str = Field("horizontal_flow", description="horizontal_flow, vertical_stack, grid_2col")
    spacing_x: float = 240.0
    spacing_y: float = 160.0


class ValidatePropsRequest(BaseModel):
    props: Dict[str, Any]
    schema_definition: Dict[str, Any]


class SandboxEnvelopeRequest(BaseModel):
    component_code: str
    props: Dict[str, Any] = Field(default_factory=dict)
    framework: str = "react"
    instance_id: str = "inst_sandbox_001"


# --- Helper to get or init engine ---

def _get_engine(canvas_id: str) -> CanvasGraphEngine:
    if canvas_id not in _graph_engines:
        _graph_engines[canvas_id] = CanvasGraphEngine(canvas_id=canvas_id, grid_size=20, snap_to_grid=True)
    return _graph_engines[canvas_id]


def _get_occ(canvas_id: str) -> CanvasOCCSyncManager:
    if canvas_id not in _occ_managers:
        _occ_managers[canvas_id] = CanvasOCCSyncManager(canvas_id=canvas_id)
    return _occ_managers[canvas_id]


# --- REST Endpoints ---

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_canvas(req: CreateCanvasRequest):
    cid = f"canvas_{uuid.uuid4().hex[:8]}"
    canvas = {
        "id": cid,
        "name": req.name,
        "workspace_id": req.workspace_id,
        "viewport": {"x": req.viewport_x, "y": req.viewport_y, "zoom": req.zoom},
        "snap_to_grid": req.snap_to_grid,
        "grid_size": req.grid_size,
        "background_color": req.background_color,
        "version": 1,
        "created_at": time.time(),
        "updated_at": time.time()
    }
    _canvas_store[cid] = canvas
    _get_engine(cid)
    _get_occ(cid)
    return canvas


@router.get("")
async def list_canvases(workspace_id: str = Query("ws-alpha-001")):
    return [c for c in _canvas_store.values() if c.get("workspace_id") == workspace_id]


# --- Workflow DAG Execution Engine & Template Endpoints (DNK-CANVAS-001) ---

@router.get("/workflows/templates", response_model=List[WorkflowTemplateMetadata])
async def list_workflow_templates(category: Optional[str] = None):
    registry = get_template_registry()
    return registry.list_templates(category=category)


@router.get("/workflows/templates/{template_id}", response_model=WorkflowDAG)
async def get_workflow_template(template_id: str):
    registry = get_template_registry()
    template = registry.get_template(template_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_id} not found"
        )
    return template


@router.post("/workflows", response_model=WorkflowDAG, status_code=status.HTTP_201_CREATED)
async def create_or_save_workflow(dag: WorkflowDAG):
    """
    Saves and validates a complete Workflow DAG structure.
    """
    engine = get_canvas_execution_engine()
    return engine.save_workflow(dag)


@router.get("/workflows", response_model=List[WorkflowDAG])
async def list_workflows(workspace_id: Optional[str] = Query(None)):
    """
    Lists all saved workflows in the workspace.
    """
    engine = get_canvas_execution_engine()
    return engine.list_workflows(workspace_id=workspace_id)


@router.post("/workflows/validate")
async def validate_workflow_dag(dag: WorkflowDAG):
    """
    Validates a Workflow DAG without saving it.
    """
    return {
        "valid": True,
        "workflow_id": dag.id,
        "nodes_count": len(dag.nodes),
        "edges_count": len(dag.edges),
        "topological_order": dag.get_topological_order()
    }


@router.get("/workflows/{workflow_id}", response_model=WorkflowDAG)
async def get_workflow(workflow_id: str):
    """
    Retrieves a single Workflow DAG by ID.
    """
    engine = get_canvas_execution_engine()
    wf = engine.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return wf


@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecutionSummary)
async def execute_workflow_endpoint(workflow_id: str, req: WorkflowExecuteRequest):
    """
    Executes a Workflow DAG step-by-step and returns execution metrics.
    """
    engine = get_canvas_execution_engine()
    try:
        summary = await engine.execute_workflow(workflow_id, req)
        return summary
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")


@router.get("/workflows/{workflow_id}/status")
async def stream_workflow_status(workflow_id: str, execution_id: str = Query(...)):
    """
    Server-Sent Events (SSE) stream for real-time node execution status updates.
    """
    engine = get_canvas_execution_engine()
    return StreamingResponse(
        engine.subscribe_execution_stream(workflow_id, execution_id),
        media_type="text/event-stream"
    )


@router.delete("/workflows/{workflow_id}")
async def delete_workflow_endpoint(workflow_id: str):
    """
    Deletes a workflow by its ID.
    """
    engine = get_canvas_execution_engine()
    deleted = engine.delete_workflow(workflow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return {"status": "deleted", "workflow_id": workflow_id}


@router.get("/{canvas_id}")
async def get_canvas(canvas_id: str):
    canvas = _canvas_store.get(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")

    engine = _get_engine(canvas_id)
    occ = _get_occ(canvas_id)
    return {
        **canvas,
        "version": occ.current_version,
        "nodes": list(engine.nodes.values()),
        "edges": list(engine.edges.values())
    }


@router.put("/{canvas_id}")
async def update_canvas_metadata(canvas_id: str, req: UpdateCanvasRequest):
    canvas = _canvas_store.get(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")

    if req.name is not None:
        canvas["name"] = req.name
    if req.viewport_x is not None:
        canvas["viewport"]["x"] = req.viewport_x
    if req.viewport_y is not None:
        canvas["viewport"]["y"] = req.viewport_y
    if req.zoom is not None:
        canvas["viewport"]["zoom"] = req.zoom
    if req.snap_to_grid is not None:
        canvas["snap_to_grid"] = req.snap_to_grid
    if req.grid_size is not None:
        canvas["grid_size"] = req.grid_size
    if req.background_color is not None:
        canvas["background_color"] = req.background_color

    canvas["updated_at"] = time.time()
    return canvas


@router.delete("/{canvas_id}")
async def delete_canvas(canvas_id: str):
    if canvas_id not in _canvas_store:
        raise HTTPException(status_code=404, detail="Canvas not found")

    del _canvas_store[canvas_id]
    _graph_engines.pop(canvas_id, None)
    _occ_managers.pop(canvas_id, None)
    return {"status": "deleted", "canvas_id": canvas_id}


# --- Nodes Endpoints ---

@router.post("/{canvas_id}/nodes", status_code=status.HTTP_201_CREATED)
async def add_canvas_node(canvas_id: str, req: AddNodeRequest):
    if canvas_id not in _canvas_store:
        raise HTTPException(status_code=404, detail="Canvas not found")

    engine = _get_engine(canvas_id)
    occ = _get_occ(canvas_id)

    node_id = req.id or f"node_{uuid.uuid4().hex[:8]}"
    added = engine.add_node(
        node_id=node_id,
        node_type=req.node_type,
        title=req.title,
        pos_x=req.x,
        pos_y=req.y,
        width=req.width,
        height=req.height,
        data=req.data,
        style=req.style,
        component_id=req.component_id
    )

    # Sync with OCC
    patch = CanvasPatchOp(
        op_type=PatchOpType.NODE_ADD,
        client_id="rest_api",
        base_version=occ.current_version,
        payload=added
    )
    occ.apply_patch(patch)

    return added


@router.put("/{canvas_id}/nodes/{node_id}/move")
async def move_canvas_node(canvas_id: str, node_id: str, req: MoveNodeRequest):
    engine = _get_engine(canvas_id)
    occ = _get_occ(canvas_id)

    moved = engine.move_node(node_id, req.x, req.y)
    if not moved:
        raise HTTPException(status_code=404, detail="Node not found")

    patch = CanvasPatchOp(
        op_type=PatchOpType.NODE_MOVE,
        client_id="rest_api",
        base_version=occ.current_version,
        payload={"node_id": node_id, "x": moved["position"]["x"], "y": moved["position"]["y"]}
    )
    occ.apply_patch(patch)

    return moved


@router.post("/{canvas_id}/nodes/move-batch")
async def move_nodes_batch(canvas_id: str, req: MoveBatchRequest):
    engine = _get_engine(canvas_id)
    moved_nodes = engine.move_nodes_batch(req.node_ids, req.delta_x, req.delta_y)
    return moved_nodes


@router.delete("/{canvas_id}/nodes/{node_id}")
async def delete_canvas_node(canvas_id: str, node_id: str):
    engine = _get_engine(canvas_id)
    occ = _get_occ(canvas_id)

    ok = engine.remove_node(node_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Node not found")

    patch = CanvasPatchOp(
        op_type=PatchOpType.NODE_DELETE,
        client_id="rest_api",
        base_version=occ.current_version,
        payload={"node_id": node_id}
    )
    occ.apply_patch(patch)

    return {"status": "deleted", "node_id": node_id}


# --- Edges Endpoints ---

@router.post("/{canvas_id}/edges", status_code=status.HTTP_201_CREATED)
async def add_canvas_edge(canvas_id: str, req: AddEdgeRequest):
    engine = _get_engine(canvas_id)
    occ = _get_occ(canvas_id)

    edge_id = req.id or f"edge_{uuid.uuid4().hex[:8]}"
    edge, err = engine.add_edge(
        edge_id=edge_id,
        source_node_id=req.source_node_id,
        target_node_id=req.target_node_id,
        source_port=req.source_port,
        target_port=req.target_port,
        edge_type=req.edge_type,
        label=req.label,
        allow_cycles=req.allow_cycles
    )
    if not edge:
        raise HTTPException(status_code=400, detail=err or "Failed to add edge")

    patch = CanvasPatchOp(
        op_type=PatchOpType.EDGE_ADD,
        client_id="rest_api",
        base_version=occ.current_version,
        payload=edge
    )
    occ.apply_patch(patch)

    return edge


@router.delete("/{canvas_id}/edges/{edge_id}")
async def delete_canvas_edge(canvas_id: str, edge_id: str):
    engine = _get_engine(canvas_id)
    occ = _get_occ(canvas_id)

    ok = engine.remove_edge(edge_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Edge not found")

    patch = CanvasPatchOp(
        op_type=PatchOpType.EDGE_DELETE,
        client_id="rest_api",
        base_version=occ.current_version,
        payload={"edge_id": edge_id}
    )
    occ.apply_patch(patch)

    return {"status": "deleted", "edge_id": edge_id}


# --- Generative UI & Layout Endpoints ---

@router.post("/generate-ui")
async def generate_ui_component(req: GenUISynthesisRequest):
    comp = CanvasGenerativeUIEngine.synthesize_component_from_prompt(
        prompt=req.prompt,
        framework=req.framework,
        category=req.category
    )
    comp_dict = comp.to_dict()
    _components_catalog[comp.component_id] = comp_dict
    return comp_dict


@router.post("/validate-props")
async def validate_component_props(req: ValidatePropsRequest):
    valid, errors = CanvasGenerativeUIEngine.validate_props(req.props, req.schema_definition)
    return {"valid": valid, "errors": errors}


@router.post("/{canvas_id}/auto-layout")
async def apply_auto_layout(canvas_id: str, req: AutoLayoutRequest):
    engine = _get_engine(canvas_id)
    nodes_raw = list(engine.nodes.values())

    positioned = CanvasGenerativeUIEngine.suggest_auto_layout(
        nodes_raw,
        layout_type=req.layout_type,
        spacing_x=req.spacing_x,
        spacing_y=req.spacing_y
    )

    # Apply back to graph engine
    for p in positioned:
        engine.move_node(p["id"], p["position"]["x"], p["position"]["y"])

    return positioned


@router.post("/{canvas_id}/smart-connectors")
async def infer_smart_connectors_endpoint(canvas_id: str):
    engine = _get_engine(canvas_id)
    nodes_raw = list(engine.nodes.values())
    inferred_edges = CanvasGenerativeUIEngine.infer_smart_connectors(nodes_raw)

    added_edges = []
    for e in inferred_edges:
        edge, _ = engine.add_edge(
            edge_id=e["id"],
            source_node_id=e["source_node_id"],
            target_node_id=e["target_node_id"],
            source_port=e["source_port"],
            target_port=e["target_port"],
            edge_type=e["edge_type"],
            label=e.get("label"),
            allow_cycles=True
        )
        if edge:
            added_edges.append(edge)

    return added_edges


# --- Sandbox Endpoints ---

@router.post("/sandbox/envelope")
async def generate_sandbox_envelope(req: SandboxEnvelopeRequest):
    envelope = _sandbox.generate_iframe_envelope(
        component_code=req.component_code,
        props=req.props,
        framework=req.framework,
        instance_id=req.instance_id
    )
    return {"envelope_html": envelope}


