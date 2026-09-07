# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/liquid_ast_optimizer.py"
# purpose: "Shopify Liquid AST Optimization Pipeline: Tree-Shaking, Dead Code Elimination, Asset Minification & Vite Plugin Integration."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-ECOM-003"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym / Gerych Prime"
# --- END DNK-MRH-HEADER ---

import re
import json
import time
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field

from apps.api.services.liquid_ast_compiler import (
    ASTNode,
    TemplateNode,
    TextNode,
    VariableNode,
    FilterNode,
    TagNode,
    BlockNode,
    BlockBranch,
    RawNode,
    LiquidASTParser,
    LiquidTokenizer,
    LiquidASTCompiler,
)


@dataclass
class OptimizationStats:
    original_nodes_count: int = 0
    optimized_nodes_count: int = 0
    nodes_eliminated: int = 0
    original_size_bytes: int = 0
    optimized_size_bytes: int = 0
    reduction_pct: float = 0.0
    dead_branches_pruned: int = 0
    unused_assigns_pruned: int = 0
    snippets_referenced: List[str] = field(default_factory=list)
    snippets_pruned: List[str] = field(default_factory=list)
    sections_referenced: List[str] = field(default_factory=list)
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_nodes_count": self.original_nodes_count,
            "optimized_nodes_count": self.optimized_nodes_count,
            "nodes_eliminated": self.nodes_eliminated,
            "original_size_bytes": self.original_size_bytes,
            "optimized_size_bytes": self.optimized_size_bytes,
            "reduction_pct": round(self.reduction_pct, 2),
            "dead_branches_pruned": self.dead_branches_pruned,
            "unused_assigns_pruned": self.unused_assigns_pruned,
            "snippets_referenced": self.snippets_referenced,
            "snippets_pruned": self.snippets_pruned,
            "sections_referenced": self.sections_referenced,
            "execution_time_ms": round(self.execution_time_ms, 3),
        }


class CSSMinifier:
    """Minifies CSS stylesheet content inside Liquid themes."""

    @staticmethod
    def minify(css: str) -> str:
        if not css:
            return ""
        # Remove comments /* ... */
        css = re.sub(r"/\*[\s\S]*?\*/", "", css)
        # Collapse whitespace
        css = re.sub(r"\s+", " ", css)
        # Remove spaces around delimiters
        css = re.sub(r"\s*([\{\}\:\;\,\>])\s*", r"\1", css)
        # Remove trailing semicolons in blocks
        css = re.sub(r";\}", "}", css)
        # Remove empty rule blocks
        css = re.sub(r"[^{}]+\{\}", "", css)
        return css.strip()


class JSMinifier:
    """Minifies JavaScript script content inside Liquid themes."""

    @staticmethod
    def minify(js: str) -> str:
        if not js:
            return ""
        # Remove block comments
        js = re.sub(r"/\*[\s\S]*?\*/", "", js)
        # Remove line comments (careful with URLs like http://)
        lines = []
        for line in js.splitlines():
            stripped = line.strip()
            if stripped.startswith("//"):
                continue
            # Remove trailing comments if not in string
            if "//" in stripped and not ("http://" in stripped or "https://" in stripped):
                idx = stripped.find("//")
                stripped = stripped[:idx].rstrip()
            if stripped:
                lines.append(stripped)
        compressed = " ".join(lines)
        compressed = re.sub(r"\s+", " ", compressed)
        # Clean spacing around common operators
        compressed = re.sub(r"\s*([\{\}\(\)\=\;\,\:\+\-\<\>])\s*", r"\1", compressed)
        return compressed.strip()


