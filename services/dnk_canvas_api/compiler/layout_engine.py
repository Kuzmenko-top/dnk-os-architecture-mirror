# --- DNK-MRH-HEADER ---
# mrh_id: "compiler/layout_engine.py"
# purpose: "Implement a deterministic layout engine that calculates absolute x, y, width, height for regions and components."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, List
from .compiler_types import DesignIntent, DesignRegion, DesignComponent

class LayoutEngine:
    @classmethod
    def calculate_layout(
        cls, 
        intent: DesignIntent, 
        canvas_width: float = 1920.0, 
        canvas_height: float = 1080.0
    ) -> Dict[str, Any]:
        """
        Deterministically calculates coordinates for all regions and components.
        Returns a dict with structured region/component layout properties.
        """
        # 1. Position Regions
        region_layouts: Dict[str, Dict[str, float]] = {}
        
        # Default region specifications if not provided or size is 0
        defaults = {
            "sidebar": {"x": 0.0, "y": 0.0, "width": 250.0, "height": canvas_height},
            "header": {"x": 250.0, "y": 0.0, "width": canvas_width - 250.0, "height": 80.0},
            "main": {"x": 250.0, "y": 80.0, "width": canvas_width - 550.0, "height": canvas_height - 230.0},
            "context_panel": {"x": canvas_width - 300.0, "y": 80.0, "width": 300.0, "height": canvas_height - 80.0},
            "prompt_dock": {"x": 300.0, "y": canvas_height - 130.0, "width": canvas_width - 650.0, "height": 110.0},
            "activity_panel": {"x": 250.0, "y": canvas_height - 150.0, "width": canvas_width - 550.0, "height": 150.0}
        }

        # First copy predefined or use defaults
        for reg in intent.regions:
            r_id = reg.id
            reg_defaults = defaults.get(r_id, {"x": 0.0, "y": 0.0, "width": 400.0, "height": 400.0})
            
            x = reg.x if reg.x > 0 else reg_defaults["x"]
            y = reg.y if reg.y > 0 else reg_defaults["y"]
            w = reg.width if reg.width > 0 else reg_defaults["width"]
            h = reg.height if reg.height > 0 else reg_defaults["height"]
            
            region_layouts[r_id] = {"x": x, "y": y, "width": w, "height": h}

        # Fill in missing regions that might be used by components but not explicitly defined
        for comp in intent.components:
            r_id = comp.region_id
            if r_id not in region_layouts:
                reg_defaults = defaults.get(r_id, {"x": 100.0, "y": 100.0, "width": 400.0, "height": 400.0})
                region_layouts[r_id] = reg_defaults.copy()

        # 2. Stack Components inside regions deterministically
        component_layouts: Dict[str, Dict[str, float]] = {}
        region_stacks: Dict[str, float] = {} # Tracks the y-offset for stacking inside each region
        
        # Component default heights
        comp_heights = {
            "header": 60.0,
            "navigation": 180.0,
            "card": 140.0,
            "button": 40.0,
            "input": 45.0,
            "list": 200.0,
            "table": 250.0,
            "panel": 300.0,
            "status_badge": 35.0,
            "prompt_dock": 80.0,
            "activity_log": 120.0
        }

        padding = 20.0
        gap = 15.0

        for comp in intent.components:
            r_id = comp.region_id
            r_layout = region_layouts.get(r_id, {"x": 0.0, "y": 0.0, "width": 400.0, "height": 400.0})
            
            # Initialize stacking position for region if not yet started
            if r_id not in region_stacks:
                region_stacks[r_id] = r_layout["y"] + padding

            comp_type = comp.type
            comp_h = comp_heights.get(comp_type, 100.0)
            
            comp_x = r_layout["x"] + padding
            comp_w = r_layout["width"] - (2 * padding)
            comp_y = region_stacks[r_id]
            
            component_layouts[comp.id] = {
                "x": comp_x,
                "y": comp_y,
                "width": max(comp_w, 20.0),
                "height": comp_h
            }
            
            # Advance the stacking offset
            region_stacks[r_id] += comp_h + gap

        return {
            "regions": region_layouts,
            "components": component_layouts
        }
