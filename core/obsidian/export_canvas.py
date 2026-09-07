# --- DNK-MRH-HEADER ---
# mrh_id: "core/obsidian/export_canvas.py"
# purpose: "Export Canvas nodes and edges into Markdown files and Obsidian .canvas format with canonical Vault path validation and deterministic revision/content_hash attributes."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import re
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import yaml

def get_canonical_vault_root() -> Path:
    """Returns the canonical root directory of the Obsidian Vault."""
    env_root = os.getenv("DNK_OBSIDIAN_VAULT_ROOT") or os.getenv("OBSIDIAN_VAULT_ROOT")
    if env_root:
        return Path(os.path.expanduser(env_root)).resolve()
    return Path(os.path.expanduser("~/Documents/DNK_HUB My Notes")).resolve()


def get_canonical_task_forest_dir(vault_root: Optional[Path] = None) -> Path:
    """Returns the canonical TaskForest directory inside the Vault root."""
    env_dir = os.getenv("DNK_OBSIDIAN_TASK_FOREST_DIR") or os.getenv("DNK_OBSIDIAN_TASKFOREST_PATH")
    if env_dir:
        return Path(os.path.expanduser(env_dir)).resolve()
    root = vault_root or get_canonical_vault_root()
    return (root / "TaskForest").resolve()


DEFAULT_VAULT_ROOT = get_canonical_vault_root()
DEFAULT_TASK_FOREST_DIR = get_canonical_task_forest_dir(DEFAULT_VAULT_ROOT)
DEFAULT_VAULT_TASKFOREST_PATH = DEFAULT_TASK_FOREST_DIR


def validate_vault_path(
    target_dir: Optional[Union[str, Path]] = None,
    vault_root: Optional[Union[str, Path]] = None,
) -> Path:
    """Validates that target_dir is strictly inside the canonical Vault root.

    Prevents path traversal attacks (e.g. ../../etc, /tmp, or symlink escapes).
    If target_dir is None, returns the canonical task_forest_dir.

    Raises:
        ValueError: If target_dir resolves outside canonical Vault root.
    """
    canonical_root = (
        Path(os.path.expanduser(str(vault_root))).resolve()
        if vault_root is not None
        else get_canonical_vault_root()
    )
    if target_dir is None:
        return get_canonical_task_forest_dir(canonical_root)

    str_target = str(target_dir).strip()
    if str_target.startswith("vault:"):
        sub = str_target[6:].lstrip("/\\")
        resolved_target = (canonical_root / sub).resolve()
    else:
        resolved_target = Path(os.path.expanduser(str_target)).resolve()

    try:
        resolved_target.relative_to(canonical_root)
    except ValueError:
        raise ValueError(
            f"Path traversal forbidden: target_dir '{resolved_target}' is outside canonical Vault root '{canonical_root}'"
        )
    return resolved_target


def _sanitize_filename(name: str) -> str:
    """Sanitize string to create safe filesystem filename."""
    cleaned = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or "unnamed_node"


