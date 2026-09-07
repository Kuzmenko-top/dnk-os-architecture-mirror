# --- DNK-MRH-HEADER ---
# mrh_id: "services/dnk_shopify_builder/mechanical_transpiler.py"
# purpose: "Mechanical Transpiler converting Canvas visual nodes (HTML/Tailwind + Open Design Tokens) into Shopify OS 2.0 Liquid sections with schema and style blocks."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Set, Tuple

from services.dnk_shopify_builder.liquid_compiler import liquid_compiler


class DOMNode:
    """Lightweight AST Node representation for HTML/Liquid parsing and transpilation."""
    def __init__(self, tag: Optional[str] = None, attrs: Optional[List[Tuple[str, Optional[str]]]] = None, is_text: bool = False, text_content: str = ""):
        self.tag: Optional[str] = tag.lower() if tag else None
        self.attrs: Dict[str, str] = {k.lower(): (v or "") for k, v in (attrs or [])}
        self.is_text: bool = is_text
        self.text_content: str = text_content
        self.children: List['DOMNode'] = []
        self.parent: Optional['DOMNode'] = None
        self.extra_attributes_in_tag: List[str] = []

    def get_attr(self, name: str) -> Optional[str]:
        return self.attrs.get(name.lower())

    def set_attr(self, name: str, value: str) -> None:
        self.attrs[name.lower()] = value

    def add_child(self, child: 'DOMNode') -> None:
        child.parent = self
        self.children.append(child)

    def to_html(self) -> str:
        if self.is_text:
            return self.text_content

        if not self.tag:
            return "".join(child.to_html() for child in self.children)

        # Void elements in HTML
        void_elements = {"img", "input", "br", "hr", "meta", "link", "source", "area", "base", "col", "embed", "param", "track", "wbr"}

        # Build attribute string
        attr_parts = []
        for k, v in self.attrs.items():
            if v == "" and k in ("disabled", "checked", "readonly", "required", "autofocus", "multiple", "defer", "async"):
                attr_parts.append(k)
            else:
                attr_parts.append(f'{k}="{v}"')

        # Insert extra attributes (e.g. {{ block.shopify_attributes }})
        for extra in self.extra_attributes_in_tag:
            attr_parts.append(extra)

        attr_str = (" " + " ".join(attr_parts)) if attr_parts else ""

        if self.tag in void_elements and not self.children:
            return f"<{self.tag}{attr_str} />"

        inner_html = "".join(child.to_html() for child in self.children)
        return f"<{self.tag}{attr_str}>{inner_html}</{self.tag}>"


