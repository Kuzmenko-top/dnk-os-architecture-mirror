# --- DNK-MRH-HEADER ---
# mrh_id: "supervisor/context_builder.py"
# purpose: "Implement Context Builder to compile and filter context data for design runs."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("context_builder")

class ContextBuilder:
    @staticmethod
    def build_context(
        db, 
        project_id: str, 
        canvas_id: str, 
        prompt: str, 
        design_system_id: str, 
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        logger.info(f"Assembling design context for project {project_id}, canvas {canvas_id}")
        
        # 1. Project metadata (mocked or loaded if model exists)
        project_metadata = {
            "id": project_id,
            "name": f"DNK OS Workspace {project_id[:6]}",
            "environment": "production"
        }

        # 2. Design System definition
        design_system = {
            "id": design_system_id or "dnk-default",
            "theme": "macchiato",
            "grid_size": 10,
            "colors": {
                "background": "#1e1e2e",
                "sidebar": "#181825",
                "accent": "#f38ba8",
                "text": "#cdd6f4"
            }
        }

        # 3. Assemble full context dict, carefully stripping any potentially sensitive details
        context = {
            "project_id": project_id,
            "canvas_id": canvas_id,
            "prompt": prompt,
            "design_system_id": design_system_id,
            "project_metadata": project_metadata,
            "design_system": design_system,
            "active_canvas_metadata": {
                "canvas_id": canvas_id,
                "document_type": "excalidraw"
            },
            "last_canvas_snapshot": {
                "version": 1,
                "elements": [] # Fetch if query available or empty for new
            },
            "selected_screenshots": [] # Optional screenshots list
        }

        # Exclude secrets, credentials, irrelevant data
        # We explicitly ensure no credentials/api_keys are loaded in this payload
        context.pop("secrets", None)
        context.pop("credentials", None)
        context.pop("api_keys", None)

        return context
