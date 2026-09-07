# --- DNK-MRH-HEADER ---
# mrh_id: "scripts_system_sync_codebase_to_canvas"
# purpose: "AST-driven codebase architecture scanning and Obsidian Canvas synchronizer"
# canonical_source: true
# alters_files: ["docs/notes/DNK_HUB_Core_Architecture.canvas"]
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import argparse
import ast
import json
import logging
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("sync_codebase_to_canvas")

ROOT_DIR = Path(__file__).resolve().parents[2]


class CodebaseASTScanner:
    """Scans repository code modules and extracts architectural entities and relations."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def scan_python_module(self, rel_path: str) -> Dict[str, Any]:
        """Extract classes, functions, and docstrings from a Python file."""
        file_path = self.base_dir / rel_path
        if not file_path.exists():
            return {}

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=rel_path)
        except Exception as e:
            logger.debug(f"Failed to parse AST for {rel_path}: {e}")
            return {"file": rel_path, "classes": [], "functions": [], "loc": 0}

        loc = len([line for line in content.splitlines() if line.strip() and not line.strip().startswith("#")])

        classes = []
        functions = []
        imports = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                classes.append({
                    "name": node.name,
                    "doc": doc.split("\n")[0] if doc else "",
                    "methods": methods[:5]
                })
            elif isinstance(node, ast.FunctionDef) and isinstance(getattr(node, 'parent', None), (type(None), ast.Module)):
                doc = ast.get_docstring(node) or ""
                functions.append({
                    "name": node.name,
                    "doc": doc.split("\n")[0] if doc else ""
                })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)

        return {
            "file": rel_path,
            "classes": classes,
            "functions": functions,
            "imports": list(imports),
            "loc": loc
        }

    def scan_typescript_file(self, rel_path: str) -> Dict[str, Any]:
        """Extract components, functions, interfaces from TS/TSX file."""
        file_path = self.base_dir / rel_path
        if not file_path.exists():
            return {}

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {"file": rel_path, "classes": [], "functions": [], "loc": 0}

        loc = len([line for line in content.splitlines() if line.strip() and not line.strip().startswith("//")])

        components = re.findall(r"export\s+(?:default\s+)?function\s+([A-Z]\w+)", content)
        components += re.findall(r"export\s+const\s+([A-Z]\w+)\s*[:=]", content)
        interfaces = re.findall(r"export\s+interface\s+([A-Za-z0-9_]+)", content)
        interfaces += re.findall(r"export\s+type\s+([A-Za-z0-9_]+)", content)

        return {
            "file": rel_path,
            "classes": [{"name": c, "doc": "React Component / UI View", "methods": []} for c in set(components)],
            "functions": [{"name": i, "doc": "TypeScript Interface / Contract"} for i in set(interfaces[:5])],
            "loc": loc
        }


class CanvasSyncEngine:
    """Builds and serializes an Obsidian Canvas structure representing DNK OS architecture."""

    # Obsidian Canvas Color palette:
    # 1: Red, 2: Orange, 3: Yellow, 4: Green, 5: Cyan/Blue, 6: Purple
    GROUPS_CONFIG = [
        {
            "id": "grp_core",
            "label": "👑 Core Orchestration & Swarm Hub",
            "color": "6",
            "patterns": [
                "core/orchestrator/control_plane.py",
                "core/orchestrator/swarm_health.py",
                "core/orchestrator/accounting_engine.py",
                "core/orchestrator/visual_canvas_control.py",
                "core/orchestrator/session_sentinel.py",
                "core/orchestrator/dna_assimilation.py",
                "core/orchestrator/task_forest.py",
                "core/orchestrator/mcp_slim_guard.py",
            ]
        },
        {
            "id": "grp_backend",
            "label": "⚡ FastAPI Backend & Routers",
            "color": "5",
            "patterns": [
                "apps/api/main.py",
                "apps/api/routers/workspace.py",
                "apps/api/routers/agent.py",
                "apps/api/routers/health.py",
                "apps/api/routers/swarm_ws.py",
                "apps/api/routers/canvas_bridge.py",
                "apps/api/routers/a2a_mesh_router.py",
            ]
        },
        {
            "id": "grp_frontend",
            "label": "🖥️ Web Frontend (apps/web)",
            "color": "4",
            "patterns": [
                "apps/web/types/apiProtocol.ts",
                "apps/web/types/apiGenerated.ts",
                "apps/web/components/workspace/WorkspaceShell.tsx",
                "apps/web/components/canvas/ObsidianSyncBar.tsx",
                "apps/web/components/canvas/TimeTravelRail.tsx",
                "apps/web/lib/api/swarm_health_client.ts",
            ]
        },
        {
            "id": "grp_gates",
            "label": "🛡️ System Quality Gates & Automation",
            "color": "3",
            "patterns": [
                "scripts/verify_all.sh",
                "scripts/system/auto_precommit_guard.py",
                "scripts/system/blast_radius_analyzer.py",
                "scripts/system/generate_frontend_types.py",
                "scripts/system/sync_codebase_to_canvas.py",
                "scripts/system/repo_map.py",
            ]
        },
        {
            "id": "grp_workers",
            "label": "🤖 Autonomous Swarm Workers",
            "color": "1",
            "patterns": [
                "core/orchestrator/agents/gerych_prime/SOUL.md",
                "core/orchestrator/agents/gerych_builder/SOUL.md",
                "core/orchestrator/agents/gerych_researcher/SOUL.md",
                "core/orchestrator/agents/gerych_auditor/SOUL.md",
                "core/orchestrator/agents/dnk_dev_fullstack/SOUL.md",
                "core/orchestrator/agents/dnk_shopify/SOUL.md",
            ]
        }
    ]

    def __init__(self, root_dir: Path, max_nodes_per_group: int = 12):
        self.root_dir = root_dir
        self.max_nodes_per_group = max_nodes_per_group
        self.scanner = CodebaseASTScanner(root_dir)

    def generate_canvas(self) -> Dict[str, Any]:
        """Assembles the complete Obsidian Canvas JSON structure."""
        nodes: List[Dict[str, Any]] = []
        edges: List[Dict[str, Any]] = []

        grp_x = 0
        grp_y = 0
        grp_spacing_x = 600
        grp_spacing_y = 750

        node_map: Dict[str, str] = {}  # file_path -> node_id

        # Calculate coordinates for 2-column or 3-column layout
        for idx, grp in enumerate(self.GROUPS_CONFIG):
            col = idx % 2
            row = idx // 2
            gx = col * grp_spacing_x
            gy = row * grp_spacing_y

            grp_node_id = grp["id"]
            inner_nodes: List[Dict[str, Any]] = []

            # Process group files
            card_x = gx + 30
            card_y = gy + 60
            card_w = 480
            card_h = 100

            file_list = grp["patterns"][: self.max_nodes_per_group]
            for f_idx, rel_file in enumerate(file_list):
                node_id = f"n_{re.sub(r'[^a-zA-Z0-9_]', '_', rel_file)}"
                node_map[rel_file] = node_id

                cur_y = card_y + f_idx * (card_h + 20)

                # Scan details
                md_text = self._build_node_markdown(rel_file)

                node_entry = {
                    "id": node_id,
                    "type": "text",
                    "text": md_text,
                    "x": card_x,
                    "y": cur_y,
                    "width": card_w,
                    "height": card_h,
                    "color": grp["color"]
                }
                nodes.append(node_entry)
                inner_nodes.append(node_entry)

            # Determine group container size
            grp_height = max(400, (len(file_list) * (card_h + 20)) + 80)
            grp_node = {
                "id": grp_node_id,
                "type": "group",
                "label": grp["label"],
                "x": gx,
                "y": gy,
                "width": card_w + 60,
                "height": grp_height,
                "color": grp["color"]
            }
            nodes.insert(0, grp_node)

        # Build cross-layer edges
        edges = self._build_edges(node_map)

        return {
            "nodes": nodes,
            "edges": edges
        }

    def _build_node_markdown(self, rel_path: str) -> str:
        """Create structured markdown content for each canvas node."""
        path_obj = self.root_dir / rel_path
        if not path_obj.exists():
            return f"### `{Path(rel_path).name}`\n*Virtual reference: {rel_path}*"

        name = path_obj.name
        if rel_path.endswith(".py"):
            info = self.scanner.scan_python_module(rel_path)
            cls_names = [c["name"] for c in info.get("classes", [])]
            cls_str = ", ".join(cls_names[:3]) if cls_names else "Module"
            loc = info.get("loc", 0)
            return (
                f"### `{name}`\n"
                f"**Classes**: `{cls_str}`\n"
                f"**Path**: `{rel_path}` | **LOC**: {loc}\n"
                f"*Status*: Active SSOT"
            )
        elif rel_path.endswith(".ts") or rel_path.endswith(".tsx"):
            info = self.scanner.scan_typescript_file(rel_path)
            comp_names = [c["name"] for c in info.get("classes", [])]
            comp_str = ", ".join(comp_names[:3]) if comp_names else "Types/Utils"
            loc = info.get("loc", 0)
            return (
                f"### `{name}`\n"
                f"**Symbols**: `{comp_str}`\n"
                f"**Path**: `{rel_path}` | **LOC**: {loc}\n"
                f"*Tier*: 1 (Web SSOT)"
            )
        elif rel_path.endswith(".sh"):
            loc = len([l for l in path_obj.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()])
            return (
                f"### `{name}`\n"
                f"**Type**: Shell Gatekeeper / Orchestrator\n"
                f"**Path**: `{rel_path}` | **LOC**: {loc}\n"
                f"*Verification*: Master Quality Gate"
            )
        elif rel_path.endswith("SOUL.md"):
            agent_name = path_obj.parent.name
            return (
                f"### 🤖 `{agent_name}`\n"
                f"**Role**: Specialized DNK OS Swarm Agent\n"
                f"**Specification**: `{rel_path}`\n"
                f"*Status*: Autonomous Worker"
            )
        else:
            return f"### `{name}`\n**Path**: `{rel_path}`"

    def _build_edges(self, node_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """Construct semantic relationship edges between architectural layers."""
        edges: List[Dict[str, Any]] = []

        # Explicit architectural links
        RELATIONS = [
            ("scripts/verify_all.sh", "scripts/system/blast_radius_analyzer.py", "evaluates"),
            ("scripts/verify_all.sh", "scripts/system/auto_precommit_guard.py", "executes"),
            ("scripts/system/generate_frontend_types.py", "apps/api/main.py", "extracts OpenAPI"),
            ("scripts/system/generate_frontend_types.py", "apps/web/types/apiGenerated.ts", "generates"),
            ("apps/web/types/apiProtocol.ts", "apps/web/types/apiGenerated.ts", "re-exports"),
            ("apps/api/main.py", "apps/api/routers/workspace.py", "mounts"),
            ("apps/api/main.py", "apps/api/routers/health.py", "mounts"),
            ("apps/api/main.py", "apps/api/routers/swarm_ws.py", "mounts"),
            ("apps/api/routers/health.py", "core/orchestrator/swarm_health.py", "queries"),
            ("apps/api/routers/swarm_ws.py", "core/orchestrator/control_plane.py", "streams"),
            ("apps/web/lib/api/swarm_health_client.ts", "apps/api/routers/health.py", "fetches"),
            ("core/orchestrator/control_plane.py", "core/orchestrator/accounting_engine.py", "tracks cost"),
            ("core/orchestrator/control_plane.py", "core/orchestrator/visual_canvas_control.py", "renders"),
            ("core/orchestrator/agents/gerych_prime/SOUL.md", "core/orchestrator/control_plane.py", "orchestrates"),
            ("core/orchestrator/agents/gerych_auditor/SOUL.md", "scripts/verify_all.sh", "validates"),
        ]

        edge_idx = 1
        for src, tgt, label in RELATIONS:
            if src in node_map and tgt in node_map:
                edges.append({
                    "id": f"edge_arch_{edge_idx}",
                    "fromNode": node_map[src],
                    "fromSide": "right",
                    "toNode": node_map[tgt],
                    "toSide": "left",
                    "label": label
                })
                edge_idx += 1

        return edges


def main():
    parser = argparse.ArgumentParser(description="Synchronize DNK OS Codebase Architecture to Obsidian Canvas")
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="docs/notes/DNK_HUB_Core_Architecture.canvas",
        help="Target canvas file path (default: docs/notes/DNK_HUB_Core_Architecture.canvas)"
    )
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=12,
        help="Max nodes per group (default: 12)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and report without writing to disk"
    )

    args = parser.parse_args()

    engine = CanvasSyncEngine(ROOT_DIR, max_nodes_per_group=args.max_nodes)
    canvas_doc = engine.generate_canvas()

    num_nodes = len([n for n in canvas_doc["nodes"] if n.get("type") != "group"])
    num_groups = len([n for n in canvas_doc["nodes"] if n.get("type") == "group"])
    num_edges = len(canvas_doc["edges"])

    logger.info(f"Generated Codebase Canvas Graph: {num_groups} groups, {num_nodes} nodes, {num_edges} edges")

    if args.dry_run:
        logger.info("[DRY-RUN] Skipping disk write.")
        return

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = ROOT_DIR / out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(canvas_doc, f, indent=2, ensure_ascii=False)

    logger.info(f"Successfully saved codebase architecture canvas to: {out_path} ✅")


if __name__ == "__main__":
    main()
