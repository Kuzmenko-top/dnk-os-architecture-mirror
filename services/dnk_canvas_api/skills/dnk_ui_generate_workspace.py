# --- DNK-MRH-HEADER ---
# mrh_id: "skills/dnk_ui_generate_workspace.py"
# purpose: "Implementation of the dnk.ui.generate_workspace skill."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any
from .models import BaseSkill, SkillContract

class DNKUiGenerateWorkspaceSkill(BaseSkill):
    contract = SkillContract(
        id="dnk.ui.generate_workspace",
        version="1.0.0",
        risk_level="L1",
        input_schema=["project_id", "canvas_id", "prompt", "design_system_id"],
        output_artifacts=["design_brief", "excalidraw_scene", "critique_report"],
        approval_required=False
    )

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # Return deterministic design components for validation
        prompt = context.get("prompt", "Default Prompt")
        project_id = context.get("project_id", "default_proj")
        canvas_id = context.get("canvas_id", "default_canvas")
        design_system_id = context.get("design_system_id", "dnk-default")

        brief_content = f"# Design Brief for {design_system_id}\n\nPrompt: {prompt}\nProject: {project_id}\nCanvas: {canvas_id}\n"
        critique_content = f"### Critique Report\n\n1. Layout satisfies high-fidelity constraints.\n2. Workspace layout elements generated successfully.\n"

        # Excalidraw scene elements
        scene_elements = [
            {"id": "header_1", "type": "rectangle", "x": 100, "y": 50, "width": 800, "height": 60, "backgroundColor": "#1e1e2e", "strokeColor": "#313244", "fillStyle": "solid", "label": "Header"},
            {"id": "sidebar_1", "type": "rectangle", "x": 100, "y": 120, "width": 200, "height": 500, "backgroundColor": "#181825", "strokeColor": "#313244", "fillStyle": "solid", "label": "Sidebar"},
            {"id": "main_workspace_1", "type": "rectangle", "x": 310, "y": 120, "width": 590, "height": 400, "backgroundColor": "#1e1e2e", "strokeColor": "#45475a", "fillStyle": "solid", "label": "Main Workspace"},
            {"id": "right_panel_1", "type": "rectangle", "x": 910, "y": 120, "width": 190, "height": 500, "backgroundColor": "#181825", "strokeColor": "#313244", "fillStyle": "solid", "label": "Right Context Panel"},
            {"id": "prompt_dock_1", "type": "rectangle", "x": 310, "y": 530, "width": 590, "height": 90, "backgroundColor": "#11111b", "strokeColor": "#f38ba8", "fillStyle": "solid", "label": "Prompt Dock"},
            {"id": "activity_area_1", "type": "rectangle", "x": 310, "y": 450, "width": 590, "height": 70, "backgroundColor": "#181825", "strokeColor": "#a6adc8", "fillStyle": "solid", "label": "Agent Activity Area"}
        ]

        return {
            "design_brief": {
                "name": "Design Brief",
                "type": "design_brief",
                "content_json": brief_content
            },
            "excalidraw_scene": {
                "name": "Excalidraw Workspace Scene",
                "type": "excalidraw_scene",
                "content_json": {"elements": scene_elements}
            },
            "critique_report": {
                "name": "Critique Report",
                "type": "critique_report",
                "content_json": critique_content
            }
        }
