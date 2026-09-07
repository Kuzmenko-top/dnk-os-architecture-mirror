# --- DNK-MRH-HEADER ---
# mrh_id: "core/bricks/blueprint.py"
# purpose: "DNK Blueprint DSL (app.blueprint.yaml) parser, validator, and canvas graph state generator."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
from pydantic import BaseModel, Field


class BrickConfig(BaseModel):
    brick_id: str
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)
    routes_prefix: Optional[str] = None
    custom_env: Dict[str, str] = Field(default_factory=dict)


class CanvasNodeSpec(BaseModel):
    id: str
    type: str
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    data: Dict[str, Any] = Field(default_factory=dict)


class CanvasEdgeSpec(BaseModel):
    id: str
    source: str
    target: str
    type: Optional[str] = "default"
    animated: Optional[bool] = False
    data: Dict[str, Any] = Field(default_factory=dict)


class CanvasInitialState(BaseModel):
    viewport: Dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0, "zoom": 1.0})
    nodes: List[CanvasNodeSpec] = Field(default_factory=list)
    edges: List[CanvasEdgeSpec] = Field(default_factory=list)


class DNKAppBlueprint(BaseModel):
    """
    Declarative DSL for assembling modular DNK OS AI Applications.
    Specifies selected bricks, their runtime configurations, environment variables,
    and the initial visual state of the Spatial Canvas.
    """
    id: str
    name: str
    version: str = "1.0.0"
    mrh_id: Optional[str] = None
    description: str = ""
    target_profile: str = "production"
    bricks: List[BrickConfig] = Field(default_factory=list)
    canvas: CanvasInitialState = Field(default_factory=CanvasInitialState)
    environment: Dict[str, str] = Field(default_factory=dict)

    @classmethod
    def from_yaml(cls, source: Union[str, Path]) -> "DNKAppBlueprint":
        """
        Parses a blueprint from either a YAML string or a file path.
        """
        if isinstance(source, Path) or (isinstance(source, str) and (source.endswith(".yaml") or source.endswith(".yml") or os.path.exists(source))):
            file_path = Path(source)
            if not file_path.exists():
                raise FileNotFoundError(f"Blueprint file not found at: {file_path}")
            content = file_path.read_text(encoding="utf-8")
        else:
            content = source

        raw_data = yaml.safe_load(content)
        if not isinstance(raw_data, dict):
            raise ValueError("Invalid YAML: Blueprint root must be a dictionary")
        return cls(**raw_data)

    def to_yaml(self, destination: Optional[Union[str, Path]] = None) -> str:
        """
        Serializes the blueprint to a YAML string and optionally writes it to disk.
        """
        data = self.model_dump(exclude_none=True)
        yaml_str = yaml.safe_dump(data, sort_keys=False, allow_unicode=True)
        if destination:
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(yaml_str, encoding="utf-8")
        return yaml_str

    def get_active_brick_ids(self) -> List[str]:
        """
        Returns a list of IDs for bricks explicitly marked enabled.
        """
        return [b.brick_id for b in self.bricks if b.enabled]

    def validate_against_registry(self, registry: Any) -> List[str]:
        """
        Validates that all specified bricks exist in the registry and computes
        the resolved topological dependency list.
        """
        active_bricks = self.get_active_brick_ids()
        if not active_bricks:
            raise ValueError(f"Blueprint '{self.id}' contains no active/enabled bricks.")

        # Ensure all referenced bricks exist
        for b_id in active_bricks:
            if not registry.get_brick(b_id):
                raise KeyError(f"Brick '{b_id}' in blueprint '{self.id}' is not registered.")

        # Resolve DAG
        return registry.resolve_dependencies(active_bricks)

    def to_canvas_graph_state(self) -> Dict[str, Any]:
        """
        Converts the canvas configuration into the standard React Flow / Canvas V3 JSON structure.
        """
        return {
            "canvas_id": f"canvas_{self.id}",
            "viewport": self.canvas.viewport,
            "nodes": [node.model_dump() for node in self.canvas.nodes],
            "edges": [edge.model_dump() for edge in self.canvas.edges],
            "version": 1,
        }