def export_node_to_markdown(
    node: Dict[str, Any],
    output_dir: Union[str, Path] = DEFAULT_VAULT_TASKFOREST_PATH,
    filename: Optional[str] = None,
    vault_root: Optional[Union[str, Path]] = None,
    enforce_vault_root: bool = False,
) -> Path:
    """Exports a single node as an Obsidian Markdown file with YAML frontmatter.

    Args:
        node: Canvas node dictionary.
        output_dir: Destination folder.
        filename: Optional explicit filename (e.g. 'task_1.md').
        vault_root: Optional canonical vault root.
        enforce_vault_root: If True, validates target_dir against canonical Vault root.

    Returns:
        Path to the generated markdown file.
    """
    if enforce_vault_root:
        target_dir = validate_vault_path(output_dir, vault_root=vault_root)
    else:
        target_dir = Path(os.path.expanduser(str(output_dir))).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    node_id = str(node.get("id", "node"))
    node_type = node.get("type", "text")
    raw_data = node.get("data")
    data: Dict[str, Any] = raw_data if isinstance(raw_data, dict) else {}

    title = (
        data.get("title")
        or data.get("label")
        or node.get("title")
        or node.get("label")
        or f"Node {node_id}"
    )

    tags_val = data.get("tags") or node.get("tags") or []
    if isinstance(tags_val, str):
        tags = [t.strip().lstrip("#") for t in tags_val.split(",") if t.strip()]
    elif isinstance(tags_val, list):
        tags = [str(t).strip().lstrip("#") for t in tags_val if str(t).strip()]
    else:
        tags = []

    description = str(data.get("description") or node.get("description") or "")
    content = str(
        data.get("content")
        or data.get("text")
        or node.get("content")
        or node.get("text")
        or description
    )

    status = data.get("status") or node.get("status")
    priority = data.get("priority") or node.get("priority")
    updated_at = (
        data.get("updated_at")
        or node.get("updated_at")
        or time.time()
    )
    revision = int(data.get("revision") or node.get("revision") or 1)
    content_hash = str(
        data.get("content_hash")
        or node.get("content_hash")
        or hashlib.sha256(content.encode("utf-8")).hexdigest()
    )

    # Build frontmatter
    frontmatter: Dict[str, Any] = {
        "id": node_id,
        "type": node_type,
        "title": title,
        "tags": tags,
        "updated_at": updated_at,
        "revision": revision,
        "content_hash": content_hash,
    }
    if status is not None:
        frontmatter["status"] = status
    if priority is not None:
        frontmatter["priority"] = priority

    # Preserve any custom metadata keys
    for k, v in data.items():
        if k not in (
            "title",
            "label",
            "tags",
            "description",
            "content",
            "text",
            "status",
            "priority",
            "updated_at",
            "revision",
            "content_hash",
        ):
            if isinstance(v, (str, int, float, bool, list, dict)):
                frontmatter[k] = v

    # Build markdown body
    fm_str = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()
    
    body_lines = [f"# {title}\n"]
    if description and description.strip() != content.strip():
        body_lines.append(f"**Description:** {description.strip()}\n")
    if content and content.strip():
        # Avoid duplicate title heading if content already begins with it
        if not content.strip().startswith(f"# {title}"):
            body_lines.append(content.strip())
        else:
            body_lines.append(content.strip())

    md_text = f"---\n{fm_str}\n---\n\n" + "\n".join(body_lines) + "\n"

    if not filename:
        filename = f"{_sanitize_filename(node_id)}.md"
    elif not filename.endswith(".md"):
        filename = f"{filename}.md"

    out_file = target_dir / filename
    out_file.write_text(md_text, encoding="utf-8")
    return out_file


def export_nodes_to_markdown(
    nodes: List[Dict[str, Any]],
    output_dir: Union[str, Path] = DEFAULT_VAULT_TASKFOREST_PATH,
    vault_root: Optional[Union[str, Path]] = None,
    enforce_vault_root: bool = False,
) -> List[Path]:
    """Exports a list of nodes to individual Markdown files in output_dir.

    Args:
        nodes: List of canvas node dictionaries.
        output_dir: Destination directory.
        vault_root: Optional canonical vault root.
        enforce_vault_root: If True, validates target_dir against canonical Vault root.

    Returns:
        List of Paths of created markdown files.
    """
    written_paths: List[Path] = []
    for node in nodes:
        path = export_node_to_markdown(
            node,
            output_dir=output_dir,
            vault_root=vault_root,
            enforce_vault_root=enforce_vault_root,
        )
        written_paths.append(path)
    return written_paths


