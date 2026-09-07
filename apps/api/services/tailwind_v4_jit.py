# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_tailwind_v4_jit"
# purpose: "Tailwind v4 JIT Compiler & Utility Class Extractor for Liquid Theme AST with Shopify Token Mapping"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import re
from typing import List, Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass, field

from apps.api.services.liquid_ast_compiler import (
    ASTNode,
    TemplateNode,
    TextNode,
    VariableNode,
    FilterNode,
    TagNode,
    BlockNode,
)


@dataclass
class TailwindCompilationResult:
    """Result of Tailwind v4 JIT Compilation."""
    css: str
    classes_found: List[str]
    rules_generated: int
    css_size_bytes: int
    execution_time_ms: float = 0.0


class TailwindV4JITCompiler:
    """
    Tailwind CSS v4 JIT Compilation Engine for Shopify Liquid AST.
    Extracts utility classes from Liquid AST nodes, generates atomic CSS rules,
    and supports theme tokens and arbitrary values.
    """

    COLOR_MAP = {
        "white": "#ffffff",
        "black": "#000000",
        "transparent": "transparent",
        "current": "currentColor",
        "gray-50": "#f9fafb",
        "gray-100": "#f3f4f6",
        "gray-200": "#e5e7eb",
        "gray-300": "#d1d5db",
        "gray-400": "#9ca3af",
        "gray-500": "#6b7280",
        "gray-600": "#4b5563",
        "gray-700": "#374151",
        "gray-800": "#1f2937",
        "gray-900": "#111827",
        "red-500": "#ef4444",
        "red-600": "#dc2626",
        "green-500": "#22c55e",
        "green-600": "#16a34a",
        "blue-500": "#3b82f6",
        "blue-600": "#2563eb",
        "indigo-500": "#6366f1",
        "indigo-600": "#4f46e5",
        "primary": "var(--color-primary, #0f172a)",
        "secondary": "var(--color-secondary, #64748b)",
        "accent": "var(--color-accent, #3b82f6)",
    }

    SPACING_MAP = {
        "0": "0px",
        "0.5": "0.125rem",
        "1": "0.25rem",
        "1.5": "0.375rem",
        "2": "0.5rem",
        "2.5": "0.625rem",
        "3": "0.75rem",
        "3.5": "0.875rem",
        "4": "1rem",
        "5": "1.25rem",
        "6": "1.5rem",
        "7": "1.75rem",
        "8": "2rem",
        "9": "2.25rem",
        "10": "2.5rem",
        "12": "3rem",
        "14": "3.5rem",
        "16": "4rem",
        "20": "5rem",
        "24": "6rem",
        "32": "8rem",
        "auto": "auto",
        "full": "100%",
        "screen": "100vh",
    }

    BREAKPOINTS = {
        "sm": "640px",
        "md": "768px",
        "lg": "1024px",
        "xl": "1280px",
        "2xl": "1536px",
    }

    def __init__(self, custom_theme_tokens: Optional[Dict[str, Any]] = None):
        self.theme_tokens: Dict[str, Any] = custom_theme_tokens or {}
        custom_colors: Dict[str, str] = {}
        if isinstance(self.theme_tokens.get("colors"), dict):
            custom_colors = {str(k): str(v) for k, v in self.theme_tokens["colors"].items()}
        
        custom_spacing: Dict[str, str] = {}
        if isinstance(self.theme_tokens.get("spacing"), dict):
            custom_spacing = {str(k): str(v) for k, v in self.theme_tokens["spacing"].items()}

        self.color_map = {**self.COLOR_MAP, **custom_colors}
        self.spacing_map = {**self.SPACING_MAP, **custom_spacing}

    def extract_classes_from_ast(self, node: ASTNode) -> Set[str]:
        """Traverses Liquid AST and extracts potential CSS class names."""
        classes: Set[str] = set()

        def _traverse(n: ASTNode):
            if isinstance(n, TextNode):
                # Extract classes from class="..." and class='...'
                raw_text = getattr(n, "content", "") or getattr(n, "value", "") or getattr(n, "text", "")
                matches = re.findall(r'class=["\']([^"\']+)["\']', raw_text)
                for match in matches:
                    # Ignore liquid tags inside class attribute
                    cleaned = re.sub(r'\{[{%].*?[%}]\}', '', match)
                    for cls in cleaned.split():
                        if cls and not cls.startswith("{") and not cls.endswith("}"):
                            classes.add(cls.strip())
            elif isinstance(n, TagNode):
                # Check for class attributes in tag parameters if any
                for val in n.attributes.values():
                    if isinstance(val, str):
                        for cls in val.split():
                            if cls and not cls.startswith("{"):
                                classes.add(cls.strip())
            elif isinstance(n, BlockNode):
                for child in n.body:
                    _traverse(child)
                for branch in n.branches:
                    for child in branch.body:
                        _traverse(child)
            elif isinstance(n, TemplateNode):
                for child in (n.children or []):
                    _traverse(child)

        _traverse(node)
        return classes

    def extract_classes_from_source(self, source: str) -> Set[str]:
        """Extracts CSS classes directly from Liquid/HTML source string."""
        classes: Set[str] = set()
        matches = re.findall(r'class=["\']([^"\']+)["\']', source)
        for match in matches:
            cleaned = re.sub(r'\{[{%].*?[%}]\}', '', match)
            for cls in cleaned.split():
                cls = cls.strip()
                if cls and not cls.startswith("{") and not cls.endswith("}"):
                    classes.add(cls)
        return classes

    def _escape_selector(self, cls: str) -> str:
        """Escapes special characters in class name for CSS selector."""
        return re.sub(r'([:\.\[\]\/#%])', r'\\\1', cls)

    def _generate_rule_for_class(self, cls: str) -> Optional[Tuple[str, Optional[str]]]:
        """
        Parses a single Tailwind utility class and generates (css_rule, media_query_or_none).
        Returns None if class is not a recognized Tailwind utility.
        """
        prefix = ""
        media_query = None
        pseudo_class = None
        working_cls = cls

        # Handle responsive and state variants (e.g. md:hover:flex, lg:text-center)
        variants = working_cls.split(":")
        if len(variants) > 1:
            working_cls = variants[-1]
            for v in variants[:-1]:
                if v in self.BREAKPOINTS:
                    media_query = f"@media (min-width: {self.BREAKPOINTS[v]})"
                elif v in ("hover", "focus", "active", "focus-within", "focus-visible", "disabled"):
                    pseudo_class = f":{v}"
                elif v == "group-hover":
                    pseudo_class = " .group:hover &"

        selector = f".{self._escape_selector(cls)}"
        if pseudo_class:
            if pseudo_class.startswith(" "):
                selector = f".group:hover .{self._escape_selector(cls)}"
            else:
                selector = f"{selector}{pseudo_class}"

        # 1. Arbitrary Values: w-[100px], bg-[#ff0000], text-[14px], etc.
        arb_match = re.match(r'^([a-z-]+)-\[([^\]]+)\]$', working_cls)
        if arb_match:
            prop_prefix, val = arb_match.group(1), arb_match.group(2)
            rule_body = None
            if prop_prefix == "w":
                rule_body = f"width: {val};"
            elif prop_prefix == "h":
                rule_body = f"height: {val};"
            elif prop_prefix == "bg":
                rule_body = f"background-color: {val};"
            elif prop_prefix == "text":
                rule_body = f"color: {val};" if re.match(r'^(#|rgb|hsl|var)', val) else f"font-size: {val};"
            elif prop_prefix == "p":
                rule_body = f"padding: {val};"
            elif prop_prefix == "m":
                rule_body = f"margin: {val};"
            elif prop_prefix == "top":
                rule_body = f"top: {val};"
            elif prop_prefix == "bottom":
                rule_body = f"bottom: {val};"
            elif prop_prefix == "left":
                rule_body = f"left: {val};"
            elif prop_prefix == "right":
                rule_body = f"right: {val};"
            elif prop_prefix == "z":
                rule_body = f"z-index: {val};"
            elif prop_prefix == "gap":
                rule_body = f"gap: {val};"

            if rule_body:
                return (f"{selector} {{ {rule_body} }}", media_query)

        # 2. Display & Layout
        display_map = {
            "block": "display: block;",
            "inline-block": "display: inline-block;",
            "inline": "display: inline;",
            "flex": "display: flex;",
            "inline-flex": "display: inline-flex;",
            "grid": "display: grid;",
            "inline-grid": "display: inline-grid;",
            "hidden": "display: none;",
        }
        if working_cls in display_map:
            return (f"{selector} {{ {display_map[working_cls]} }}", media_query)

        # 3. Flex & Grid Properties
        flex_map = {
            "flex-row": "flex-direction: row;",
            "flex-row-reverse": "flex-direction: row-reverse;",
            "flex-col": "flex-direction: column;",
            "flex-col-reverse": "flex-direction: column-reverse;",
            "flex-wrap": "flex-wrap: wrap;",
            "flex-nowrap": "flex-wrap: nowrap;",
            "flex-1": "flex: 1 1 0%;",
            "flex-auto": "flex: 1 1 auto;",
            "flex-initial": "flex: 0 1 auto;",
            "flex-none": "flex: none;",
            "items-start": "align-items: flex-start;",
            "items-end": "align-items: flex-end;",
            "items-center": "align-items: center;",
            "items-baseline": "align-items: baseline;",
            "items-stretch": "align-items: stretch;",
            "justify-start": "justify-content: flex-start;",
            "justify-end": "justify-content: flex-end;",
            "justify-center": "justify-content: center;",
            "justify-between": "justify-content: space-between;",
            "justify-around": "justify-content: space-around;",
            "justify-evenly": "justify-content: space-evenly;",
        }
        if working_cls in flex_map:
            return (f"{selector} {{ {flex_map[working_cls]} }}", media_query)

        # Grid Columns
        grid_cols_match = re.match(r'^grid-cols-(\d+)$', working_cls)
        if grid_cols_match:
            cols = grid_cols_match.group(1)
            return (f"{selector} {{ grid-template-columns: repeat({cols}, minmax(0, 1fr)); }}", media_query)

        # 4. Spacing (Padding, Margin, Gap)
        # Margin
        m_match = re.match(r'^(m|mx|my|mt|mr|mb|ml)-([0-9\.]+|auto|full)$', working_cls)
        if m_match:
            side, val_key = m_match.group(1), m_match.group(2)
            val = self.spacing_map.get(val_key, f"{val_key}rem")
            prop_dict = {
                "m": f"margin: {val};",
                "mx": f"margin-left: {val}; margin-right: {val};",
                "my": f"margin-top: {val}; margin-bottom: {val};",
                "mt": f"margin-top: {val};",
                "mr": f"margin-right: {val};",
                "mb": f"margin-bottom: {val};",
                "ml": f"margin-left: {val};",
            }
            return (f"{selector} {{ {prop_dict[side]} }}", media_query)

        # Padding
        p_match = re.match(r'^(p|px|py|pt|pr|pb|pl)-([0-9\.]+|auto|full)$', working_cls)
        if p_match:
            side, val_key = p_match.group(1), p_match.group(2)
            val = self.spacing_map.get(val_key, f"{val_key}rem")
            prop_dict = {
                "p": f"padding: {val};",
                "px": f"padding-left: {val}; padding-right: {val};",
                "py": f"padding-top: {val}; padding-bottom: {val};",
                "pt": f"padding-top: {val};",
                "pr": f"padding-right: {val};",
                "pb": f"padding-bottom: {val};",
                "pl": f"padding-left: {val};",
            }
            return (f"{selector} {{ {prop_dict[side]} }}", media_query)

        # Gap
        gap_match = re.match(r'^gap-([0-9\.]+)$', working_cls)
        if gap_match:
            val = self.spacing_map.get(gap_match.group(1), f"{gap_match.group(1)}rem")
            return (f"{selector} {{ gap: {val}; }}", media_query)

        # 5. Sizing (Width, Height, Max-Width)
        w_match = re.match(r'^(w|h|max-w|min-h)-([a-z0-9\.\/]+)$', working_cls)
        if w_match:
            prop_type, val_key = w_match.group(1), w_match.group(2)
            val = self.spacing_map.get(val_key)
            if not val:
                if val_key == "full":
                    val = "100%"
                elif val_key == "screen":
                    val = "100vh" if prop_type in ("h", "min-h") else "100vw"
                elif "/" in val_key:
                    num, den = val_key.split("/")
                    val = f"{(float(num) / float(den)) * 100:.6f}%"
                elif val_key in ("xs", "sm", "md", "lg", "xl", "2xl", "3xl", "4xl", "5xl", "6xl", "7xl"):
                    sizes = {
                        "xs": "20rem", "sm": "24rem", "md": "28rem", "lg": "32rem",
                        "xl": "36rem", "2xl": "42rem", "3xl": "48rem", "4xl": "56rem",
                        "5xl": "64rem", "6xl": "72rem", "7xl": "80rem"
                    }
                    val = sizes.get(val_key, "100%")

            if val:
                prop_name = {
                    "w": "width",
                    "h": "height",
                    "max-w": "max-width",
                    "min-h": "min-height",
                }[prop_type]
                return (f"{selector} {{ {prop_name}: {val}; }}", media_query)

        # 6. Typography
        text_size_map = {
            "text-xs": "font-size: 0.75rem; line-height: 1rem;",
            "text-sm": "font-size: 0.875rem; line-height: 1.25rem;",
            "text-base": "font-size: 1rem; line-height: 1.5rem;",
            "text-lg": "font-size: 1.125rem; line-height: 1.75rem;",
            "text-xl": "font-size: 1.25rem; line-height: 1.75rem;",
            "text-2xl": "font-size: 1.5rem; line-height: 2rem;",
            "text-3xl": "font-size: 1.875rem; line-height: 2.25rem;",
            "text-4xl": "font-size: 2.25rem; line-height: 2.5rem;",
            "text-5xl": "font-size: 3rem; line-height: 1;",
        }
        if working_cls in text_size_map:
            return (f"{selector} {{ {text_size_map[working_cls]} }}", media_query)

        font_weight_map = {
            "font-thin": "font-weight: 100;",
            "font-light": "font-weight: 300;",
            "font-normal": "font-weight: 400;",
            "font-medium": "font-weight: 500;",
            "font-semibold": "font-weight: 600;",
            "font-bold": "font-weight: 700;",
            "font-extrabold": "font-weight: 800;",
            "font-black": "font-weight: 900;",
        }
        if working_cls in font_weight_map:
            return (f"{selector} {{ {font_weight_map[working_cls]} }}", media_query)

        text_align_map = {
            "text-left": "text-align: left;",
            "text-center": "text-align: center;",
            "text-right": "text-align: right;",
            "text-justify": "text-align: justify;",
            "uppercase": "text-transform: uppercase;",
            "lowercase": "text-transform: lowercase;",
            "capitalize": "text-transform: capitalize;",
            "truncate": "overflow: hidden; text-overflow: ellipsis; white-space: nowrap;",
        }
        if working_cls in text_align_map:
            return (f"{selector} {{ {text_align_map[working_cls]} }}", media_query)

        # 7. Colors (Text, Background, Border)
        # Background Colors
        bg_color_match = re.match(r'^bg-([a-z0-9-]+)$', working_cls)
        if bg_color_match:
            color_name = bg_color_match.group(1)
            if color_name in self.color_map:
                return (f"{selector} {{ background-color: {self.color_map[color_name]}; }}", media_query)

        # Text Colors
        text_color_match = re.match(r'^text-([a-z0-9-]+)$', working_cls)
        if text_color_match:
            color_name = text_color_match.group(1)
            if color_name in self.color_map:
                return (f"{selector} {{ color: {self.color_map[color_name]}; }}", media_query)

        # Border Colors
        border_color_match = re.match(r'^border-([a-z0-9-]+)$', working_cls)
        if border_color_match:
            color_name = border_color_match.group(1)
            if color_name in self.color_map:
                return (f"{selector} {{ border-color: {self.color_map[color_name]}; }}", media_query)

        # 8. Borders & Rounded Corners
        rounded_map = {
            "rounded-none": "border-radius: 0px;",
            "rounded-sm": "border-radius: 0.125rem;",
            "rounded": "border-radius: 0.25rem;",
            "rounded-md": "border-radius: 0.375rem;",
            "rounded-lg": "border-radius: 0.5rem;",
            "rounded-xl": "border-radius: 0.75rem;",
            "rounded-2xl": "border-radius: 1rem;",
            "rounded-full": "border-radius: 9999px;",
        }
        if working_cls in rounded_map:
            return (f"{selector} {{ {rounded_map[working_cls]} }}", media_query)

        border_width_map = {
            "border": "border-width: 1px;",
            "border-0": "border-width: 0px;",
            "border-2": "border-width: 2px;",
            "border-4": "border-width: 4px;",
            "border-8": "border-width: 8px;",
            "border-t": "border-top-width: 1px;",
            "border-b": "border-bottom-width: 1px;",
            "border-l": "border-left-width: 1px;",
            "border-r": "border-right-width: 1px;",
        }
        if working_cls in border_width_map:
            return (f"{selector} {{ {border_width_map[working_cls]} }}", media_query)

        # 9. Shadows & Effects
        shadow_map = {
            "shadow-sm": "box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);",
            "shadow": "box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);",
            "shadow-md": "box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);",
            "shadow-lg": "box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);",
            "shadow-none": "box-shadow: none;",
        }
        if working_cls in shadow_map:
            return (f"{selector} {{ {shadow_map[working_cls]} }}", media_query)

        # Transition & Animation
        trans_map = {
            "transition": "transition-property: color, background-color, border-color, text-decoration-color, fill, stroke, opacity, box-shadow, transform, filter, backdrop-filter; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 150ms;",
            "transition-all": "transition-property: all; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); transition-duration: 150ms;",
            "duration-150": "transition-duration: 150ms;",
            "duration-200": "transition-duration: 200ms;",
            "duration-300": "transition-duration: 300ms;",
            "duration-500": "transition-duration: 500ms;",
            "ease-in-out": "transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);",
            "cursor-pointer": "cursor: pointer;",
        }
        if working_cls in trans_map:
            return (f"{selector} {{ {trans_map[working_cls]} }}", media_query)

        return None

    def compile(
        self,
        ast_or_classes_or_source: Any,
        include_reset: bool = True
    ) -> TailwindCompilationResult:
        """
        Compiles Tailwind v4 utility CSS from AST, source string, or set of classes.
        """
        import time
        start_time = time.perf_counter()

        classes_to_compile: Set[str] = set()

        if isinstance(ast_or_classes_or_source, (TemplateNode, ASTNode)):
            classes_to_compile = self.extract_classes_from_ast(ast_or_classes_or_source)
        elif isinstance(ast_or_classes_or_source, (set, list)):
            classes_to_compile = set(ast_or_classes_or_source)
        elif isinstance(ast_or_classes_or_source, str):
            classes_to_compile = self.extract_classes_from_source(ast_or_classes_or_source)

        base_rules: List[str] = []
        media_rules: Dict[str, List[str]] = {}
        rules_count = 0

        # Optional Tailwind v4 Preflight / Reset
        if include_reset:
            base_rules.append("*, ::before, ::after { box-sizing: border-box; border-width: 0; border-style: solid; }")
            base_rules.append("html { line-height: 1.5; -webkit-text-size-adjust: 100%; font-family: ui-sans-serif, system-ui, sans-serif; }")
            base_rules.append("body { margin: 0; line-height: inherit; }")

        for cls in sorted(list(classes_to_compile)):
            res = self._generate_rule_for_class(cls)
            if res:
                rule, mq = res
                if mq:
                    if mq not in media_rules:
                        media_rules[mq] = []
                    media_rules[mq].append(rule)
                else:
                    base_rules.append(rule)
                rules_count += 1

        # Format Final CSS
        css_lines = list(base_rules)
        for mq, rules in sorted(media_rules.items()):
            inner = "\n  ".join(rules)
            css_lines.append(f"{mq} {{\n  {inner}\n}}")

        final_css = "\n".join(css_lines)
        size_bytes = len(final_css.encode("utf-8"))
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return TailwindCompilationResult(
            css=final_css,
            classes_found=sorted(list(classes_to_compile)),
            rules_generated=rules_count,
            css_size_bytes=size_bytes,
            execution_time_ms=elapsed_ms
        )
