# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/shopify_theme_extension.py"
# purpose: "Shopify Theme Extension, App Block Schema Generator & Theme Store V2 Compliance Engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-ECOM-003"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym / Gerych Prime"
# --- END DNK-MRH-HEADER ---

"""
Shopify Theme Extension, App Block Schema Generator & Theme Store V2 Compliance Engine.
Implements Online Store 2.0 standards, Theme App Extension (TAE) schemas, and strict validation.
"""

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class AppBlockTarget(str, Enum):
    SECTION = "section"
    BODY = "body"
    HEAD = "head"


class SettingType(str, Enum):
    # Basic input settings
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    RANGE = "range"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    COLOR = "color"
    COLOR_BACKGROUND = "color_background"
    FONT_PICKER = "font_picker"
    # Resource pickers
    IMAGE_PICKER = "image_picker"
    VIDEO = "video"
    URL = "url"
    COLLECTION = "collection"
    PRODUCT = "product"
    PRODUCT_LIST = "product_list"
    BLOG = "blog"
    PAGE = "page"
    LINK_LIST = "link_list"
    # Content & code
    HTML = "html"
    LIQUID = "liquid"
    RICHTEXT = "richtext"
    # Informational
    HEADER = "header"
    PARAGRAPH = "paragraph"


VALID_SETTING_TYPES: Set[str] = {st.value for st in SettingType}


@dataclass
class SchemaSetting:
    type: str
    id: str
    label: str
    default: Optional[Any] = None
    info: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    unit: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "type": self.type,
            "id": self.id,
            "label": self.label
        }
        if self.default is not None:
            data["default"] = self.default
        if self.info:
            data["info"] = self.info
        if self.type == "range":
            if self.min is not None:
                data["min"] = self.min
            if self.max is not None:
                data["max"] = self.max
            if self.step is not None:
                data["step"] = self.step
            if self.unit:
                data["unit"] = self.unit
        if self.options and self.type in ("select", "radio"):
            data["options"] = self.options
        return data


@dataclass
class BlockDefinition:
    type: str
    name: str
    limit: Optional[int] = None
    settings: List[SchemaSetting] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        res: Dict[str, Any] = {
            "type": self.type,
            "name": self.name,
            "settings": [s.to_dict() for s in self.settings]
        }
        if self.limit:
            res["limit"] = self.limit
        return res


@dataclass
class SectionPreset:
    name: str
    category: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    blocks: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": self.name,
            "settings": self.settings
        }
        if self.category:
            data["category"] = self.category
        if self.blocks:
            data["blocks"] = self.blocks
        return data


@dataclass
class AppBlockSchema:
    name: str
    target: AppBlockTarget = AppBlockTarget.SECTION
    javascript: Optional[str] = None
    stylesheet: Optional[str] = None
    settings: List[SchemaSetting] = field(default_factory=list)
    available_if: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "name": self.name,
            "target": self.target.value,
            "settings": [s.to_dict() for s in self.settings]
        }
        if self.javascript:
            data["javascript"] = self.javascript
        if self.stylesheet:
            data["stylesheet"] = self.stylesheet
        if self.available_if:
            data["available_if"] = self.available_if
        return data


@dataclass
class ValidationIssue:
    severity: str  # "error", "warning", "info"
    code: str
    message: str
    file_path: Optional[str] = None
    line: Optional[int] = None


