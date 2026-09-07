# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_liquid_preview_engine"
# purpose: "Real-Time Liquid Preview Engine with Mock Store Context, Filter Pipeline, AST Interpreter & Tailwind v4 JIT Integration"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import re
import json
import time
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field

from apps.api.services.liquid_ast_compiler import (
    LiquidTokenizer,
    LiquidASTParser,
    LiquidASTCompiler,
    ASTNode,
    TemplateNode,
    TextNode,
    VariableNode,
    FilterNode,
    TagNode,
    BlockNode,
    BlockBranch,
    RawNode,
)
from apps.api.services.liquid_ast_optimizer import LiquidASTOptimizer
from apps.api.services.tailwind_v4_jit import TailwindV4JITCompiler, TailwindCompilationResult


@dataclass
class LiquidRenderResult:
    """Result of rendering a Liquid template/AST in real-time."""
    html: str
    css: str
    classes_used: List[str]
    execution_time_ms: float
    sections_rendered: List[str]
    snippets_rendered: List[str]
    schemas_extracted: Dict[str, Any]
    error: Optional[str] = None


class LiquidFilterEngine:
    """Standard Shopify Liquid filter implementation for the Preview Engine."""

    @staticmethod
    def apply_filter(val: Any, filter_node: FilterNode, context: Dict[str, Any]) -> Any:
        fname = filter_node.name.lower()
        args = [LiquidFilterEngine._resolve_arg(a, context) for a in filter_node.args]
        kwargs = getattr(filter_node, "kwargs", {}) or {}

        if fname == "upcase":
            return str(val).upper() if val is not None else ""
        elif fname == "downcase":
            return str(val).lower() if val is not None else ""
        elif fname == "capitalize":
            return str(val).capitalize() if val is not None else ""
        elif fname == "strip":
            return str(val).strip() if val is not None else ""
        elif fname == "escape":
            import html
            return html.escape(str(val)) if val is not None else ""
        elif fname == "money":
            try:
                num = float(val)
                if num > 1000 and isinstance(val, int):
                    num = num / 100.0
                return f"${num:,.2f}"
            except Exception:
                return str(val)
        elif fname == "money_without_currency":
            try:
                num = float(val)
                if num > 1000 and isinstance(val, int):
                    num = num / 100.0
                return f"{num:,.2f}"
            except Exception:
                return str(val)
        elif fname == "asset_url":
            return f"/assets/{val}"
        elif fname == "image_url":
            width = kwargs.get("width")
            if width:
                return f"https://cdn.shopify.com/s/files/1/{val}?width={width}"
            return f"https://cdn.shopify.com/s/files/1/{val}"
        elif fname == "default":
            default_val = args[0] if args else (kwargs.get("default") or "")
            if val is None or val == "" or val is False or val == [] or val == {}:
                return default_val
            return val
        elif fname == "plus":
            try:
                return float(val) + float(args[0])
            except Exception:
                return val
        elif fname == "minus":
            try:
                return float(val) - float(args[0])
            except Exception:
                return val
        elif fname == "times":
            try:
                return float(val) * float(args[0])
            except Exception:
                return val
        elif fname == "divided_by":
            try:
                divisor = float(args[0])
                return float(val) / divisor if divisor != 0 else 0
            except Exception:
                return val
        elif fname == "modulo":
            try:
                return float(val) % float(args[0])
            except Exception:
                return val
        elif fname == "size":
            try:
                return len(val)
            except Exception:
                return 0
        elif fname == "first":
            try:
                return val[0] if len(val) > 0 else None
            except Exception:
                return None
        elif fname == "last":
            try:
                return val[-1] if len(val) > 0 else None
            except Exception:
                return None
        elif fname == "join":
            delimiter = str(args[0]) if args else ", "
            try:
                return delimiter.join(str(x) for x in val)
            except Exception:
                return str(val)
        elif fname == "json":
            try:
                return json.dumps(val)
            except Exception:
                return "{}"
        elif fname == "truncate":
            try:
                length = int(args[0]) if args else 50
                s = str(val)
                return s[:length] + "..." if len(s) > length else s
            except Exception:
                return str(val)

        return val

    @staticmethod
    def _resolve_arg(arg: Any, context: Dict[str, Any]) -> Any:
        if isinstance(arg, str):
            arg_str = arg.strip()
            if (arg_str.startswith('"') and arg_str.endswith('"')) or (arg_str.startswith("'") and arg_str.endswith("'")):
                return arg_str[1:-1]
            if arg_str.lower() == "true":
                return True
            if arg_str.lower() == "false":
                return False
            try:
                if "." in arg_str and any(char.isdigit() for char in arg_str):
                    return float(arg_str)
                elif arg_str.isdigit() or (arg_str.startswith("-") and arg_str[1:].isdigit()):
                    return int(arg_str)
            except ValueError:
                pass

            res = LiquidPreviewEngine.resolve_lookup(arg_str, context)
            if res is not None:
                return res
            return arg_str
        return arg


