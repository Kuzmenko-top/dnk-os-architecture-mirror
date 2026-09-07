# --- DNK-MRH-HEADER ---
# mrh_id: "supervisor/validation.py"
# purpose: "Implement JSON Schema and strict domain-safety validation for LLM design specs."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import re
import json
from typing import Dict, Any, List, Tuple

class DesignValidationException(Exception):
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"422 SCHEMA_VALIDATION_FAILED: {'; '.join(errors)}")

class StructuredDesignValidator:
    # 1. Structure JSON Schema definition
    SCHEMA = {
        "type": "object",
        "required": ["type", "version", "title", "layout", "components", "excalidraw_scene"],
        "properties": {
            "type": {"type": "string"},
            "version": {"type": "string"},
            "title": {"type": "string"},
            "layout": {"type": "object"},
            "components": {"type": "array"},
            "excalidraw_scene": {"type": "object"}
        }
    }

    # Prohibited patterns to prevent prompt injections/malicious queries
    PROHIBITED_PATTERNS = [
        (r"(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\s+", "SQL query detected"),
        (r"(/etc/passwd|/bin/sh|/bin/bash|cmd\.exe|C:\\\\Windows)", "System filesystem path detected"),
        (r"(sudo\s+|rm\s+-rf|chmod\s+|curl\s+http)", "Shell commands detected"),
        (r"(bearer|api[_-]?key|password|secret|passwd)[\s:]+['\"]?[a-zA-Z0-9_\-]{16,}", "Credentials leak detected")
    ]

    @classmethod
    def validate_design(cls, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        errors = []

        # JSON Schema validation checks
        if not isinstance(data, dict):
            return False, ["Design specification must be a dictionary."]

        for field in cls.SCHEMA["required"]:
            if field not in data:
                errors.append(f"Missing required schema field: '{field}'")

        if errors:
            return False, errors

        # 2. Strict Domain Safety Validation
        # Convert to string to check for prohibited injections
        data_str = json.dumps(data)
        for pattern, msg in cls.PROHIBITED_PATTERNS:
            if re.search(pattern, data_str, re.IGNORECASE):
                errors.append(f"Domain Validation: {msg}")

        # Validate layout elements and regions boundaries
        layout = data.get("layout", {})
        if isinstance(layout, dict):
            regions = layout.get("regions", [])
            if isinstance(regions, list):
                for region in regions:
                    if not isinstance(region, dict):
                        errors.append("Layout regions must be objects")
                        continue
                    r_id = region.get("id")
                    if not r_id:
                        errors.append("Layout region is missing an ID")
                    # Bound regions sizes
                    w = region.get("width", 0)
                    h = region.get("height", 0)
                    if w > 5000 or h > 5000:
                        errors.append(f"Region '{r_id}' dimensions are out of bounds (> 5000px)")

        # Validate Excalidraw elements
        ex_scene = data.get("excalidraw_scene", {})
        if isinstance(ex_scene, dict):
            elements = ex_scene.get("elements", [])
            if isinstance(elements, list):
                for elem in elements:
                    if not isinstance(elem, dict):
                        errors.append("Excalidraw element must be a dictionary")
                        continue
                    # Check for nebezpechnyi (unsafe) direct DB action in event label
                    label = elem.get("label", "")
                    if label and any(p[0] in str(label) for p in cls.PROHIBITED_PATTERNS):
                        errors.append(f"Excalidraw element {elem.get('id')} contains unsafe label instructions.")

        return len(errors) == 0, errors
