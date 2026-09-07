# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_shopify_builder/liquid_compiler.py"
# purpose: "High-Performance Liquid AST Parser, Validator, Schema Diagnostic Engine, and Section Compiler for dnk_shopify agent."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class LiquidSyntaxError(Exception):
    pass


class LiquidSectionModel(BaseModel):
    name: str
    tag: str = "section"
    class_name: str = "dnk-shopify-section"
    liquid_body: str
    css_content: str = ""
    js_content: str = ""
    settings_schema: Dict[str, Any] = Field(default_factory=dict)


class LiquidCompiler:
    """
    Liquid AST & Section Compiler.
    Validates tag balance ({% if %}, {% for %}, {% schema %}, {% javascript %}, {% style %}),
    checks {{ block.shopify_attributes }} placement, validates Shopify OS 2.0 schema setting types,
    and compiles production-ready Shopify theme sections.
    """

    TAG_PAIRS = {
        "if": "endif",
        "unless": "endunless",
        "for": "endfor",
        "case": "endcase",
        "tablerow": "endtablerow",
        "form": "endform",
        "paginate": "endpaginate",
        "schema": "endschema",
        "style": "endstyle",
        "stylesheet": "endstylesheet",
        "javascript": "endjavascript",
        "comment": "endcomment",
    }

    SUPPORTED_SETTING_TYPES = {
        "text",
        "textarea",
        "image_picker",
        "color",
        "color_background",
        "range",
        "select",
        "checkbox",
        "radio",
        "richtext",
        "inline_richtext",
        "font_picker",
        "collection",
        "product",
        "blog",
        "page",
        "link_list",
        "url",
        "video",
        "video_url",
        "html",
        "liquid",
        "number",
        "header",
        "paragraph",
    }

    def validate_syntax(self, liquid_code: str) -> Tuple[bool, Optional[str]]:
        """Validates that all liquid tags are properly opened and closed."""
        tag_stack: List[Tuple[str, int]] = []
        lines = liquid_code.splitlines()

        for line_num, line in enumerate(lines, start=1):
            matches = re.finditer(r"\{%\s*([a-zA-Z0-9_]+)", line)
            for m in matches:
                tag = m.group(1).strip()
                if tag in self.TAG_PAIRS:
                    tag_stack.append((tag, line_num))
                elif tag.startswith("end"):
                    if not tag_stack:
                        return False, f"Unexpected closing tag '{tag}' at line {line_num}"
                    last_tag, last_line = tag_stack[-1]
                    expected_closing = self.TAG_PAIRS.get(last_tag)
                    if tag == expected_closing:
                        tag_stack.pop()
                    else:
                        return False, f"Mismatched closing tag '{tag}' at line {line_num} (expected '{expected_closing}' for '{last_tag}' from line {last_line})"

        if tag_stack:
            unclosed_tag, unclosed_line = tag_stack[-1]
            return False, f"Unclosed tag '{unclosed_tag}' from line {unclosed_line} (missing 'end{unclosed_tag}')"

        return True, None

    def validate_shopify_attributes_placement(self, liquid_code: str) -> List[Dict[str, Any]]:
        """
        Validates placement of {{ block.shopify_attributes }}.
        In Shopify OS 2.0, {{ block.shopify_attributes }} must reside inside the opening tag
        of a block container (e.g. <div {{ block.shopify_attributes }} class="...">),
        never outside tags or inside inner text content.
        """
        issues: List[Dict[str, Any]] = []
        pattern = re.compile(r"\{\{\-?\s*block\.shopify_attributes\s*\-?\}\}")

        # Find all occurrences
        for m in pattern.finditer(liquid_code):
            pos = m.start()
            line_num = liquid_code[:pos].count("\n") + 1

            # Check surrounding context in the string
            # Find the preceding '<' and '>'
            pre_str = liquid_code[:pos]
            last_open = pre_str.rfind("<")
            last_close = pre_str.rfind(">")

            # Find the succeeding '>' and '<'
            post_str = liquid_code[m.end():]
            next_close = post_str.find(">")
            next_open = post_str.find("<")

            is_inside_tag = False
            if last_open != -1 and (last_close == -1 or last_open > last_close):
                if next_close != -1 and (next_open == -1 or next_close < next_open):
                    tag_content = liquid_code[last_open : m.end() + next_close + 1]
                    # Ensure it's not a closing tag like </div {{ block.shopify_attributes }}>
                    if not tag_content.startswith("</"):
                        is_inside_tag = True

            if not is_inside_tag:
                issues.append({
                    "line": line_num,
                    "type": "error",
                    "code": "SHOPIFY_ATTRIBUTES_OUTSIDE_TAG",
                    "message": f"Line {line_num}: '{{{{ block.shopify_attributes }}}}' must be placed inside an opening HTML tag (e.g., <div {{{{ block.shopify_attributes }}}}>)."
                })

        return issues

    def validate_settings_schema(self, schema_data: Any) -> List[Dict[str, Any]]:
        """
        Validates the schema structure and setting types according to Shopify OS 2.0 specifications.
        """
        issues: List[Dict[str, Any]] = []
        if not isinstance(schema_data, dict):
            issues.append({
                "type": "error",
                "code": "SCHEMA_NOT_OBJECT",
                "message": "Root schema must be a JSON object"
            })
            return issues

        # 1. Validate top-level settings
        settings = schema_data.get("settings", [])
        if not isinstance(settings, list):
            issues.append({
                "type": "error",
                "code": "SETTINGS_NOT_ARRAY",
                "message": "'settings' field in schema must be an array"
            })
        else:
            for idx, setting in enumerate(settings):
                self._validate_single_setting(setting, f"settings[{idx}]", issues)

        # 2. Validate blocks
        blocks = schema_data.get("blocks", [])
        if not isinstance(blocks, list):
            issues.append({
                "type": "error",
                "code": "BLOCKS_NOT_ARRAY",
                "message": "'blocks' field in schema must be an array"
            })
        else:
            for b_idx, block in enumerate(blocks):
                if not isinstance(block, dict):
                    issues.append({
                        "type": "error",
                        "code": "BLOCK_NOT_OBJECT",
                        "message": f"Block at index {b_idx} must be an object"
                    })
                    continue
                if "type" not in block:
                    issues.append({
                        "type": "error",
                        "code": "BLOCK_MISSING_TYPE",
                        "message": f"Block at index {b_idx} is missing required 'type' attribute"
                    })
                b_settings = block.get("settings", [])
                if not isinstance(b_settings, list):
                    issues.append({
                        "type": "error",
                        "code": "BLOCK_SETTINGS_NOT_ARRAY",
                        "message": f"Block '{block.get('type', b_idx)}' settings must be an array"
                    })
                else:
                    for bs_idx, b_setting in enumerate(b_settings):
                        self._validate_single_setting(b_setting, f"blocks[{b_idx}].settings[{bs_idx}]", issues)

        return issues

    def _validate_single_setting(self, setting: Any, path: str, issues: List[Dict[str, Any]]) -> None:
        if not isinstance(setting, dict):
            issues.append({
                "type": "error",
                "code": "SETTING_NOT_OBJECT",
                "message": f"Setting at {path} must be an object"
            })
            return

        s_type = setting.get("type")
        if not s_type:
            issues.append({
                "type": "error",
                "code": "SETTING_MISSING_TYPE",
                "message": f"Setting at {path} is missing required 'type'"
            })
            return

        if s_type not in self.SUPPORTED_SETTING_TYPES:
            issues.append({
                "type": "error",
                "code": "UNSUPPORTED_SETTING_TYPE",
                "message": f"Setting at {path} has unsupported type '{s_type}'. Supported: {', '.join(sorted(self.SUPPORTED_SETTING_TYPES))}"
            })
            return

        # Header and paragraph don't strictly require id
        if s_type not in ("header", "paragraph"):
            if "id" not in setting or not setting["id"]:
                issues.append({
                    "type": "error",
                    "code": "SETTING_MISSING_ID",
                    "message": f"Setting '{s_type}' at {path} is missing required 'id'"
                })
            if "label" not in setting or not setting["label"]:
                issues.append({
                    "type": "warning",
                    "code": "SETTING_MISSING_LABEL",
                    "message": f"Setting '{setting.get('id', s_type)}' at {path} should have a 'label'"
                })

        # Range specific checks
        if s_type == "range":
            for req_field in ("min", "max", "step"):
                if req_field not in setting:
                    issues.append({
                        "type": "error",
                        "code": "RANGE_MISSING_ATTRIBUTE",
                        "message": f"Range setting at {path} requires '{req_field}' attribute"
                    })

        # Select / Radio specific checks
        if s_type in ("select", "radio"):
            options = setting.get("options")
            if not isinstance(options, list) or len(options) == 0:
                issues.append({
                    "type": "error",
                    "code": "SELECT_OPTIONS_MISSING",
                    "message": f"Setting '{s_type}' at {path} requires a non-empty 'options' list"
                })

    def extract_schema(self, liquid_code: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Extracts JSON schema from {% schema %} block."""
        match = re.search(r"\{%\s*schema\s*%\}(.*?)\{%\s*endschema\s*%\}", liquid_code, re.DOTALL)
        if not match:
            return None, "No {% schema %} block found"
        try:
            schema_json = json.loads(match.group(1).strip())
            return schema_json, None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON in schema block: {str(e)}"

    def validate_section_full(self, liquid_code: str) -> Dict[str, Any]:
        """
        Executes complete Shopify theme section diagnostic & validation suite:
        - Tag balance and syntax.
        - Block shopify_attributes placement.
        - Schema JSON extraction and validation.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Syntax & tag balance
        is_valid_syntax, syntax_err = self.validate_syntax(liquid_code)
        if not is_valid_syntax and syntax_err:
            errors.append(syntax_err)

        # 2. shopify_attributes placement
        attr_issues = self.validate_shopify_attributes_placement(liquid_code)
        for issue in attr_issues:
            if issue["type"] == "error":
                errors.append(issue["message"])
            else:
                warnings.append(issue["message"])

        # 3. Schema block
        schema_dict, schema_err = self.extract_schema(liquid_code)
        if schema_err and "{% schema %}" in liquid_code:
            errors.append(schema_err)
        elif schema_dict:
            schema_issues = self.validate_settings_schema(schema_dict)
            for s_issue in schema_issues:
                if s_issue["type"] == "error":
                    errors.append(s_issue["message"])
                else:
                    warnings.append(s_issue["message"])

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "schema": schema_dict
        }

    # Alias for convenience
    validate = validate_section_full

    def compile_section(self, section: LiquidSectionModel) -> str:
        """Compiles a clean, validated Shopify theme section file."""
        is_valid, error = self.validate_syntax(section.liquid_body)
        if not is_valid:
            raise LiquidSyntaxError(f"Liquid syntax validation failed: {error}")

        parts = [
            f"{{% comment %}}\n  Auto-compiled by DNK OS LiquidCompiler for {section.name}\n{{% endcomment %}}",
        ]

        if section.css_content:
            parts.append(f"{{% style %}}\n{section.css_content.strip()}\n{{% endstyle %}}")

        parts.append(section.liquid_body.strip())

        if section.js_content:
            parts.append(f"{{% javascript %}}\n{section.js_content.strip()}\n{{% endjavascript %}}")

        if section.settings_schema:
            schema_json_str = json.dumps(section.settings_schema, indent=2)
            parts.append(f"{{% schema %}}\n{schema_json_str}\n{{% endschema %}}")

        return "\n\n".join(parts) + "\n"


liquid_compiler = LiquidCompiler()