class LiquidASTOptimizer:
    """
    Advanced AST Optimizer for Shopify Liquid Themes.
    Performs Tree-Shaking, Dead Code Elimination, Constant Folding & Asset Compaction.
    """

    def __init__(self, enable_dce: bool = True, enable_tree_shaking: bool = True, minify_assets: bool = True):
        self.enable_dce = enable_dce
        self.enable_tree_shaking = enable_tree_shaking
        self.minify_assets = minify_assets
        self.css_minifier = CSSMinifier()
        self.js_minifier = JSMinifier()

    def get_children(self, node: ASTNode) -> List[ASTNode]:
        """Returns direct child AST nodes for any node type."""
        if isinstance(node, TemplateNode):
            return node.children if node.children else getattr(node, "body", [])
        elif isinstance(node, BlockNode):
            res = list(node.body)
            for branch in node.branches:
                res.extend(branch.body)
            return res
        return []

    def count_nodes(self, node: ASTNode) -> int:
        count = 1
        for child in self.get_children(node):
            count += self.count_nodes(child)
        return count

    def collect_used_symbols(self, node: ASTNode) -> Set[str]:
        """Collects all variable and symbol identifiers read across the AST tree."""
        used: Set[str] = set()

        if isinstance(node, VariableNode):
            root_var = node.expression.split(".")[0].split("[")[0].strip()
            if root_var:
                used.add(root_var)
            for f in node.filters:
                for arg in f.args:
                    arg_str = str(arg).strip()
                    if arg_str and not (arg_str.startswith('"') or arg_str.startswith("'") or arg_str.isdigit()):
                        used.add(arg_str.split(".")[0])

        elif isinstance(node, TagNode):
            for k, v in node.attributes.items():
                if isinstance(v, str):
                    for word in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", v):
                        used.add(word)

        elif isinstance(node, BlockNode):
            if "condition" in node.attributes and isinstance(node.attributes["condition"], str):
                for word in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", node.attributes["condition"]):
                    used.add(word)
            for branch in node.branches:
                if branch.condition:
                    for word in re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", branch.condition):
                        used.add(word)

        for child in self.get_children(node):
            used.update(self.collect_used_symbols(child))

        return used

    def collect_references(self, node: ASTNode) -> Tuple[Set[str], Set[str]]:
        """Collects snippet (render/include) and section references from the AST."""
        snippets: Set[str] = set()
        sections: Set[str] = set()

        if isinstance(node, TagNode):
            if node.tag_name in ("render", "include"):
                snip = node.attributes.get("snippet") or node.attributes.get("target")
                if not snip and node.raw_content:
                    m = re.search(r"['\"]([^'\"]+)['\"]", node.raw_content)
                    if m:
                        snip = m.group(1)
                if snip:
                    snippets.add(snip.strip("\"'"))
            elif node.tag_name in ("section", "sections"):
                sec = node.attributes.get("section") or node.attributes.get("target")
                if not sec and node.raw_content:
                    m = re.search(r"['\"]([^'\"]+)['\"]", node.raw_content)
                    if m:
                        sec = m.group(1)
                if sec:
                    sections.add(sec.strip("\"'"))

        for child in self.get_children(node):
            child_snippets, child_sections = self.collect_references(child)
            snippets.update(child_snippets)
            sections.update(child_sections)

        return snippets, sections

    def _eval_static_condition(self, condition: Optional[str]) -> Optional[bool]:
        """Statically evaluates constant boolean conditions (e.g. 'false', 'true', '0', '1', 'blank')."""
        if condition is None:
            return None
        cond = condition.strip().lower()
        if cond in ("false", "nil", "null", "0 == 1", "false == true"):
            return False
        if cond in ("true", "1 == 1", "true == true"):
            return True
        return None

    def optimize_node(self, node: ASTNode, used_symbols: Set[str], stats: OptimizationStats) -> Optional[ASTNode]:
        """Recursively optimizes an AST node."""

        # 1. Raw Nodes (Schema, Stylesheet, Javascript)
        if isinstance(node, RawNode):
            if node.tag_name in ("stylesheet", "style") and self.minify_assets:
                node.content = self.css_minifier.minify(node.content)
            elif node.tag_name == "javascript" and self.minify_assets:
                node.content = self.js_minifier.minify(node.content)
            elif node.tag_name == "comment":
                # Prune liquid comments in production optimization
                stats.nodes_eliminated += 1
                return None
            return node

        # 2. Text Nodes
        if isinstance(node, TextNode):
            # If text is solely whitespace and empty, keep minimal or as is
            return node

        # 3. Tag Nodes (Assigns, Render, etc.)
        if isinstance(node, TagNode):
            if self.enable_tree_shaking and node.tag_name == "assign":
                var_name = node.attributes.get("target") or node.attributes.get("var_name")
                if not var_name and node.raw_content:
                    m = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)", node.raw_content.strip())
                    if m:
                        var_name = m.group(1)
                # If assigned variable is never read anywhere in the template
                if var_name and var_name not in used_symbols:
                    stats.unused_assigns_pruned += 1
                    stats.nodes_eliminated += 1
                    return None
            return node

        # 4. Block Nodes (if / unless / for / etc.)
        if isinstance(node, BlockNode):
            # Optimize children inside body
            optimized_body: List[ASTNode] = []
            for child in node.body:
                opt_child = self.optimize_node(child, used_symbols, stats)
                if opt_child is not None:
                    optimized_body.append(opt_child)

            # Optimize branches
            optimized_branches: List[BlockBranch] = []
            for branch in node.branches:
                branch_body: List[ASTNode] = []
                for b_child in branch.body:
                    opt_b = self.optimize_node(b_child, used_symbols, stats)
                    if opt_b is not None:
                        branch_body.append(opt_b)
                optimized_branches.append(
                    BlockBranch(
                        branch_type=branch.branch_type,
                        condition=branch.condition,
                        body=branch_body,
                    )
                )

            # Dead Code Elimination for Static Conditions
            if self.enable_dce and node.tag_name in ("if", "unless"):
                cond_val = self._eval_static_condition(node.attributes.get("condition"))
                if node.tag_name == "unless" and cond_val is not None:
                    cond_val = not cond_val

                # If statically FALSE -> prune main body
                if cond_val is False:
                    stats.dead_branches_pruned += 1
                    # Check if there is an else/elsif branch
                    else_branch = next((b for b in optimized_branches if b.branch_type == "else"), None)
                    if else_branch and else_branch.body:
                        stats.nodes_eliminated += (1 + len(optimized_body))
                        return BlockNode(
                            tag_name="if",
                            attributes={"condition": "true"},
                            body=else_branch.body,
                            branches=[],
                            line=node.line,
                            col=node.col,
                        )
                    else:
                        stats.nodes_eliminated += (1 + len(optimized_body))
                        return None

                # If statically TRUE -> discard all elsif / else branches
                elif cond_val is True:
                    stats.dead_branches_pruned += len(optimized_branches)
                    optimized_branches = []

            return BlockNode(
                tag_name=node.tag_name,
                attributes=node.attributes,
                body=optimized_body,
                branches=optimized_branches,
                trim_left=node.trim_left,
                trim_right=node.trim_right,
                line=node.line,
                col=node.col,
            )

        # 5. Template Node
        if isinstance(node, TemplateNode):
            node_children = self.get_children(node)
            optimized_body: List[ASTNode] = []
            for child in node_children:
                opt_child = self.optimize_node(child, used_symbols, stats)
                if opt_child is not None:
                    optimized_body.append(opt_child)
            return TemplateNode(
                name=node.name,
                file_path=node.file_path,
                children=optimized_body,
                metadata=node.metadata,
                line=node.line,
                col=node.col,
            )

        return node

    def optimize(
        self,
        template: TemplateNode,
        original_source: str = "",
        available_snippets: Optional[List[str]] = None,
    ) -> Tuple[TemplateNode, OptimizationStats]:
        """
        Executes full AST optimization pipeline on a given TemplateNode.
        """
        start_time = time.perf_counter()
        stats = OptimizationStats()

        stats.original_nodes_count = self.count_nodes(template)
        stats.original_size_bytes = len(original_source.encode("utf-8")) if original_source else 0

        # Phase 1: Symbol & Reference Analysis
        used_symbols = self.collect_used_symbols(template)
        referenced_snippets, referenced_sections = self.collect_references(template)
        stats.snippets_referenced = sorted(list(referenced_snippets))
        stats.sections_referenced = sorted(list(referenced_sections))

        # Check for unreferenced snippets if inventory provided
        if available_snippets:
            for s in available_snippets:
                if s not in referenced_snippets:
                    stats.snippets_pruned.append(s)

        # Phase 2: AST Node Optimization Pass
        optimized_root = self.optimize_node(template, used_symbols, stats)
        if not isinstance(optimized_root, TemplateNode):
            optimized_root = TemplateNode(children=[optimized_root] if optimized_root else [])

        stats.optimized_nodes_count = self.count_nodes(optimized_root)
        stats.nodes_eliminated = max(0, stats.original_nodes_count - stats.optimized_nodes_count)

        # Measure serialized output size
        optimized_json = json.dumps(optimized_root.to_dict())
        stats.optimized_size_bytes = len(optimized_json.encode("utf-8"))

        if stats.original_size_bytes > 0:
            reduction = ((stats.original_size_bytes - stats.optimized_size_bytes) / stats.original_size_bytes) * 100.0
            stats.reduction_pct = max(0.0, reduction)

        stats.execution_time_ms = (time.perf_counter() - start_time) * 1000.0
        return optimized_root, stats