def export_to_obsidian_canvas(
    nodes: List[Dict[str, Any]],
    edges: Optional[List[Dict[str, Any]]] = None,
    output_path: Optional[Union[str, Path]] = None,
    link_as_file_nodes: bool = False,
    file_prefix: str = "",
    vault_root: Optional[Union[str, Path]] = None,
    enforce_vault_root: bool = False,
) -> Dict[str, Any]:
    """Generates Obsidian Canvas v1.0 JSON format and optionally saves it to disk.

    Args:
        nodes: List of nodes.
        edges: Optional list of edges.
        output_path: Path to write .canvas file.
        link_as_file_nodes: If True, convert nodes to Obsidian file-link nodes.
        file_prefix: Optional prefix for linked markdown filenames.
        vault_root: Optional canonical vault root.
        enforce_vault_root: If True, validates parent directory against canonical Vault root.

    Returns:
        Obsidian Canvas v1.0 compatible dictionary.
    """
    canvas_nodes: List[Dict[str, Any]] = []
    for n in nodes:
        node_id = str(n.get("id", ""))
        # Handle position coordinates (both flat x,y and ReactFlow {position: {x, y}})
        if "x" in n and "y" in n:
            x = float(n["x"])
            y = float(n["y"])
        elif isinstance(n.get("position"), dict):
            pos = n["position"]
            x = float(pos.get("x", 0))
            y = float(pos.get("y", 0))
        else:
            x, y = 0.0, 0.0

        width = float(n.get("width", 250))
        height = float(n.get("height", 160))

        raw_data = n.get("data")
        data: Dict[str, Any] = raw_data if isinstance(raw_data, dict) else {}
        title = data.get("title") or data.get("label") or n.get("title") or n.get("label") or ""
        content = str(
            data.get("content")
            or data.get("text")
            or n.get("content")
            or n.get("text")
            or data.get("description")
            or n.get("description")
            or ""
        )

        c_node: Dict[str, Any] = {
            "id": node_id,
            "x": int(x),
            "y": int(y),
            "width": int(width),
            "height": int(height),
        }

        color = n.get("color") or data.get("color")
        if color:
            c_node["color"] = str(color)

        if link_as_file_nodes:
            c_node["type"] = "file"
            rel_file = f"{file_prefix}{_sanitize_filename(node_id)}.md"
            c_node["file"] = rel_file
        else:
            c_node["type"] = "text"
            if title and content and not content.startswith(f"# {title}"):
                text_val = f"## {title}\n\n{content}"
            else:
                text_val = content or title or f"Node {node_id}"
            c_node["text"] = text_val

        canvas_nodes.append(c_node)

    canvas_edges: List[Dict[str, Any]] = []
    if edges:
        for idx, e in enumerate(edges):
            edge_id = str(e.get("id") or f"edge_{idx}")
            from_node = str(e.get("fromNode") or e.get("source") or "")
            to_node = str(e.get("toNode") or e.get("target") or "")
            
            c_edge: Dict[str, Any] = {
                "id": edge_id,
                "fromNode": from_node,
                "toNode": to_node,
            }

            from_side = e.get("fromSide") or e.get("sourceHandle")
            if from_side in ("top", "right", "bottom", "left"):
                c_edge["fromSide"] = from_side

            to_side = e.get("toSide") or e.get("targetHandle")
            if to_side in ("top", "right", "bottom", "left"):
                c_edge["toSide"] = to_side

            if e.get("label"):
                c_edge["label"] = str(e["label"])
            if e.get("color"):
                c_edge["color"] = str(e["color"])

            canvas_edges.append(c_edge)

    canvas_doc = {
        "nodes": canvas_nodes,
        "edges": canvas_edges,
    }

    if output_path:
        if enforce_vault_root:
            out_p = validate_vault_path(output_path, vault_root=vault_root)
        else:
            out_p = Path(os.path.expanduser(str(output_path))).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(canvas_doc, indent=2, ensure_ascii=False), encoding="utf-8")

    return canvas_doc


def export_canvas_bundle(
    nodes: List[Dict[str, Any]],
    edges: Optional[List[Dict[str, Any]]] = None,
    canvas_name: str = "task_forest",
    output_dir: Union[str, Path] = DEFAULT_VAULT_TASKFOREST_PATH,
    export_individual_md: bool = True,
    link_as_file_nodes: bool = False,
    vault_root: Optional[Union[str, Path]] = None,
    enforce_vault_root: bool = False,
) -> Dict[str, Any]:
    """Exports both individual markdown files and an Obsidian .canvas file into output_dir.

    Args:
        nodes: List of canvas nodes.
        edges: Optional list of edges.
        canvas_name: Base filename for the .canvas file.
        output_dir: Directory path (defaults to TaskForest vault folder).
        export_individual_md: If True, writes each node as a .md file.
        link_as_file_nodes: If True, .canvas references the created .md files.
        vault_root: Optional canonical vault root.
        enforce_vault_root: If True, validates target_dir against canonical Vault root.

    Returns:
        Dictionary with exported canvas file path, markdown file paths, and canvas data.
    """
    if enforce_vault_root:
        target_dir = validate_vault_path(output_dir, vault_root=vault_root)
    else:
        target_dir = Path(os.path.expanduser(str(output_dir))).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    markdown_paths: List[Path] = []
    if export_individual_md:
        markdown_paths = export_nodes_to_markdown(
            nodes,
            output_dir=target_dir,
            vault_root=vault_root,
            enforce_vault_root=enforce_vault_root,
        )

    canvas_filename = f"{_sanitize_filename(canvas_name)}.canvas"
    canvas_path = target_dir / canvas_filename

    canvas_data = export_to_obsidian_canvas(
        nodes=nodes,
        edges=edges,
        output_path=canvas_path,
        link_as_file_nodes=link_as_file_nodes,
        file_prefix="",
        vault_root=vault_root,
        enforce_vault_root=enforce_vault_root,
    )

    return {
        "canvas_path": str(canvas_path),
        "canvas_data": canvas_data,
        "markdown_files": [str(p) for p in markdown_paths],
        "node_count": len(nodes),
        "edge_count": len(edges or []),
    }