class DOMTreeBuilder(HTMLParser):
    """Builds a DOMNode tree from raw HTML string."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = DOMNode()
        self.current = self.root
        self.stack: List[DOMNode] = [self.root]

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        node = DOMNode(tag=tag, attrs=attrs)
        self.current.add_child(node)
        void_elements = {"img", "input", "br", "hr", "meta", "link", "source", "area", "base", "col", "embed", "param", "track", "wbr"}
        if tag.lower() not in void_elements:
            self.stack.append(node)
            self.current = node

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        # Pop stack until matching tag
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag_lower:
                self.stack = self.stack[:i]
                self.current = self.stack[-1]
                break

    def handle_data(self, data: str):
        if data:
            node = DOMNode(is_text=True, text_content=data)
            self.current.add_child(node)


class MechanicalTranspiler:
    """
    Mechanical Transpiler:
    Transpiles HTML / Tailwind components from Canvas visual nodes into Shopify OS 2.0 Liquid sections.
    - Extracts text nodes into {{ section.settings.<id> }}
    - Extracts repeating grid/card elements into {% for block in section.blocks %} with block schemas
    - Generates {% style %} scoped to #shopify-section-{{ section.id }} with Open Design Theme Tokens
    - Generates {% schema %} with settings, blocks, and presets
    """

    DEFAULT_THEME_TOKENS = {
        "accent": "#6366f1",
        "bgDark": "#0b0f19",
        "cardBg": "#111827",
        "borderColor": "rgba(255, 255, 255, 0.12)",
        "glowColor": "rgba(99, 102, 241, 0.35)",
        "accentGradient": "linear-gradient(135deg, #6366f1 0%, #a855f7 100%)",
        "textColor": "#f3f4f6",
        "textMuted": "#9ca3af"
    }

    def __init__(self):
        self.allocated_setting_ids: Set[str] = set()

    def _allocate_id(self, base_id: str, scope_ids: Optional[Set[str]] = None) -> str:
        allocated = scope_ids if scope_ids is not None else self.allocated_setting_ids
        safe_base = re.sub(r"[^a-zA-Z0-9_]", "_", base_id).lower().strip("_")
        if not safe_base:
            safe_base = "setting"
        candidate = safe_base
        counter = 2
        while candidate in allocated:
            candidate = f"{safe_base}_{counter}"
            counter += 1
        allocated.add(candidate)
        return candidate

    def transpile(
        self,
        html_content: str,
        section_name: str = "Canvas Transpiled Section",
        theme_tokens: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes full transpilation pipeline:
        Canvas Node HTML + Open Design Tokens -> Shopify OS 2.0 Liquid Section
        """
        self.allocated_setting_ids = set()
        opts = options or {}
        # Normalize theme tokens (support snake_case from OpenDesign tokens)
        normalized_user_tokens = {}
        if theme_tokens:
            for k, v in theme_tokens.items():
                if k in ("color_accent", "accent"):
                    normalized_user_tokens["accent"] = v
                elif k in ("bg_dark", "bgDark"):
                    normalized_user_tokens["bgDark"] = v
                elif k in ("bg_card", "cardBg", "card_bg"):
                    normalized_user_tokens["cardBg"] = v
                elif k in ("border_color", "borderColor"):
                    normalized_user_tokens["borderColor"] = v
                elif k in ("glow_color", "glowColor"):
                    normalized_user_tokens["glowColor"] = v
                elif k in ("accent_gradient", "accentGradient"):
                    normalized_user_tokens["accentGradient"] = v
                elif k in ("color_text", "text_color", "textColor"):
                    normalized_user_tokens["textColor"] = v
                elif k in ("text_muted", "textMuted"):
                    normalized_user_tokens["textMuted"] = v
                else:
                    normalized_user_tokens[k] = v

        tokens = {**self.DEFAULT_THEME_TOKENS, **normalized_user_tokens}

        # Parse DOM
        parser = DOMTreeBuilder()
        try:
            parser.feed(html_content)
        except Exception as e:
            # Fallback if raw text
            parser.feed(f"<div>{html_content}</div>")

        root = parser.root

        # Data collection for Schema
        section_settings: List[Dict[str, Any]] = []
        section_blocks: List[Dict[str, Any]] = []
        preset_settings: Dict[str, Any] = {}
        preset_blocks: List[Dict[str, Any]] = []

        # 1. Detect & Transpile Repeating Elements (Cards, Grids, Lists)
        repeating_detected = self._detect_and_transpile_repeating(root, section_blocks, preset_blocks)

        # 2. Transpile Section-level Text and Images
        self._transpile_section_level_nodes(root, section_settings, preset_settings)

        # 3. Build HTML Body
        liquid_body_raw = root.to_html().strip()

        # Wrap in section container if not already wrapped
        if not liquid_body_raw.startswith("<section"):
            liquid_body = f'<div id="shopify-section-{{{{ section.id }}}}" class="dnk-shopify-section">\n  {liquid_body_raw}\n</div>'
        else:
            liquid_body = liquid_body_raw

        # 4. Generate Open Design CSS Style Block
        css_content = self._generate_css_styles(tokens, opts.get("custom_css", ""))

        # 5. Generate {% schema %} block
        schema_dict = {
            "name": section_name,
            "tag": "section",
            "class": "dnk-canvas-section",
            "settings": section_settings,
        }
        if section_blocks:
            schema_dict["blocks"] = section_blocks

        preset_entry: Dict[str, Any] = {
            "name": section_name,
            "settings": preset_settings
        }
        if preset_blocks:
            preset_entry["blocks"] = preset_blocks

        schema_dict["presets"] = [preset_entry]

        # 6. Compile Section
        full_liquid = self._assemble_section_code(
            section_name=section_name,
            liquid_body=liquid_body,
            css_content=css_content,
            schema_dict=schema_dict
        )

        # 7. Validate with LiquidCompiler diagnostics
        diagnostics = liquid_compiler.validate_section_full(full_liquid)

        return {
            "success": diagnostics.get("is_valid", False) or len(diagnostics.get("errors", [])) == 0,
            "section_name": section_name,
            "liquid": full_liquid,
            "liquid_code": full_liquid,
            "liquid_body": liquid_body,
            "full_liquid_template": full_liquid,
            "css": css_content,
            "schema": schema_dict,
            "schema_json": json.dumps(schema_dict, indent=2),
            "settings": section_settings,
            "blocks": section_blocks,
            "settings_count": len(section_settings),
            "blocks_count": len(section_blocks),
            "repeating_elements_detected": repeating_detected,
            "is_valid": diagnostics.get("is_valid", True),
            "errors": diagnostics.get("errors", []),
            "warnings": diagnostics.get("warnings", []),
            "diagnostics": diagnostics,
            "theme_tokens": tokens,
        }

    def _detect_and_transpile_repeating(
        self,
        node: DOMNode,
        section_blocks: List[Dict[str, Any]],
        preset_blocks: List[Dict[str, Any]]
    ) -> bool:
        """
        Scans DOM tree for repeating sibling elements (like cards, list items, grid columns),
        replaces them with a single {% for block in section.blocks %} loop,
        and injects {{ block.shopify_attributes }}.
        """
        found_any = False

        # Check children of this node
        children = [c for c in node.children if not c.is_text or c.text_content.strip()]
        element_children = [c for c in children if not c.is_text and c.tag]

        if len(element_children) >= 2:
            # Check if elements look like repeating cards
            # Condition: same tag and similar class or marked with data-block / card class
            first = element_children[0]
            first_cls = first.get_attr("class") or ""
            is_repeating = False

            if first.get_attr("data-block") or first.get_attr("data-shopify-block"):
                is_repeating = True
            elif first.tag in ("li", "article"):
                is_repeating = all(c.tag == first.tag for c in element_children)
            elif "card" in first_cls or "col" in first_cls or "item" in first_cls or "grid" in first_cls:
                is_repeating = all(c.tag == first.tag for c in element_children)

            if is_repeating:
                block_type = first.get_attr("data-block-type") or "card"
                block_type_clean = re.sub(r"[^a-zA-Z0-9_]", "_", block_type).lower()
                
                # Transpile the template block
                template_node = element_children[0]
                block_settings: List[Dict[str, Any]] = []
                block_preset_settings: Dict[str, Any] = {}
                block_scope_ids: Set[str] = set()

                self._transpile_block_level_nodes(template_node, block_settings, block_preset_settings, block_scope_ids)

                # Ensure {{ block.shopify_attributes }} is injected in opening tag
                template_node.extra_attributes_in_tag.append("{{ block.shopify_attributes }}")

                block_html = template_node.to_html()

                # Build the Liquid For-Loop
                liquid_loop = (
                    f"{{% for block in section.blocks %}}\n"
                    f"  {{% case block.type %}}\n"
                    f"    {{% when '{block_type_clean}' %}}\n"
                    f"      {block_html}\n"
                    f"  {{% endcase %}}\n"
                    f"{{% endfor %}}"
                )

                # Replace children of node with the liquid loop
                loop_node = DOMNode(is_text=True, text_content=liquid_loop)
                node.children = [loop_node]

                # Register block in schema
                section_blocks.append({
                    "type": block_type_clean,
                    "name": block_type.capitalize(),
                    "settings": block_settings
                })

                # Register preset blocks (one for each original repeating child, up to 4)
                for _ in element_children[:3]:
                    preset_blocks.append({
                        "type": block_type_clean,
                        "settings": block_preset_settings
                    })

                return True

        # Recurse into children
        for child in node.children:
            if not child.is_text:
                if self._detect_and_transpile_repeating(child, section_blocks, preset_blocks):
                    found_any = True

        return found_any

    def _transpile_block_level_nodes(
        self,
        node: DOMNode,
        block_settings: List[Dict[str, Any]],
        block_preset_settings: Dict[str, Any],
        scope_ids: Set[str]
    ) -> None:
        """Transpiles nodes inside a repeatable block into {{ block.settings.<id> }}."""
        if node.is_text:
            return

        tag = node.tag
        # 1. Images
        if tag == "img":
            setting_id = self._allocate_id("image", scope_ids)
            node.set_attr("src", f"{{{{ block.settings.{setting_id} | image_url: width: 600 }}}}")
            block_settings.append({
                "type": "image_picker",
                "id": setting_id,
                "label": "Card Image"
            })
            return

        # 2. Headings
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = self._get_text_content(node).strip()
            if text and not text.startswith("{{"):
                setting_id = self._allocate_id("title", scope_ids)
                self._replace_inner_text(node, f"{{{{ block.settings.{setting_id} | default: '{text}' }}}}")
                block_settings.append({
                    "type": "text",
                    "id": setting_id,
                    "label": f"Block {tag.upper()} Title",
                    "default": text
                })
                block_preset_settings[setting_id] = text
                return

        # 3. Paragraphs & Text
        if tag in ("p", "span"):
            text = self._get_text_content(node).strip()
            if text and len(text) > 2 and not text.startswith("{{"):
                setting_id = self._allocate_id("text", scope_ids)
                self._replace_inner_text(node, f"{{{{ block.settings.{setting_id} | default: '{text}' }}}}")
                block_settings.append({
                    "type": "textarea" if len(text) > 40 else "text",
                    "id": setting_id,
                    "label": "Block Text",
                    "default": text
                })
                block_preset_settings[setting_id] = text
                return

        # 4. Buttons / Links
        if tag in ("button", "a"):
            text = self._get_text_content(node).strip()
            if text and not text.startswith("{{"):
                setting_id = self._allocate_id("button_label", scope_ids)
                self._replace_inner_text(node, f"{{{{ block.settings.{setting_id} | default: '{text}' }}}}")
                block_settings.append({
                    "type": "text",
                    "id": setting_id,
                    "label": "Button Label",
                    "default": text
                })
                block_preset_settings[setting_id] = text

                if tag == "a":
                    link_id = self._allocate_id("button_link", scope_ids)
                    node.set_attr("href", f"{{{{ block.settings.{link_id} }}}}")
                    block_settings.append({
                        "type": "url",
                        "id": link_id,
                        "label": "Button Link"
                    })
                return

        for child in list(node.children):
            self._transpile_block_level_nodes(child, block_settings, block_preset_settings, scope_ids)

    def _transpile_section_level_nodes(
        self,
        node: DOMNode,
        section_settings: List[Dict[str, Any]],
        preset_settings: Dict[str, Any]
    ) -> None:
        """Transpiles top-level section text, images, and buttons into {{ section.settings.<id> }}."""
        if node.is_text:
            return

        tag = node.tag

        # 1. Images
        if tag == "img":
            setting_id = self._allocate_id("image")
            node.set_attr("src", f"{{{{ section.settings.{setting_id} | image_url: width: 1200 }}}}")
            section_settings.append({
                "type": "image_picker",
                "id": setting_id,
                "label": "Section Image"
            })
            return

        # 2. Headings
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = self._get_text_content(node).strip()
            if text and not text.startswith("{{") and not "{%" in text:
                setting_id = self._allocate_id("heading" if tag in ("h1", "h2") else "subheading")
                self._replace_inner_text(node, f"{{{{ section.settings.{setting_id} | default: '{text}' }}}}")
                section_settings.append({
                    "type": "text",
                    "id": setting_id,
                    "label": f"Section {tag.upper()} Heading",
                    "default": text
                })
                preset_settings[setting_id] = text
                return

        # 3. Paragraphs
        if tag == "p":
            text = self._get_text_content(node).strip()
            if text and not text.startswith("{{") and not "{%" in text:
                setting_id = self._allocate_id("description")
                self._replace_inner_text(node, f"{{{{ section.settings.{setting_id} | default: '{text}' }}}}")
                section_settings.append({
                    "type": "textarea" if len(text) > 40 else "text",
                    "id": setting_id,
                    "label": "Section Description",
                    "default": text
                })
                preset_settings[setting_id] = text
                return

        # 4. Buttons / Action links
        if tag in ("button", "a"):
            text = self._get_text_content(node).strip()
            if text and not text.startswith("{{") and not "{%" in text:
                label_id = self._allocate_id("button_label")
                self._replace_inner_text(node, f"{{{{ section.settings.{label_id} | default: '{text}' }}}}")
                section_settings.append({
                    "type": "text",
                    "id": label_id,
                    "label": "Button Label",
                    "default": text
                })
                preset_settings[label_id] = text

                if tag == "a":
                    link_id = self._allocate_id("button_link")
                    node.set_attr("href", f"{{{{ section.settings.{link_id} }}}}")
                    section_settings.append({
                        "type": "url",
                        "id": link_id,
                        "label": "Button Link"
                    })
                return

        for child in list(node.children):
            self._transpile_section_level_nodes(child, section_settings, preset_settings)

    def _get_text_content(self, node: DOMNode) -> str:
        if node.is_text:
            return node.text_content
        return "".join(self._get_text_content(c) for c in node.children)

    def _replace_inner_text(self, node: DOMNode, new_text: str) -> None:
        node.children = [DOMNode(is_text=True, text_content=new_text)]

    def _generate_css_styles(self, tokens: Dict[str, Any], custom_css: str = "") -> str:
        """Builds scoped CSS block with Open Design Theme CSS custom properties."""
        accent = tokens.get("accent") or tokens.get("color_accent") or "#6366f1"
        bg = tokens.get("bgDark") or tokens.get("bg_dark") or tokens.get("bg_card") or "#0b0f19"
        card_bg = tokens.get("cardBg") or tokens.get("bg_card") or "#111827"
        border = tokens.get("borderColor") or tokens.get("border_color") or "rgba(255, 255, 255, 0.12)"
        glow = tokens.get("glowColor") or tokens.get("glow_color") or "rgba(99, 102, 241, 0.35)"
        gradient = tokens.get("accentGradient") or tokens.get("accent_gradient") or "linear-gradient(135deg, #6366f1 0%, #a855f7 100%)"
        text = tokens.get("textColor") or tokens.get("color_text") or tokens.get("text_color") or "#f3f4f6"
        text_muted = tokens.get("textMuted") or tokens.get("text_muted") or "#9ca3af"

        css_lines = [
            f"#shopify-section-{{{{ section.id }}}} {{",
            f"  --dnk-accent: {accent};",
            f"  --dnk-bg: {bg};",
            f"  --dnk-card-bg: {card_bg};",
            f"  --dnk-border: {border};",
            f"  --dnk-glow: {glow};",
            f"  --dnk-accent-gradient: {gradient};",
            f"  --dnk-text: {text};",
            f"  --dnk-text-muted: {text_muted};",
            f"  position: relative;",
            f"  width: 100%;",
            f"}}",
        ]
        if custom_css:
            css_lines.append(custom_css.strip())

        return "\n".join(css_lines)

    def _assemble_section_code(
        self,
        section_name: str,
        liquid_body: str,
        css_content: str,
        schema_dict: Dict[str, Any]
    ) -> str:
        """Assembles standard Shopify OS 2.0 .liquid section string."""
        parts = [
            f"{{% comment %}}\n  DNK OS Transpiled Section: {section_name}\n  Generated by Mechanical Transpiler (Canvas -> Liquid AST)\n{{% endcomment %}}",
        ]
        if css_content:
            parts.append(f"{{% style %}}\n{css_content.strip()}\n{{% endstyle %}}")

        parts.append(liquid_body.strip())

        schema_json_str = json.dumps(schema_dict, indent=2, ensure_ascii=False)
        parts.append(f"{{% schema %}}\n{schema_json_str}\n{{% endschema %}}")

        return "\n\n".join(parts) + "\n"


mechanical_transpiler = MechanicalTranspiler()
