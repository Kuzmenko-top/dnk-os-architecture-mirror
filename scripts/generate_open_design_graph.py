# --- DNK-MRH-HEADER ---
# mrh_id: "scripts/generate_open_design_graph.py"
# purpose: "High-fidelity AST-based/Regex-based Code Graph Parser for the JS/TS monorepo Open Design to map all directories, files, imports, classes, and functions into PostgreSQL."
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

import os
import sys
import re
import json
from pathlib import Path
from loguru import logger

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.dnk_os_memory.db import get_db_connection

# Root path of the Open Design project
OPEN_DESIGN_ROOT = PROJECT_ROOT / "DNK OS" / "visual_shell" / "open_design"

# Folders to completely ignore during scanning
EXCLUDED_FOLDERS = {
    "node_modules", "dist", ".next", "build", ".git", "out", ".tmp", "tmp",
    "cache", "docs", "design-systems", "design-templates", "prompt-templates",
    "clones", "postgres_data", "__pycache__", ".venv", "venv"
}

SCANNABLE_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}

def count_lines(filepath: Path) -> int:
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

def parse_js_ts_file(filepath: Path, rel_path: str):
    """Extracts imports, classes, and functions from a JS/TS file."""
    imports = []
    classes = []
    functions = []
    
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.warning(f"Failed to read {filepath}: {e}")
        return imports, classes, functions

    # Using character escapes to avoid string quote parsing issues in python
    # \x27 is single quote ('), \x22 is double quote (")
    import_pattern = re.compile(
        r"(?:import\s+(?:type\s+)?([\w*$\s{},]*)\s+from\s+[\x27\x22]([^\x27\x22]+)[\x27\x22]|import\s+[\x27\x22]([^\x27\x22]+)[\x27\x22]|require\([\x27\x22]([^\x27\x22]+)[\x27\x22]\))"
    )
    class_pattern = re.compile(
        r"(?:export\s+)?(?:default\s+)?class\s+([a-zA-Z0-9_$]+)(?:\s+extends\s+([a-zA-Z0-9_$.]+))?"
    )
    func_pattern = re.compile(
        r"(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\("
    )
    arrow_pattern = re.compile(
        r"(?:export\s+)?(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"
    )
    method_pattern = re.compile(
        r"(?:async\s+)?\b(?!if|for|while|switch|catch|function\b)([a-zA-Z0-9_$]+)\s*\([^)]*\)\s*\{"
    )

    lines = content.splitlines()
    current_class = None
    brace_depth = 0
    class_brace_depth = 0

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # Track brace depth for classes
        open_braces = line_stripped.count('{')
        close_braces = line_stripped.count('}')
        brace_depth += open_braces - close_braces
        
        if current_class and brace_depth <= class_brace_depth:
            current_class = None
            
        # Parse imports
        for match in import_pattern.finditer(line_stripped):
            groups = match.groups()
            target = groups[1] or groups[2] or groups[3]
            if target:
                imports.append({
                    "name": target,
                    "lineno": i
                })

        # Parse classes
        class_match = class_pattern.search(line_stripped)
        if class_match:
            class_name = class_match.group(1)
            parent = class_match.group(2)
            classes.append({
                "name": class_name,
                "lineno": i,
                "bases": [parent] if parent else []
            })
            current_class = class_name
            class_brace_depth = brace_depth - open_braces

        # Parse functions
        func_match = func_pattern.search(line_stripped)
        if func_match:
            func_name = func_match.group(1)
            functions.append({
                "name": func_name,
                "is_async": "async" in line_stripped,
                "class_name": current_class,
                "lineno": i,
                "args": []
            })
            continue

        arrow_match = arrow_pattern.search(line_stripped)
        if arrow_match:
            func_name = arrow_match.group(1)
            functions.append({
                "name": func_name,
                "is_async": "async" in line_stripped,
                "class_name": current_class,
                "lineno": i,
                "args": []
            })
            continue

        # Class method match
        if current_class:
            method_match = method_pattern.search(line_stripped)
            if method_match:
                method_name = method_match.group(1)
                functions.append({
                    "name": method_name,
                    "is_async": "async" in line_stripped,
                    "class_name": current_class,
                    "lineno": i,
                    "args": []
                })

    return imports, classes, functions

