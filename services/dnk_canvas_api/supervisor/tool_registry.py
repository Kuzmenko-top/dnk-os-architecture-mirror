# --- DNK-MRH-HEADER ---
# mrh_id: "supervisor/tool_registry.py"
# purpose: "Implement Model Tool Registry with strict schemas, risk levels, and approval policies."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ToolContract(BaseModel):
    name: str
    risk_level: str  # L0, L1, L2, L3, L4
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    requires_approval: bool = False

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolContract] = {}
        self._register_default_tools()

    def register(self, tool: ToolContract):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolContract]:
        return self._tools.get(name)

    def _register_default_tools(self):
        # 1. design.read_project_context
        self.register(ToolContract(
            name="design.read_project_context",
            risk_level="L0",
            description="Read non-sensitive project metadata and constraints.",
            input_schema={"type": "object", "properties": {"project_id": {"type": "string"}}, "required": ["project_id"]},
            output_schema={"type": "object", "properties": {"project_metadata": {"type": "object"}}},
            requires_approval=False
        ))

        # 2. design.read_canvas_snapshot
        self.register(ToolContract(
            name="design.read_canvas_snapshot",
            risk_level="L0",
            description="Fetch the last saved Excalidraw snapshot of the active canvas.",
            input_schema={"type": "object", "properties": {"canvas_id": {"type": "string"}}, "required": ["canvas_id"]},
            output_schema={"type": "object", "properties": {"snapshot": {"type": "object"}}},
            requires_approval=False
        ))

        # 3. design.read_design_system
        self.register(ToolContract(
            name="design.read_design_system",
            risk_level="L0",
            description="Retrieve authorized design system parameters (themes, grid metrics, standard palette).",
            input_schema={"type": "object", "properties": {"design_system_id": {"type": "string"}}, "required": ["design_system_id"]},
            output_schema={"type": "object", "properties": {"design_system": {"type": "object"}}},
            requires_approval=False
        ))

        # 4. design.generate_scene
        self.register(ToolContract(
            name="design.generate_scene",
            risk_level="L1",
            description="Generate high-fidelity layout blocks of elements from structured specifications.",
            input_schema={"type": "object", "properties": {"spec": {"type": "object"}}, "required": ["spec"]},
            output_schema={"type": "object", "properties": {"elements": {"type": "array"}}},
            requires_approval=False
        ))

        # 5. design.validate_scene
        self.register(ToolContract(
            name="design.validate_scene",
            risk_level="L1",
            description="Audit structured workspace design intent against boundary, dimension, and injection rules.",
            input_schema={"type": "object", "properties": {"spec": {"type": "object"}}, "required": ["spec"]},
            output_schema={"type": "object", "properties": {"passed": {"type": "boolean"}, "errors": {"type": "array"}}},
            requires_approval=False
        ))

        # 6. design.create_artifact
        self.register(ToolContract(
            name="design.create_artifact",
            risk_level="L1",
            description="Persist curated briefs, critique documents, or compiled designs in the database.",
            input_schema={"type": "object", "properties": {"run_id": {"type": "string"}, "artifact_type": {"type": "string"}, "content": {"type": "string"}}, "required": ["run_id", "artifact_type", "content"]},
            output_schema={"type": "object", "properties": {"artifact_id": {"type": "string"}}},
            requires_approval=False
        ))

        # 7. design.create_canvas_revision
        self.register(ToolContract(
            name="design.create_canvas_revision",
            risk_level="L1",
            description="Commit a new compiled Excalidraw revision structure to the canvas document history.",
            input_schema={"type": "object", "properties": {"canvas_id": {"type": "string"}, "elements": {"type": "array"}}, "required": ["canvas_id", "elements"]},
            output_schema={"type": "object", "properties": {"revision_id": {"type": "string"}, "version": {"type": "integer"}}},
            requires_approval=False
        ))

# Global tool registry instance
model_tools = ToolRegistry()
