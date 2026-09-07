# --- DNK-MRH-HEADER ---
# mrh_id: "core/bricks/brick_03_spatial_canvas/contracts/schemas.py"
# purpose: "Pydantic contract schemas for Brick 03: Spatial Canvas V3 Engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class CanvasNode(BaseModel):
    id: str
    type: str
    position: Dict[str, float]
    data: Dict[str, Any] = Field(default_factory=dict)


class CanvasEdge(BaseModel):
    id: str
    source: str
    target: str
    type: Optional[str] = "default"


class CanvasGraphState(BaseModel):
    canvas_id: str
    nodes: List[CanvasNode] = Field(default_factory=list)
    edges: List[CanvasEdge] = Field(default_factory=list)
    version: int = 1