def resolve_import_path(source_rel_path: str, import_target: str) -> str:
    if import_target.startswith("."):
        source_dir = Path(source_rel_path).parent
        resolved = (source_dir / import_target).resolve()
        try:
            rel = resolved.relative_to(PROJECT_ROOT)
            return str(rel)
        except ValueError:
            pass
    elif import_target.startswith("@/"):
        target_path = import_target[2:]
        for sub in ["apps/web/src", "apps/web", "apps/daemon/src", "packages"]:
            candidate = OPEN_DESIGN_ROOT / sub / target_path
            if candidate.exists() or candidate.with_suffix(".ts").exists() or candidate.with_suffix(".tsx").exists():
                return str(candidate.relative_to(PROJECT_ROOT))
    elif "/" in import_target and not import_target.startswith("@"):
        for folder in ["packages", "apps", "tools"]:
            if import_target.startswith(folder):
                candidate = OPEN_DESIGN_ROOT / import_target
                if candidate.exists() or candidate.with_suffix(".ts").exists():
                    return str(candidate.relative_to(PROJECT_ROOT))
    return None

def analyze_and_populate():
    logger.info("🎬 Starting High-Fidelity JS/TS Code Graph Parser for Open Design...")
    
    nodes_to_insert = []
    edges_to_insert = []
    visited_directories = set()

    for root, dirs, files in os.walk(OPEN_DESIGN_ROOT):
        # Prune excluded folders in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDED_FOLDERS and not d.startswith(".")]
        
        root_path = Path(root)
        try:
            dir_rel_path = str(root_path.relative_to(PROJECT_ROOT))
        except ValueError:
            continue

        if not dir_rel_path or dir_rel_path == ".":
            continue

        # 1. Add Directory Node
        dir_node_id = f"dir:{dir_rel_path}"
        if dir_rel_path not in visited_directories:
            visited_directories.add(dir_rel_path)
            nodes_to_insert.append({
                "node_id": dir_node_id,
                "label": root_path.name,
                "node_type": "directory",
                "metadata": {"path": dir_rel_path}
            })
            
            # Connect parent directory to child directory
            parent_dir = root_path.parent
            try:
                parent_rel = str(parent_dir.relative_to(PROJECT_ROOT))
                if parent_rel and parent_rel != ".":
                    edges_to_insert.append({
                        "source_id": f"dir:{parent_rel}",
                        "target_id": dir_node_id,
                        "relationship": "CONTAINS",
                        "weight": 1.0
                    })
            except ValueError:
                pass

        # 2. Scan Files
        for file in files:
            file_path = root_path / file
            suffix = file_path.suffix.lower()
            if suffix not in SCANNABLE_EXTENSIONS:
                continue

            rel_file_path = str(file_path.relative_to(PROJECT_ROOT))
            file_node_id = f"file:{rel_file_path}"
            loc = count_lines(file_path)

            # Add File Node
            nodes_to_insert.append({
                "node_id": file_node_id,
                "label": file,
                "node_type": "file",
                "metadata": {"path": rel_file_path, "loc": loc, "language": suffix[1:]}
            })

            # Connect Directory containing File
            edges_to_insert.append({
                "source_id": dir_node_id,
                "target_id": file_node_id,
                "relationship": "CONTAINS",
                "weight": 1.0
            })

            # Parse imports, classes, functions/methods
            imports, classes, functions = parse_js_ts_file(file_path, rel_file_path)

            # Class Nodes
            for cls in classes:
                cls_node_id = f"class:{rel_file_path}:{cls['name']}"
                nodes_to_insert.append({
                    "node_id": cls_node_id,
                    "label": cls["name"],
                    "node_type": "class",
                    "metadata": {"filepath": rel_file_path, "lineno": cls["lineno"], "bases": cls["bases"]}
                })
                edges_to_insert.append({
                    "source_id": file_node_id,
                    "target_id": cls_node_id,
                    "relationship": "CONTAINS",
                    "weight": 1.0
                })

            # Function / Method Nodes
            for func in functions:
                func_node_id = f"func:{rel_file_path}:{func['name']}"
                nodes_to_insert.append({
                    "node_id": func_node_id,
                    "label": func["name"],
                    "node_type": "function",
                    "metadata": {
                        "filepath": rel_file_path,
                        "lineno": func["lineno"],
                        "is_async": func["is_async"],
                        "class_name": func["class_name"],
                        "args": func["args"]
                    }
                })

                if func["class_name"]:
                    cls_node_id = f"class:{rel_file_path}:{func['class_name']}"
                    edges_to_insert.append({
                        "source_id": cls_node_id,
                        "target_id": func_node_id,
                        "relationship": "CONTAINS",
                        "weight": 1.0
                    })
                else:
                    edges_to_insert.append({
                        "source_id": file_node_id,
                        "target_id": func_node_id,
                        "relationship": "CONTAINS",
                        "weight": 1.0
                    })

            # Imports (Dependencies)
            for imp in imports:
                resolved_target = resolve_import_path(rel_file_path, imp["name"])
                if resolved_target:
                    target_file = PROJECT_ROOT / resolved_target
                    target_node_id = None
                    if target_file.exists():
                        target_node_id = f"file:{resolved_target}"
                    elif (target_file.parent / (target_file.name + ".ts")).exists():
                        target_node_id = f"file:{resolved_target}.ts"
                    elif (target_file.parent / (target_file.name + ".tsx")).exists():
                        target_node_id = f"file:{resolved_target}.tsx"
                    elif target_file.is_dir():
                        target_node_id = f"dir:{resolved_target}"
                    
                    if target_node_id:
                        edges_to_insert.append({
                            "source_id": file_node_id,
                            "target_id": target_node_id,
                            "relationship": "IMPORTS",
                            "weight": 1.0
                        })

    logger.info(f"📊 Extraction completed. Prepared {len(nodes_to_insert)} nodes and {len(edges_to_insert)} edges.")

    try:
        conn = get_db_connection(project_id="00_Ecosystem_Library")
        with conn.cursor() as cur:
            logger.info("🧹 Purging old Open Design Code Graph entries from PostgreSQL...")
            
            # Find nodes belonging to Open Design path
            cur.execute("""
                DELETE FROM cross_repo_nodes 
                WHERE (node_type IN ('file', 'directory', 'class', 'function') 
                       AND (metadata->>'path' LIKE 'visual_shell/open_design%' 
                            OR metadata->>'filepath' LIKE 'visual_shell/open_design%'));
            """)
            
            cur.execute("""
                DELETE FROM cross_repo_edges 
                WHERE (source_id LIKE 'dir:visual_shell/open_design%'
                       OR source_id LIKE 'file:visual_shell/open_design%'
                       OR source_id LIKE 'class:visual_shell/open_design%'
                       OR source_id LIKE 'func:visual_shell/open_design%'
                       OR target_id LIKE 'dir:visual_shell/open_design%'
                       OR target_id LIKE 'file:visual_shell/open_design%'
                       OR target_id LIKE 'class:visual_shell/open_design%'
                       OR target_id LIKE 'func:visual_shell/open_design%');
            """)

            node_query = """
                INSERT INTO cross_repo_nodes (node_id, label, node_type, metadata)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (node_id) DO UPDATE SET
                    label = EXCLUDED.label,
                    node_type = EXCLUDED.node_type,
                    metadata = EXCLUDED.metadata;
            """
            for node in nodes_to_insert:
                cur.execute(node_query, (
                    node["node_id"],
                    node["label"],
                    node["node_type"],
                    json.dumps(node["metadata"])
                ))
                
            edge_query = """
                INSERT INTO cross_repo_edges (source_id, target_id, relationship, weight)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """
            for edge in edges_to_insert:
                cur.execute(edge_query, (
                    edge["source_id"],
                    edge["target_id"],
                    edge["relationship"],
                    edge["weight"]
                ))
                
        logger.success(f"🎉 Open Design Code Graph populated successfully! Added {len(nodes_to_insert)} nodes and {len(edges_to_insert)} edges to PostgreSQL!")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to write Open Design Code Graph to database: {e}")
        return False

if __name__ == "__main__":
    analyze_and_populate()
