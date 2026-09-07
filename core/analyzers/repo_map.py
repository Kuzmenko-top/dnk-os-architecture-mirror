# --- DNK-MRH-HEADER ---
# mrh_id: "core_analyzers_repo_map"
# purpose: "Zero-token AST structural code skeleton generator for fast repository indexing."
# author: "DNK-e.com Maksym"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import ast
from pathlib import Path
from typing import Optional, List, Dict, Any


class RepoMapEngine:
    """
    Generates compact structural AST repo maps (classes, functions, signatures)
    for high-speed agent context and token efficiency.
    """

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()

    def render_repo_map(self, query: Optional[str] = None, max_files: int = 30) -> str:
        """
        Scans python modules and renders an AST symbol skeleton map.
        """
        lines: List[str] = ["# === DNK OS Codebase AST Repo-Map ==="]
        target_dirs = [self.root_dir / "core", self.root_dir / "apps" / "api"]

        py_files: List[Path] = []
        for td in target_dirs:
            if td.exists():
                for p in td.rglob("*.py"):
                    if any(part in p.parts for part in [".venv", "__pycache__", "node_modules", ".git"]):
                        continue
                    if query and query.lower() not in str(p).lower():
                        continue
                    py_files.append(p)

        py_files = py_files[:max_files]

        for p in py_files:
            try:
                rel_path = str(p.relative_to(self.root_dir))
            except ValueError:
                rel_path = p.name

            lines.append(f"\n📂 {rel_path}:")
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content, filename=str(p))
                symbols_found = 0
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, ast.ClassDef):
                        methods = [m.name for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))]
                        methods_str = f" (methods: {', '.join(methods[:5])})" if methods else ""
                        lines.append(f"  • class {node.name}{methods_str}")
                        symbols_found += 1
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        args = [a.arg for a in node.args.args if a.arg != "self"]
                        is_async = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
                        lines.append(f"  • {is_async}def {node.name}({', '.join(args[:4])})")
                        symbols_found += 1
                if symbols_found == 0:
                    lines.append("  • (module constants and top-level definitions)")
            except Exception:
                lines.append("  • (syntax inspection skipped)")

        return "\n".join(lines)


repo_map_engine = RepoMapEngine()
