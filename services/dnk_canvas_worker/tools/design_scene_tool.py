# --- DNK-MRH-HEADER ---
# mrh_id: "tools/design_scene_tool.py"
# purpose: "Implement deterministic design tool to generate workspace scene elements."
# canonical_source: true
# status: "Active"
# version: "1.0.1"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, List

def generate_workspace_scene(context: Dict[str, Any]) -> Dict[str, Any]:
    prompt = context.get("prompt", "Створи головний екран кабінету DNK OS")
    design_system_id = context.get("design_system_id", "dnk-default")

    elements = [
        {
            "id": "header_1",
            "type": "rectangle",
            "x": 100,
            "y": 50,
            "width": 800,
            "height": 60,
            "backgroundColor": "#1e1e2e",
            "strokeColor": "#313244",
            "fillStyle": "solid",
            "label": f"Header - Prompt: {prompt[:30]}"
        },
        {
            "id": "sidebar_1",
            "type": "rectangle",
            "x": 100,
            "y": 120,
            "width": 200,
            "height": 500,
            "backgroundColor": "#181825",
            "strokeColor": "#313244",
            "fillStyle": "solid",
            "label": "Sidebar - DNK OS Nav"
        },
        {
            "id": "main_workspace_1",
            "type": "rectangle",
            "x": 310,
            "y": 120,
            "width": 590,
            "height": 400,
            "backgroundColor": "#1e1e2e",
            "strokeColor": "#45475a",
            "fillStyle": "solid",
            "label": f"Main Workspace ({design_system_id})"
        },
        {
            "id": "right_panel_1",
            "type": "rectangle",
            "x": 910,
            "y": 120,
            "width": 190,
            "height": 500,
            "backgroundColor": "#181825",
            "strokeColor": "#313244",
            "fillStyle": "solid",
            "label": "Right Context Panel"
        },
        {
            "id": "prompt_dock_1",
            "type": "rectangle",
            "x": 310,
            "y": 530,
            "width": 590,
            "height": 90,
            "backgroundColor": "#11111b",
            "strokeColor": "#f38ba8",
            "fillStyle": "solid",
            "label": "Prompt Dock"
        },
        {
            "id": "activity_area_1",
            "type": "rectangle",
            "x": 310,
            "y": 450,
            "width": 590,
            "height": 70,
            "backgroundColor": "#181825",
            "strokeColor": "#a6adc8",
            "fillStyle": "solid",
            "label": "Agent Activity Area"
        },
        {
            "id": "text_gen_1",
            "type": "text",
            "x": 380,
            "y": 220,
            "text": "Orchestrated Workspace Sketch",
            "fontSize": 14,
            "color": "#ffffff",
        }
    ]

    return {
        "elements": elements
    }