@dataclass
class ComplianceReport:
    is_valid: bool
    score: int  # 0 to 100
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AppBlockSchemaGenerator:
    """
    Generates and parses Liquid {% schema %} blocks for Theme App Extensions (TAE)
    and Shopify Online Store 2.0 sections.
    """

    @staticmethod
    def generate_app_block_schema(
        name: str,
        target: str = "section",
        javascript: Optional[str] = None,
        stylesheet: Optional[str] = None,
        settings: Optional[List[Dict[str, Any]]] = None,
        available_if: Optional[str] = None
    ) -> str:
        """
        Generate a valid {% schema %} JSON block for a Shopify Theme App Extension App Block.
        """
        target_enum = AppBlockTarget(target)
        parsed_settings: List[SchemaSetting] = []
        if settings:
            for s in settings:
                parsed_settings.append(SchemaSetting(
                    type=s.get("type", "text"),
                    id=s.get("id", ""),
                    label=s.get("label", ""),
                    default=s.get("default"),
                    info=s.get("info"),
                    min=s.get("min"),
                    max=s.get("max"),
                    step=s.get("step"),
                    unit=s.get("unit"),
                    options=s.get("options")
                ))

        block_schema = AppBlockSchema(
            name=name,
            target=target_enum,
            javascript=javascript,
            stylesheet=stylesheet,
            settings=parsed_settings,
            available_if=available_if
        )
        schema_json = json.dumps(block_schema.to_dict(), indent=2)
        return f"{{% schema %}}\n{schema_json}\n{{% endschema %}}"

    @staticmethod
    def generate_section_schema(
        name: str,
        tag: Optional[str] = "section",
        class_name: Optional[str] = None,
        limit: Optional[int] = None,
        settings: Optional[List[Dict[str, Any]]] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        presets: Optional[List[Dict[str, Any]]] = None,
        max_blocks: Optional[int] = None,
        disabled_on: Optional[Dict[str, Any]] = None,
        enabled_on: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a valid {% schema %} JSON block for an OS 2.0 theme section.
        """
        schema_dict: Dict[str, Any] = {
            "name": name
        }
        if tag:
            schema_dict["tag"] = tag
        if class_name:
            schema_dict["class"] = class_name
        if limit:
            schema_dict["limit"] = limit
        if max_blocks:
            schema_dict["max_blocks"] = max_blocks

        schema_dict["settings"] = settings or []
        if blocks:
            schema_dict["blocks"] = blocks
        if presets:
            schema_dict["presets"] = presets
        if disabled_on:
            schema_dict["disabled_on"] = disabled_on
        if enabled_on:
            schema_dict["enabled_on"] = enabled_on

        schema_json = json.dumps(schema_dict, indent=2)
        return f"{{% schema %}}\n{schema_json}\n{{% endschema %}}"

    @staticmethod
    def extract_schema_from_liquid(liquid_content: str) -> Optional[Dict[str, Any]]:
        """
        Extract and parse JSON from {% schema %}...{% endschema %} tags.
        """
        match = re.search(r'\{%\s*schema\s*%\}([\s\S]*?)\{%\s*endschema\s*%\}', liquid_content)
        if not match:
            return None
        raw_json = match.group(1).strip()
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in schema block: {exc}") from exc


class SectionConfigManager:
    """
    Manages and builds Online Store 2.0 JSON templates (templates/*.json)
    and section group configurations (sections/*-group.json).
    """

    @staticmethod
    def build_template_json(
        sections: Dict[str, Dict[str, Any]],
        order: List[str],
        name: Optional[str] = None,
        wrapper: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build an OS 2.0 template JSON structure.
        """
        template: Dict[str, Any] = {
            "sections": sections,
            "order": order
        }
        if name:
            template["name"] = name
        if wrapper:
            template["wrapper"] = wrapper
        return template

    @staticmethod
    def build_section_group_json(
        name: str,
        sections: Dict[str, Dict[str, Any]],
        order: List[str],
        group_type: str = "header"
    ) -> Dict[str, Any]:
        """
        Build an OS 2.0 section group (header-group.json or footer-group.json).
        """
        return {
            "name": name,
            "type": group_type,
            "sections": sections,
            "order": order
        }

    @staticmethod
    def build_app_block_instance(
        app_block_type: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a section block definition for an App Block.
        """
        return {
            "type": app_block_type,
            "settings": settings or {}
        }


class ThemeStoreV2Validator:
    """
    Validator for Shopify Theme Store V2 and Theme App Extension (TAE) compliance.
    """

    @classmethod
    def validate_app_block_liquid(cls, file_name: str, content: str) -> ComplianceReport:
        """
        Validate an App Block Liquid file (under blocks/*.liquid).
        """
        errors: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []
        recommendations: List[str] = []

        # 1. Schema existence check
        schema = None
        try:
            schema = AppBlockSchemaGenerator.extract_schema_from_liquid(content)
        except ValueError as exc:
            errors.append(ValidationIssue(
                severity="error",
                code="INVALID_SCHEMA_JSON",
                message=str(exc),
                file_path=file_name
            ))

        if not schema and not errors:
            errors.append(ValidationIssue(
                severity="error",
                code="MISSING_SCHEMA_BLOCK",
                message="App Block must contain a valid {% schema %} block.",
                file_path=file_name
            ))

        if schema:
            # 2. Required properties
            if "name" not in schema or not schema["name"]:
                errors.append(ValidationIssue(
                    severity="error",
                    code="SCHEMA_MISSING_NAME",
                    message="Schema must specify a non-empty 'name'.",
                    file_path=file_name
                ))
            if "target" not in schema:
                errors.append(ValidationIssue(
                    severity="error",
                    code="SCHEMA_MISSING_TARGET",
                    message="App Block schema must specify 'target' ('section', 'body', or 'head').",
                    file_path=file_name
                ))
            else:
                target = schema.get("target")
                if target not in [t.value for t in AppBlockTarget]:
                    errors.append(ValidationIssue(
                        severity="error",
                        code="INVALID_SCHEMA_TARGET",
                        message=f"Invalid target '{target}'. Allowed targets: section, body, head.",
                        file_path=file_name
                    ))

            # 3. Settings validation
            settings = schema.get("settings", [])
            if not isinstance(settings, list):
                errors.append(ValidationIssue(
                    severity="error",
                    code="INVALID_SETTINGS_TYPE",
                    message="Schema 'settings' must be a list of setting objects.",
                    file_path=file_name
                ))
            else:
                seen_ids: Set[str] = set()
                for idx, setting in enumerate(settings):
                    stype = setting.get("type")
                    sid = setting.get("id")

                    if not stype or stype not in VALID_SETTING_TYPES:
                        errors.append(ValidationIssue(
                            severity="error",
                            code="UNKNOWN_SETTING_TYPE",
                            message=f"Unknown or missing setting type '{stype}' at index {idx}.",
                            file_path=file_name
                        ))

                    # Headers & paragraphs don't require an ID
                    if stype not in ("header", "paragraph"):
                        if not sid:
                            errors.append(ValidationIssue(
                                severity="error",
                                code="SETTING_MISSING_ID",
                                message=f"Setting at index {idx} must have an 'id'.",
                                file_path=file_name
                            ))
                        elif sid in seen_ids:
                            errors.append(ValidationIssue(
                                severity="error",
                                code="DUPLICATE_SETTING_ID",
                                message=f"Duplicate setting id '{sid}'.",
                                file_path=file_name
                            ))
                        else:
                            seen_ids.add(sid)

                    # Range validation
                    if stype == "range":
                        if "min" not in setting or "max" not in setting:
                            errors.append(ValidationIssue(
                                severity="error",
                                code="RANGE_MISSING_MIN_MAX",
                                message=f"Range setting '{sid}' must specify both 'min' and 'max'.",
                                file_path=file_name
                            ))

            # 4. Asset checks
            js_asset = schema.get("javascript")
            if js_asset and not (js_asset.endswith(".js") or js_asset.endswith(".mjs")):
                warnings.append(ValidationIssue(
                    severity="warning",
                    code="UNCONVENTIONAL_JS_EXTENSION",
                    message=f"JavaScript asset '{js_asset}' should have a .js or .mjs extension.",
                    file_path=file_name
                ))
            css_asset = schema.get("stylesheet")
            if css_asset and not css_asset.endswith(".css"):
                warnings.append(ValidationIssue(
                    severity="warning",
                    code="UNCONVENTIONAL_CSS_EXTENSION",
                    message=f"Stylesheet asset '{css_asset}' should have a .css extension.",
                    file_path=file_name
                ))

        # 5. Liquid AST syntax / anti-pattern checks
        if re.search(r'\{%\s*include\s+', content):
            warnings.append(ValidationIssue(
                severity="warning",
                code="DEPRECATED_INCLUDE_TAG",
                message="Deprecated {% include %} tag detected. Use {% render %} for better performance.",
                file_path=file_name
            ))
            recommendations.append("Replace all {% include %} tags with {% render %}.")

        if "<script" in content and "defer" not in content and "async" not in content:
            if "type=\"application/json\"" not in content and "type=\"application/ld+json\"" not in content:
                warnings.append(ValidationIssue(
                    severity="warning",
                    code="BLOCKING_SCRIPT_TAG",
                    message="Inline <script> tags should use 'defer' or 'async' or be loaded via schema assets.",
                    file_path=file_name
                ))
                recommendations.append("Load scripts asynchronously or through schema 'javascript' attribute.")

        # Calculate score (100 base, -25 per error, -5 per warning)
        score = max(0, 100 - (len(errors) * 25) - (len(warnings) * 5))
        is_valid = len(errors) == 0

        return ComplianceReport(
            is_valid=is_valid,
            score=score,
            errors=errors,
            warnings=warnings,
            recommendations=recommendations,
            metadata={
                "file_name": file_name,
                "has_schema": schema is not None,
                "schema_name": schema.get("name") if schema else None,
                "target": schema.get("target") if schema else None
            }
        )

    @classmethod
    def validate_theme_extension_directory(
        cls,
        files: Dict[str, str]
    ) -> ComplianceReport:
        """
        Validate a full Theme App Extension tree (e.g. {'blocks/star-rating.liquid': '...', 'assets/star.js': '...'}).
        """
        all_errors: List[ValidationIssue] = []
        all_warnings: List[ValidationIssue] = []
        all_recommendations: List[str] = []

        has_blocks = any(f.startswith("blocks/") and f.endswith(".liquid") for f in files)
        if not has_blocks:
            all_errors.append(ValidationIssue(
                severity="error",
                code="NO_APP_BLOCKS_FOUND",
                message="Theme App Extension must contain at least one .liquid file in 'blocks/' directory."
            ))

        for file_path, content in files.items():
            if file_path.startswith("blocks/") and file_path.endswith(".liquid"):
                report = cls.validate_app_block_liquid(file_path, content)
                all_errors.extend(report.errors)
                all_warnings.extend(report.warnings)
                all_recommendations.extend(report.recommendations)

            # Check asset size limits (mock text size for simplicity: > 100KB is warning, > 5MB is error)
            if file_path.startswith("assets/"):
                size_kb = len(content.encode("utf-8")) / 1024
                if size_kb > 5000:
                    all_errors.append(ValidationIssue(
                        severity="error",
                        code="ASSET_SIZE_EXCEEDED",
                        message=f"Asset '{file_path}' exceeds the 5MB limit ({size_kb:.1f} KB).",
                        file_path=file_path
                    ))
                elif size_kb > 100:
                    all_warnings.append(ValidationIssue(
                        severity="warning",
                        code="ASSET_SIZE_HIGH",
                        message=f"Asset '{file_path}' is large ({size_kb:.1f} KB). Consider minifying.",
                        file_path=file_path
                    ))

        all_recommendations = list(dict.fromkeys(all_recommendations))
        score = max(0, 100 - (len(all_errors) * 20) - (len(all_warnings) * 4))

        return ComplianceReport(
            is_valid=len(all_errors) == 0,
            score=score,
            errors=all_errors,
            warnings=all_warnings,
            recommendations=all_recommendations,
            metadata={"total_files": len(files)}
        )
