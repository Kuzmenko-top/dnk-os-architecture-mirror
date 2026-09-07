# --- DNK-MRH-HEADER ---
# mrh_id: "core/bricks/__init__.py"
# purpose: "Brick Registry Module Initialization."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Antigravity Orchestrator"
# --- END DNK-MRH-HEADER ---

from .registry import DNKBrickRegistry, BrickManifest, BrickDependencies, BrickContracts, BrickQualityGate
from .blueprint import DNKAppBlueprint, BrickConfig, CanvasNodeSpec, CanvasEdgeSpec, CanvasInitialState

__all__ = [
    "DNKBrickRegistry",
    "BrickManifest",
    "BrickDependencies",
    "BrickContracts",
    "BrickQualityGate",
    "DNKAppBlueprint",
    "BrickConfig",
    "CanvasNodeSpec",
    "CanvasEdgeSpec",
    "CanvasInitialState",
]