class LiquidPreviewEngine:
    """
    High-Performance In-Memory Real-Time Liquid Preview & AST Rendering Engine.
    Processes Liquid AST, hydrates mock store objects, evaluates filters/tags,
    compiles on-demand Tailwind v4 JIT CSS, and outputs production-ready HTML.
    """

    DEFAULT_STORE_CONTEXT = {
        "shop": {
            "name": "DNK Luxury Store",
            "domain": "dnk-luxury.myshopify.com",
            "currency": "USD",
            "money_format": "${{amount}}",
            "email": "concierge@dnk-luxury.com"
        },
        "settings": {
            "primary_color": "#0f172a",
            "accent_color": "#3b82f6",
            "font_family": "Inter, sans-serif",
            "header_sticky": True,
            "show_announcement": True,
            "announcement_text": "✨ Free Worldwide Express Shipping on Orders Over $200"
        },
        "cart": {
            "item_count": 2,
            "total_price": 24900,
            "items": [
                {
                    "title": "DNK Cyber Stealth Jacket",
                    "price": 19900,
                    "quantity": 1,
                    "image": "cyber-jacket.png"
                },
                {
                    "title": "DNK Neural Beanie",
                    "price": 5000,
                    "quantity": 1,
                    "image": "neural-beanie.png"
                }
            ]
        },
        "product": {
            "id": 101,
            "title": "DNK Cyber Stealth Jacket",
            "description": "Engineered for urban stealth with adaptive weather shielding and integrated cyber-mesh.",
            "price": 19900,
            "compare_at_price": 24900,
            "available": True,
            "vendor": "DNK Lab",
            "type": "Outerwear",
            "tags": ["stealth", "cyberpunk", "featured"],
            "featured_image": "cyber-jacket.png",
            "images": ["cyber-jacket-1.png", "cyber-jacket-2.png"],
            "variants": [
                {"id": 1, "title": "S / Stealth Black", "available": True, "price": 19900},
                {"id": 2, "title": "M / Stealth Black", "available": True, "price": 19900},
                {"id": 3, "title": "L / Stealth Black", "available": False, "price": 19900}
            ]
        },
        "collection": {
            "id": 501,
            "title": "Stealth Outerwear 2026",
            "description": "High-velocity techwear designed for autonomous humans.",
            "products_count": 12,
            "all_tags": ["stealth", "waterproof", "thermal"]
        },
        "page": {
            "title": "About DNK OS",
            "content": "<p>Empowering hyper-scalable e-commerce and AI commerce experiences.</p>"
        }
    }

    def __init__(
        self,
        snippets: Optional[Dict[str, str]] = None,
        sections: Optional[Dict[str, str]] = None,
        theme_tokens: Optional[Dict[str, Any]] = None
    ):
        self.snippets = snippets or {}
        default_secs = {
            "hero": '<div class="hero bg-black text-white p-8"><h1 class="text-3xl font-extrabold">Welcome to DNK Cyber Luxury</h1></div>'
        }
        if sections:
            default_secs.update(sections)
        self.sections = default_secs
        self.optimizer = LiquidASTOptimizer()
        self.tailwind_compiler = TailwindV4JITCompiler(custom_theme_tokens=theme_tokens)

    def parse_source(self, source: str) -> TemplateNode:
        """Parses Liquid source string into TemplateNode AST."""
        parser = LiquidASTParser(source)
        return parser.parse()

    def register_snippet(self, name: str, source: str) -> None:
        """Registers a reusable Liquid snippet for {% render 'name' %}."""
        self.snippets[name] = source

    def register_section(self, name: str, source: str) -> None:
        """Registers a reusable Liquid section for {% section 'name' %}."""
        self.sections[name] = source

    @staticmethod
    def resolve_lookup(expr: str, context: Dict[str, Any]) -> Any:
        """Resolves dotted property paths like 'product.variants[0].title' or 'settings.primary_color'."""
        if not expr:
            return None
        
        expr = expr.strip()
        
        if (expr.startswith('"') and expr.endswith('"')) or (expr.startswith("'") and expr.endswith("'")):
            return expr[1:-1]
        if expr.lower() == "true":
            return True
        if expr.lower() == "false":
            return False
        if expr.lower() == "nil" or expr.lower() == "null":
            return None
        try:
            if "." in expr and not any(part.isdigit() for part in expr.split(".")):
                pass
            else:
                if "." in expr:
                    return float(expr)
                return int(expr)
        except ValueError:
            pass

        parts = expr.split(".")
        current: Any = context
        for part in parts:
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, (list, tuple)):
                try:
                    idx = int(part)
                    current = current[idx] if 0 <= idx < len(current) else None
                except ValueError:
                    return None
            else:
                return None

        return current

    def _eval_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluates Liquid boolean condition expressions."""
        if not condition:
            return False
        cond = condition.strip()

        for op in ["==", "!=", ">=", "<=", ">", "<", " contains "]:
            if op in cond:
                left_str, right_str = cond.split(op, 1)
                left_val = self.resolve_lookup(left_str.strip(), context)
                right_val = self.resolve_lookup(right_str.strip(), context)

                if op == "==":
                    return left_val == right_val
                elif op == "!=":
                    return left_val != right_val
                elif op == ">=":
                    return (left_val or 0) >= (right_val or 0)
                elif op == "<=":
                    return (left_val or 0) <= (right_val or 0)
                elif op == ">":
                    return (left_val or 0) > (right_val or 0)
                elif op == "<":
                    return (left_val or 0) < (right_val or 0)
                elif op == " contains ":
                    if left_val is None:
                        return False
                    if isinstance(left_val, (list, tuple, str)):
                        return right_val in left_val
                    return False

        val = self.resolve_lookup(cond, context)
        if val is None or val is False or val == "" or val == [] or val == {}:
            return False
        return True

    def render_node(
        self,
        node: ASTNode,
        context: Dict[str, Any],
        sections_rendered: List[str],
        snippets_rendered: List[str],
        schemas_extracted: Dict[str, Any]
    ) -> str:
        """Recursively renders AST nodes into HTML with current context."""
        if isinstance(node, TextNode):
            return getattr(node, "content", "") or getattr(node, "value", "") or getattr(node, "text", "")

        elif isinstance(node, RawNode):
            return getattr(node, "content", "") or getattr(node, "value", "")

        elif isinstance(node, VariableNode):
            val = self.resolve_lookup(node.expression, context)
            for f in node.filters:
                val = LiquidFilterEngine.apply_filter(val, f, context)
            return "" if val is None else str(val)

        elif isinstance(node, TagNode):
            tag_name = (node.tag_name or "").lower()

            if tag_name == "assign":
                raw_args = getattr(node, "raw_content", "") or node.attributes.get("raw", "") or ""
                match = re.match(r'([a-zA-Z0-9_-]+)\s*=\s*(.+)$', raw_args.strip())
                if match:
                    var_name, expr = match.group(1), match.group(2)
                    filter_parts = expr.split("|")
                    base_expr = filter_parts[0].strip()
                    val = self.resolve_lookup(base_expr, context)
                    for f_str in filter_parts[1:]:
                        f_str = f_str.strip()
                        f_name = f_str.split(":")[0].strip()
                        f_args = [a.strip() for a in f_str.split(":")[1].split(",")] if ":" in f_str else []
                        dummy_f = FilterNode(name=f_name, args=f_args, kwargs={})
                        val = LiquidFilterEngine.apply_filter(val, dummy_f, context)
                    context[var_name] = val
                return ""

            elif tag_name in ("render", "include"):
                raw_args = getattr(node, "raw_content", "") or ""
                args = raw_args.strip().split()
                if args:
                    snippet_name = args[0].strip("'\"")
                    snippets_rendered.append(snippet_name)
                    if snippet_name in self.snippets:
                        snippet_ast = self.parse_source(self.snippets[snippet_name])
                        snippet_ctx = dict(context)
                        return self.render_node(snippet_ast, snippet_ctx, sections_rendered, snippets_rendered, schemas_extracted)
                return f"<!-- [Render: Snippet '{raw_args}' Not Found] -->"

            elif tag_name == "section":
                raw_args = getattr(node, "raw_content", "") or ""
                args = raw_args.strip().split()
                if args:
                    section_name = args[0].strip("'\"")
                    sections_rendered.append(section_name)
                    if section_name in self.sections:
                        section_ast = self.parse_source(self.sections[section_name])
                        sec_ctx = dict(context)
                        rendered_inner = self.render_node(section_ast, sec_ctx, sections_rendered, snippets_rendered, schemas_extracted)
                        return f'<div class="shopify-section" id="shopify-section-{section_name}" data-shopify-section-id="{section_name}">\n{rendered_inner}\n</div>'
                return f"<!-- [Section: '{raw_args}'] -->"

            elif tag_name == "comment":
                return ""

            return ""

        elif isinstance(node, BlockNode):
            bname = (node.tag_name or "").lower()

            if bname == "if":
                condition = node.attributes.get("condition", "")
                if self._eval_condition(condition, context):
                    return "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in node.body)
                
                for branch in node.branches:
                    if branch.branch_type == "elsif":
                        branch_cond = branch.condition or ""
                        if self._eval_condition(branch_cond, context):
                            return "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in branch.body)
                    elif branch.branch_type == "else":
                        return "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in branch.body)
                return ""

            elif bname == "unless":
                condition = node.attributes.get("condition", "")
                if not self._eval_condition(condition, context):
                    return "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in node.body)
                for branch in node.branches:
                    if branch.branch_type == "else":
                        return "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in branch.body)
                return ""

            elif bname == "for":
                loop_var = node.attributes.get("loop_var") or node.attributes.get("item_var") or node.attributes.get("target_var") or node.attributes.get("target")
                collection_expr = node.attributes.get("collection") or node.attributes.get("collection_expr")

                if not loop_var or not collection_expr:
                    raw = getattr(node, "raw_content", "") or node.attributes.get("raw", "") or ""
                    m = re.search(r'([a-zA-Z0-9_-]+)\s+in\s+([a-zA-Z0-9_\.-]+)', raw)
                    if m:
                        loop_var = m.group(1)
                        collection_expr = m.group(2)

                if loop_var and collection_expr:
                    items = self.resolve_lookup(collection_expr, context)
                    if isinstance(items, (list, tuple)) and len(items) > 0:
                        output_chunks: List[str] = []
                        total = len(items)
                        for idx, item in enumerate(items):
                            loop_ctx = dict(context)
                            loop_ctx[loop_var] = item
                            loop_ctx["forloop"] = {
                                "index": idx + 1,
                                "index0": idx,
                                "first": (idx == 0),
                                "last": (idx == total - 1),
                                "length": total
                            }
                            for child in node.body:
                                output_chunks.append(self.render_node(child, loop_ctx, sections_rendered, snippets_rendered, schemas_extracted))
                        return "".join(output_chunks)
                    else:
                        for branch in node.branches:
                            if branch.branch_type == "else":
                                return "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in branch.body)
                return ""

            elif bname == "capture":
                var_name = node.attributes.get("var", "").strip() or node.attributes.get("variable", "").strip()
                if var_name:
                    captured_str = "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in node.body)
                    context[var_name] = captured_str
                return ""

            elif bname == "schema":
                raw_schema_text = "".join(getattr(child, "value", "") or getattr(child, "text", "") for child in node.body if isinstance(child, TextNode))
                try:
                    parsed_schema = json.loads(raw_schema_text.strip())
                    schemas_extracted[parsed_schema.get("name", "section_schema")] = parsed_schema
                except Exception:
                    pass
                return ""

            elif bname in ("style", "stylesheet"):
                inner_css = "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in node.body)
                return f"<style>\n{inner_css}\n</style>"

            elif bname == "javascript":
                inner_js = "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in node.body)
                return f"<script>\n{inner_js}\n</script>"

            return "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in node.body)

        elif isinstance(node, TemplateNode):
            return "".join(self.render_node(child, context, sections_rendered, snippets_rendered, schemas_extracted) for child in (node.children or []))

        return ""

    def render(
        self,
        template_or_ast: Union[str, ASTNode],
        context: Optional[Dict[str, Any]] = None,
        inject_tailwind_css: bool = True,
        optimize_ast: bool = True
    ) -> LiquidRenderResult:
        """
        Renders Liquid Template/AST with Tailwind v4 JIT compilation and context hydration.
        """
        start_time = time.perf_counter()
        active_context = dict(self.DEFAULT_STORE_CONTEXT)
        if context:
            active_context.update(context)

        sections_rendered: List[str] = []
        snippets_rendered: List[str] = []
        schemas_extracted: Dict[str, Any] = {}
        error_msg: Optional[str] = None

        try:
            if isinstance(template_or_ast, str):
                ast = self.parse_source(template_or_ast)
            elif isinstance(template_or_ast, TemplateNode):
                ast = template_or_ast
            elif isinstance(template_or_ast, ASTNode):
                ast = TemplateNode(children=[template_or_ast])
            else:
                ast = TemplateNode(children=[])

            if optimize_ast and isinstance(ast, TemplateNode):
                optimized_template, _stats = self.optimizer.optimize(ast)
                ast = optimized_template

            rendered_html = self.render_node(
                ast,
                active_context,
                sections_rendered,
                snippets_rendered,
                schemas_extracted
            )

            css_bundle = ""
            classes_used: List[str] = []

            if inject_tailwind_css:
                tailwind_res = self.tailwind_compiler.compile(ast, include_reset=False)
                css_bundle = tailwind_res.css
                classes_used = tailwind_res.classes_found

                if css_bundle.strip():
                    style_tag = f'\n<!-- DNK Tailwind v4 JIT Bundle -->\n<style id="dnk-tailwind-v4">\n{css_bundle}\n</style>\n'
                    if "</head>" in rendered_html:
                        rendered_html = rendered_html.replace("</head>", f"{style_tag}</head>", 1)
                    else:
                        rendered_html = f"{style_tag}{rendered_html}"

        except Exception as e:
            error_msg = f"Liquid Preview Render Error: {str(e)}"
            rendered_html = f'<div class="dnk-preview-error" style="background:#fee2e2;color:#991b1b;padding:16px;border-radius:8px;font-family:sans-serif;">\n  <h3>⚠️ Liquid Preview Error</h3>\n  <p>{error_msg}</p>\n</div>'
            css_bundle = ""
            classes_used = []

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return LiquidRenderResult(
            html=rendered_html,
            css=css_bundle,
            classes_used=classes_used,
            execution_time_ms=elapsed_ms,
            sections_rendered=sections_rendered,
            snippets_rendered=snippets_rendered,
            schemas_extracted=schemas_extracted,
            error=error_msg
        )
