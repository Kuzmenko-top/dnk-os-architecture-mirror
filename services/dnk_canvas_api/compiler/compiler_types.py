# --- DNK-MRH-HEADER ---
# mrh_id: "compiler/compiler_types.py"
# purpose: "Type definitions for DesignIntent, CompiledCanvas, and supported allowlists."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Supported allowlists
SUPPORTED_REGIONS = {
    "sidebar",
    "header",
    "main",
    "context_panel",
    "prompt_dock",
    "activity_panel"
}

SUPPORTED_COMPONENTS = {
    "header",
    "navigation",
    "card",
    "button",
    "input",
    "list",
    "table",
    "panel",
    "status_badge",
    "prompt_dock",
    "activity_log"
}

SUPPORTED_INTERACTIONS = {
    "click",
    "submit",
    "navigate",
    "open_panel",
    "create_task"
}

class DesignRegion(BaseModel):
    id: str
    width: float = 0
    height: float = 0
    x: float = 0
    y: float = 0

class DesignComponent(BaseModel):
    id: str
    type: str
    region_id: str
    title: Optional[str] = ""
    properties: Dict[str, Any] = Field(default_factory=dict)

class DesignInteraction(BaseModel):
    id: str
    type: str
    source_component_id: str
    target_component_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)

class DesignIntent(BaseModel):
    title: str
    layout_strategy: str
    regions: List[DesignRegion]
    components: List[DesignComponent]
    interactions: List[DesignInteraction]
    accessibility_notes: List[str]

class CompiledCanvas(BaseModel):
    elements: List[Dict[str, Any]]
    app_state: Dict[str, Any]
    files: Dict[str, Any]
    compiler_version: str
    source_artifact_id: str
    source_hash: str
