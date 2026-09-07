# --- DNK-MRH-HEADER ---
# mrh_id: "compiler/compiler_validation.py"
# purpose: "Implement rigorous validation gates for DesignIntent and compiled Excalidraw scenes."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

import re
import json
from typing import Dict, Any, List
from .compiler_types import (
    DesignIntent, SUPPORTED_COMPONENTS, SUPPORTED_REGIONS, SUPPORTED_INTERACTIONS
)

class CompilerValidationException(Exception):
    def __init__(self, message: str, error_code: str = "VALIDATION_FAILED"):
        self.message = message
        self.error_code = error_code
        super().__init__(f"{error_code}: {message}")

class UnsupportedComponentException(CompilerValidationException):
    def __init__(self, component_type: str):
        super().__init__(
            f"Component type '{component_type}' is not supported.",
            "UNSUPPORTED_DESIGN_COMPONENT"
        )

class CompilerValidator:
    # Prohibited patterns to prevent prompt injections, malicious queries, paths, URLs or credentials
    PROHIBITED_PATTERNS = [
        (r"(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER)\s+", "SQL query detected"),
        (r"(/etc/passwd|/bin/sh|/bin/bash|cmd\.exe|C:\\\\Windows)", "System filesystem path detected"),
        (r"(sudo\s+|rm\s+-rf|chmod\s+|curl\s+http)", "Shell commands detected"),
        (r"(bearer|api[_-]?key|password|secret|passwd)[\s:]+['\"]?[a-zA-Z0-9_\\-]{16,}", "Credentials leak detected")
    ]

    @classmethod
    def validate_design_intent(cls, intent: DesignIntent):
        # 1. Component types validation (unknown types must give 422 UNSUPPORTED_DESIGN_COMPONENT)
        for comp in intent.components:
            if comp.type not in SUPPORTED_COMPONENTS:
                raise UnsupportedComponentException(comp.type)

        # 2. Region types validation
        for reg in intent.regions:
            if reg.id not in SUPPORTED_REGIONS:
                raise CompilerValidationException(
                    f"Region type '{reg.id}' is not supported.",
                    "UNSUPPORTED_DESIGN_REGION"
                )

        # 3. Interaction types validation
        for inter in intent.interactions:
            if inter.type not in SUPPORTED_INTERACTIONS:
                raise CompilerValidationException(
                    f"Interaction type '{inter.type}' is not supported.",
                    "UNSUPPORTED_DESIGN_INTERACTION"
                )

        # 4. Prohibited patterns check in intent data
        intent_str = json.dumps(intent.model_dump())
        for pattern, msg in cls.PROHIBITED_PATTERNS:
            if re.search(pattern, intent_str, re.IGNORECASE):
                raise CompilerValidationException(
                    f"Safety Violation: {msg}",
                    "SAFETY_VIOLATION"
                )

        # 5. Coordinate safety checks for regions
        for reg in intent.regions:
            if reg.x < 0 or reg.y < 0:
                raise CompilerValidationException(
                    f"Region '{reg.id}' has negative coordinates.",
                    "NEGATIVE_COORDINATES"
                )
            if reg.width < 0 or reg.height < 0:
                raise CompilerValidationException(
                    f"Region '{reg.id}' has negative dimensions.",
                    "NEGATIVE_DIMENSIONS"
                )
            if reg.x + reg.width > 5000 or reg.y + reg.height > 5000:
                raise CompilerValidationException(
                    f"Region '{reg.id}' boundaries are out of bounds (> 5000px).",
                    "OUT_OF_BOUNDS_LAYOUT"
                )

    @classmethod
    def validate_compiled_elements(cls, elements: List[Dict[str, Any]], max_elements: int = 500):
        # 1. Limit total elements count
        if len(elements) > max_elements:
            raise CompilerValidationException(
                f"Total elements count {len(elements)} exceeds max allowed limit of {max_elements}.",
                "MAX_ELEMENTS_EXCEEDED"
            )

        element_ids = set()
        for elem in elements:
            elem_id = elem.get("id")
            # 2. Unique element IDs
            if not elem_id:
                raise CompilerValidationException("Element is missing an ID.", "MISSING_ELEMENT_ID")
            if elem_id in element_ids:
                raise CompilerValidationException(f"Duplicate element ID '{elem_id}' detected.", "DUPLICATE_ELEMENT_ID")
            element_ids.add(elem_id)

            # 3. Coordinates bounds check
            x = elem.get("x", 0)
            y = elem.get("y", 0)
            w = elem.get("width", 0)
            h = elem.get("height", 0)

            if x < 0 or y < 0:
                raise CompilerValidationException(
                    f"Element '{elem_id}' has negative coordinates ({x}, {y}).",
                    "OUT_OF_BOUNDS_LAYOUT"
                )
            if w < 0 or h < 0:
                raise CompilerValidationException(
                    f"Element '{elem_id}' has negative dimensions ({w}x{h}).",
                    "NEGATIVE_DIMENSIONS"
                )
            if x + w > 5000 or y + h > 5000:
                raise CompilerValidationException(
                    f"Element '{elem_id}' bounds exceed canvas size 5000x5000.",
                    "OUT_OF_BOUNDS_LAYOUT"
                )

            # 4. Text length limit
            text = elem.get("text", "")
            if text and len(str(text)) > 2000:
                raise CompilerValidationException(
                    f"Text in element '{elem_id}' exceeds max allowed length of 2000 characters.",
                    "TEXT_LENGTH_EXCEEDED"
                )
