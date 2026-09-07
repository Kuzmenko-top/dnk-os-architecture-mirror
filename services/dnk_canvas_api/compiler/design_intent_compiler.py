# --- DNK-MRH-HEADER ---
# mrh_id: "compiler/design_intent_compiler.py"
# purpose: "Implement a deterministic compiler that translates DesignIntent to canonical Excalidraw CompiledCanvas."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

import json
import hashlib
from typing import Dict, Any, List
from .compiler_types import DesignIntent, CompiledCanvas
from .compiler_validation import CompilerValidator
from .layout_engine import LayoutEngine

COMPILER_VERSION = "1.0.0"

class DesignIntentCompiler:
    @classmethod
    def compute_sha256(cls, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @classmethod
    def compile(cls, intent: DesignIntent, source_artifact_id: str) -> CompiledCanvas:
        # 1. Run Schema and Domain Validation Gates
        CompilerValidator.validate_design_intent(intent)

        # 2. Serialize DesignIntent to compute stable input hash
        serialized_intent = json.dumps(intent.model_dump(), sort_keys=True)
        input_hash = cls.compute_sha256(serialized_intent)

        # 3. Deterministically calculate layout
        layout = LayoutEngine.calculate_layout(intent)
        regions_layout = layout["regions"]
        components_layout = layout["components"]

        # 4. Generate Excalidraw Elements
        elements: List[Dict[str, Any]] = []

        # Version seed helper
        def make_element_id(prefix: str, identifier: str) -> str:
            # Deterministic ID generation based on prefix and identifier
            combined = f"{prefix}-{identifier}"
            return cls.compute_sha256(combined)[:10]

        # Draw regions
        for reg_id, r_bounds in regions_layout.items():
            reg_rect_id = make_element_id("region-rect", reg_id)
            reg_text_id = make_element_id("region-text", reg_id)

            # Region Background Container
            elements.append({
                "id": reg_rect_id,
                "type": "rectangle",
                "x": r_bounds["x"],
                "y": r_bounds["y"],
                "width": r_bounds["width"],
                "height": r_bounds["height"],
                "angle": 0.0,
                "strokeColor": "#94a3b8", # slate-400
                "backgroundColor": "#f8fafc", # slate-50
                "fillStyle": "solid",
                "strokeWidth": 1.0,
                "strokeStyle": "dashed",
                "roughness": 0.0,
                "opacity": 100.0,
                "seed": int(make_element_id("region-seed-rect", reg_id), 16) % 1000000,
                "version": 1,
                "versionNonce": int(make_element_id("region-nonce-rect", reg_id), 16) % 1000000,
                "isDeleted": False,
                "roundness": {"type": 3},
                "locked": True
            })

            # Region Label
            elements.append({
                "id": reg_text_id,
                "type": "text",
                "x": r_bounds["x"] + 10,
                "y": r_bounds["y"] + 10,
                "width": 150.0,
                "height": 20.0,
                "angle": 0.0,
                "strokeColor": "#64748b", # slate-500
                "backgroundColor": "transparent",
                "fillStyle": "hachure",
                "strokeWidth": 1.0,
                "strokeStyle": "solid",
                "roughness": 0.0,
                "opacity": 100.0,
                "seed": int(make_element_id("region-seed-text", reg_id), 16) % 1000000,
                "version": 1,
                "versionNonce": int(make_element_id("region-nonce-text", reg_id), 16) % 1000000,
                "isDeleted": False,
                "text": f"[{reg_id.upper()}]",
                "fontSize": 14.0,
                "fontFamily": 1, # sans-serif
                "textAlign": "left",
                "verticalAlign": "top"
            })

        # Draw components
        for comp in intent.components:
            comp_id = comp.id
            c_bounds = components_layout.get(comp_id, {"x": 0.0, "y": 0.0, "width": 100.0, "height": 100.0})

            comp_rect_id = make_element_id("comp-rect", comp_id)
            comp_text_id = make_element_id("comp-text", comp_id)

            # Assign color/style based on type
            stroke_color = "#0f172a" # slate-900
            fill_style = "solid"
            
            if comp.type == "button":
                bg_color = "#ccfbf1" # teal-100
                stroke_color = "#0d9488" # teal-600
                roundness_type = 3
            elif comp.type == "input":
                bg_color = "#f1f5f9" # slate-100
                roundness_type = 2
            elif comp.type == "card":
                bg_color = "#ffffff"
                roundness_type = 3
            else:
                bg_color = "#fef08a" # yellow-100
                roundness_type = 1

            # Component Container
            elements.append({
                "id": comp_rect_id,
                "type": "rectangle",
                "x": c_bounds["x"],
                "y": c_bounds["y"],
                "width": c_bounds["width"],
                "height": c_bounds["height"],
                "angle": 0.0,
                "strokeColor": stroke_color,
                "backgroundColor": bg_color,
                "fillStyle": fill_style,
                "strokeWidth": 2.0,
                "strokeStyle": "solid",
                "roughness": 0.0,
                "opacity": 100.0,
                "seed": int(make_element_id("comp-seed-rect", comp_id), 16) % 1000000,
                "version": 1,
                "versionNonce": int(make_element_id("comp-nonce-rect", comp_id), 16) % 1000000,
                "isDeleted": False,
                "roundness": {"type": roundness_type},
                "locked": False
            })

            # Component Title/Label
            title_text = comp.title or f"{comp.type.capitalize()}: {comp_id}"
            elements.append({
                "id": comp_text_id,
                "type": "text",
                "x": c_bounds["x"] + 15,
                "y": c_bounds["y"] + (c_bounds["height"] / 2.0) - 10,
                "width": c_bounds["width"] - 30,
                "height": 20.0,
                "angle": 0.0,
                "strokeColor": "#0f172a",
                "backgroundColor": "transparent",
                "fillStyle": "hachure",
                "strokeWidth": 1.0,
                "strokeStyle": "solid",
                "roughness": 0.0,
                "opacity": 100.0,
                "seed": int(make_element_id("comp-seed-text", comp_id), 16) % 1000000,
                "version": 1,
                "versionNonce": int(make_element_id("comp-nonce-text", comp_id), 16) % 1000000,
                "isDeleted": False,
                "text": title_text,
                "fontSize": 16.0,
                "fontFamily": 1,
                "textAlign": "center",
                "verticalAlign": "middle"
            })

        # 5. Run compiled elements safety and coordinates validation gates
        CompilerValidator.validate_compiled_elements(elements)

        # 6. Stable output serialization & hash calculation
        serialized_elements = json.dumps(elements, sort_keys=True)
        output_hash = cls.compute_sha256(serialized_elements)

        # 7. Construct and return CompiledCanvas
        return CompiledCanvas(
            elements=elements,
            app_state={
                "viewBackgroundColor": "#ffffff",
                "gridSize": 20
            },
            files={},
            compiler_version=COMPILER_VERSION,
            source_artifact_id=source_artifact_id,
            source_hash=input_hash
        )