class ShopifyViteCompilerPlugin:
    """
    Vite / Rollup Bridge for Shopify Liquid Compilation & Asset Optimization.
    Produces Rollup plugin hooks, asset manifests, and hashed Liquid tags.
    """

    def __init__(self, theme_root: str = ".", output_dir: str = "assets"):
        self.theme_root = theme_root
        self.output_dir = output_dir
        self.optimizer = LiquidASTOptimizer()
        self.compiler = LiquidASTCompiler()

    def generate_vite_config(self, entrypoints: List[str]) -> Dict[str, Any]:
        """Generates standard Vite configuration dictionary for Shopify theme bundling."""
        return {
            "plugins": ["vite-plugin-shopify-liquid", "vite-plugin-tailwindcss"],
            "build": {
                "outDir": self.output_dir,
                "emptyOutDir": False,
                "manifest": True,
                "rollupOptions": {
                    "input": entrypoints,
                    "output": {
                        "entryFileNames": "assets/[name].[hash].js",
                        "chunkFileNames": "assets/[name].[hash].js",
                        "assetFileNames": "assets/[name].[hash].[ext]",
                    },
                },
                "minify": "esbuild",
            },
        }

    def generate_asset_tag(self, asset_filename: str, asset_type: str = "stylesheet") -> str:
        """Generates canonical Shopify Liquid asset URL inclusion tags."""
        if asset_type == "stylesheet" or asset_filename.endswith(".css"):
            return f"{{{{ '{asset_filename}' | asset_url | stylesheet_tag }}}}"
        elif asset_type == "script" or asset_filename.endswith(".js"):
            return f"{{{{ '{asset_filename}' | asset_url | script_tag }}}}"
        return f"{{{{ '{asset_filename}' | asset_url }}}}"

    def process_liquid_file(
        self,
        liquid_source: str,
        filename: str = "template.liquid",
        available_snippets: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Compiles and optimizes a Liquid template file through the full Vite pipeline.
        """
        # Step 1: Parse AST
        ast_result = self.compiler.compile(liquid_source)
        if not ast_result.template:
            raise ValueError(f"Failed to parse Liquid AST: {ast_result.warnings}")

        # Step 2: Optimize AST
        optimized_ast, stats = self.optimizer.optimize(
            template=ast_result.template,
            original_source=liquid_source,
            available_snippets=available_snippets,
        )

        return {
            "filename": filename,
            "status": "success",
            "original_ast": ast_result.ast_dict,
            "optimized_ast": optimized_ast.to_dict(),
            "stats": stats.to_dict(),
        }
