# --- DNK-MRH-HEADER ---
# mrh_id: "core/obsidian/import_canvas.py"
# purpose: "Import Obsidian Canvas and Markdown files into Canvas nodes and edges with deterministic LWW tie-breaker (updated_at, revision, content_hash) and path traversal validation."
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
from typing import Dict, List, Any, Optional, Union, Tuple
import yaml

from .export_canvas import (
    DEFAULT_VAULT_TASKFOREST_PATH,
    DEFAULT_VAULT_ROOT,
    DEFAULT_TASK_FOREST_DIR,
    get_canonical_vault_root,
    get_canonical_task_forest_dir,
    validate_vault_path,
)


def parse_canvas_file(canvas_source: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
    """Parses an Obsidian .canvas JSON file or dict into standardized nodes and edges.

    Args:
        canvas_source: File path (str/Path) or raw canvas dict.

    Returns:
        Dict with standardized 'nodes' and 'edges'.
    """
    mtime = time.time()
    if isinstance(canvas_source, str) and canvas_source.startswith("vault:"):
        sub = canvas_source[6:].lstrip("/\\")
        canvas_source = get_canonical_vault_root() / sub

    if isinstance(canvas_source, (str, Path)):
        p = Path(canvas_source)
        if not p.exists():
            raise FileNotFoundError(f"Canvas file not found: {canvas_source}")
        mtime = os.path.getmtime(p)
        raw_text = p.read_text(encoding="utf-8")
        raw_data = json.loads(raw_text)
    elif isinstance(canvas_source, dict):
        raw_data = canvas_source
    else:
        raise ValueError(f"Invalid canvas source type: {type(canvas_source)}")

    raw_nodes: List[Dict[str, Any]] = raw_data.get("nodes", [])
    raw_edges: List[Dict[str, Any]] = raw_data.get("edges", [])

    nodes: List[Dict[str, Any]] = []
    for rn in raw_nodes:
        node_id = str(rn.get("id", ""))
        x = float(rn.get("x", 0.0))
        y = float(rn.get("y", 0.0))
        width = float(rn.get("width", 250.0))
        height = float(rn.get("height", 160.0))
        node_type = str(rn.get("type", "text"))

        text = str(rn.get("text", ""))
        file_ref = str(rn.get("file", ""))
        url_ref = str(rn.get("url", ""))
        label = str(rn.get("label", ""))

        # Derive title and description from text
        title = label
        description = ""
        if text:
            lines = text.strip().split("\n")
            if lines and lines[0].startswith("#"):
                title = lines[0].lstrip("#").strip()
                description = "\n".join(lines[1:]).strip()
            else:
                title = lines[0] if lines else f"Node {node_id}"
                description = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

        node_rev = int(rn.get("revision") or 1)
        node_content = text or description or title
        node_hash = str(rn.get("content_hash") or hashlib.sha256(node_content.encode("utf-8")).hexdigest())

        node_data: Dict[str, Any] = {
            "title": title,
            "description": description,
            "text": text,
            "file": file_ref,
            "url": url_ref,
            "updated_at": mtime,
            "revision": node_rev,
            "content_hash": node_hash,
        }
        if rn.get("color"):
            node_data["color"] = rn.get("color")

        nodes.append({
            "id": node_id,
            "type": node_type,
            "position": {"x": x, "y": y},
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "data": node_data,
            "updated_at": mtime,
            "revision": node_rev,
            "content_hash": node_hash,
        })

    edges: List[Dict[str, Any]] = []
    for idx, re_edge in enumerate(raw_edges):
        edge_id = str(re_edge.get("id") or f"edge_{idx}")
        from_node = str(re_edge.get("fromNode") or re_edge.get("source") or "")
        to_node = str(re_edge.get("toNode") or re_edge.get("target") or "")
        from_side = re_edge.get("fromSide") or re_edge.get("sourceHandle")
        to_side = re_edge.get("toSide") or re_edge.get("targetHandle")

        edge_dict: Dict[str, Any] = {
            "id": edge_id,
            "source": from_node,
            "target": to_node,
            "fromNode": from_node,
            "toNode": to_node,
            "fromSide": from_side,
            "toSide": to_side,
            "sourceHandle": from_side,
            "targetHandle": to_side,
        }
        if re_edge.get("label"):
            edge_dict["label"] = str(re_edge.get("label"))
        if re_edge.get("color"):
            edge_dict["color"] = str(re_edge.get("color"))

        edges.append(edge_dict)

    return {"nodes": nodes, "edges": edges}


def parse_markdown_file(md_path: Union[str, Path]) -> Dict[str, Any]:
    """Parses a Markdown file with optional YAML frontmatter into node data.

    Args:
        md_path: Path to the markdown file.

    Returns:
        Dict representing parsed node data, metadata, tags, and description.
    """
    p = Path(md_path)
    if not p.exists():
        raise FileNotFoundError(f"Markdown file not found: {md_path}")

    mtime = os.path.getmtime(p)
    content = p.read_text(encoding="utf-8")

    frontmatter: Dict[str, Any] = {}
    markdown_body = content

    pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", re.DOTALL)
    match = pattern.match(content.strip())
    if match:
        fm_str = match.group(1)
        markdown_body = match.group(2)
        try:
            loaded_fm = yaml.safe_load(fm_str)
            if isinstance(loaded_fm, dict):
                frontmatter = loaded_fm
        except Exception:
            frontmatter = {}

    node_id = str(frontmatter.get("id") or p.stem)
    node_type = str(frontmatter.get("type") or "text")

    # Extract title
    title = str(frontmatter.get("title") or "")
    if not title:
        # Check first heading in markdown
        h_match = re.search(r"^#\s+(.+)$", markdown_body, re.MULTILINE)
        if h_match:
            title = h_match.group(1).strip()
        else:
            title = p.stem.replace("_", " ").title()

    # Extract tags
    raw_tags = frontmatter.get("tags", [])
    tags: List[str] = []
    if isinstance(raw_tags, list):
        tags = [str(t).strip().lstrip("#") for t in raw_tags if str(t).strip()]
    elif isinstance(raw_tags, str):
        tags = [t.strip().lstrip("#") for t in raw_tags.split(",") if t.strip()]

    # Also capture any inline markdown #tags
    inline_tags = re.findall(r"(?:^|\s)#([a-zA-Z0-9_\-]+)", markdown_body)
    for it in inline_tags:
        if it not in tags:
            tags.append(it)

    # Extract description
    description = str(frontmatter.get("description") or "")
    if not description:
        desc_match = re.search(r"\*\*Description:\*\*\s*(.+)", markdown_body)
        if desc_match:
            description = desc_match.group(1).strip()
        else:
            # Fallback: take first non-heading paragraph
            paragraphs = [para.strip() for para in markdown_body.split("\n\n") if para.strip() and not para.strip().startswith("#")]
            if paragraphs:
                description = paragraphs[0][:200]

    updated_at_val = frontmatter.get("updated_at")
    if updated_at_val is not None:
        try:
            updated_at = float(updated_at_val)
        except (ValueError, TypeError):
            updated_at = mtime
    else:
        updated_at = mtime

    revision_val = frontmatter.get("revision")
    if revision_val is not None:
        try:
            revision = int(revision_val)
        except (ValueError, TypeError):
            revision = 1
    else:
        revision = 1

    content_hash = str(
        frontmatter.get("content_hash")
        or hashlib.sha256(markdown_body.encode("utf-8")).hexdigest()
    )

    data: Dict[str, Any] = {
        "title": title,
        "description": description,
        "tags": tags,
        "content": markdown_body,
        "text": markdown_body,
        "updated_at": updated_at,
        "revision": revision,
        "content_hash": content_hash,
    }
    for k, v in frontmatter.items():
        if k not in data:
            data[k] = v

    return {
        "id": node_id,
        "type": node_type,
        "title": title,
        "description": description,
        "tags": tags,
        "updated_at": updated_at,
        "revision": revision,
        "content_hash": content_hash,
        "data": data,
        "content": markdown_body,
        "file_path": str(p),
    }


def resolve_conflicts(
    canvas_nodes: List[Dict[str, Any]],
    md_nodes: List[Dict[str, Any]],
    strategy: str = "last-write-wins",
) -> List[Dict[str, Any]]:
    """Resolves conflicts between canvas nodes and markdown notes.

    Args:
        canvas_nodes: Nodes parsed from .canvas.
        md_nodes: Nodes parsed from .md files.
        strategy: Conflict resolution strategy (default: 'last-write-wins').
                  LWW uses a deterministic composite key: (updated_at, revision, content_hash).

    Returns:
        Merged list of standardized nodes.
    """
    merged_by_id: Dict[str, Dict[str, Any]] = {}

    for cn in canvas_nodes:
        cid = str(cn.get("id"))
        merged_by_id[cid] = dict(cn)

    for mn in md_nodes:
        mid = str(mn.get("id"))
        if mid not in merged_by_id:
            # New node discovered from markdown
            m_raw = mn.get("data")
            m_data: Dict[str, Any] = dict(m_raw) if isinstance(m_raw, dict) else {}
            m_ts = float(mn.get("updated_at") or m_data.get("updated_at") or time.time())
            m_rev = int(mn.get("revision") or m_data.get("revision") or 1)
            m_hash = str(
                mn.get("content_hash")
                or m_data.get("content_hash")
                or hashlib.sha256((mn.get("content") or "").encode("utf-8")).hexdigest()
            )
            merged_by_id[mid] = {
                "id": mid,
                "type": mn.get("type", "text"),
                "position": {"x": 0.0, "y": 0.0},
                "x": 0.0,
                "y": 0.0,
                "width": 250.0,
                "height": 160.0,
                "data": m_data,
                "updated_at": m_ts,
                "revision": m_rev,
                "content_hash": m_hash,
            }
        else:
            # Conflict exists
            existing = merged_by_id[mid]
            c_raw = existing.get("data")
            c_data: Dict[str, Any] = dict(c_raw) if isinstance(c_raw, dict) else {}
            m_raw = mn.get("data")
            m_data: Dict[str, Any] = dict(m_raw) if isinstance(m_raw, dict) else {}

            c_ts = float(existing.get("updated_at") or c_data.get("updated_at") or 0.0)
            m_ts = float(mn.get("updated_at") or m_data.get("updated_at") or 0.0)

            c_rev = int(existing.get("revision") or c_data.get("revision") or 1)
            m_rev = int(mn.get("revision") or m_data.get("revision") or 1)

            c_hash = str(existing.get("content_hash") or c_data.get("content_hash") or "")
            if not c_hash:
                c_text = str(existing.get("text") or c_data.get("text") or existing.get("content") or c_data.get("content") or "")
                c_hash = hashlib.sha256(c_text.encode("utf-8")).hexdigest()

            m_hash = str(mn.get("content_hash") or m_data.get("content_hash") or "")
            if not m_hash:
                m_text = str(mn.get("text") or m_data.get("text") or mn.get("content") or m_data.get("content") or "")
                m_hash = hashlib.sha256(m_text.encode("utf-8")).hexdigest()

            if strategy == "last-write-wins":
                # Deterministic LWW tie-breaker:
                # Compare (updated_at, revision, content_hash) tuples
                c_key = (c_ts, c_rev, c_hash)
                m_key = (m_ts, m_rev, m_hash)

                if m_key > c_key:
                    # Markdown wins
                    combined_data: Dict[str, Any] = dict(c_data)
                    combined_data.update(m_data)
                    combined_data["revision"] = m_rev
                    combined_data["content_hash"] = m_hash
                    existing["data"] = combined_data
                    existing["updated_at"] = m_ts
                    existing["revision"] = m_rev
                    existing["content_hash"] = m_hash
                    if mn.get("type"):
                        existing["type"] = mn["type"]
                else:
                    # Canvas wins: keep canvas content, merge only non-colliding tags/metadata
                    combined_data = dict(m_data)
                    combined_data.update(c_data)
                    combined_data["revision"] = c_rev
                    combined_data["content_hash"] = c_hash
                    c_tags = c_data.get("tags") or []
                    m_tags = m_data.get("tags") or []
                    combined_tags = list(dict.fromkeys(list(c_tags) + list(m_tags)))
                    combined_data["tags"] = combined_tags
                    existing["data"] = combined_data
                    existing["updated_at"] = c_ts
                    existing["revision"] = c_rev
                    existing["content_hash"] = c_hash
            else:
                # Default merge
                combined_data = dict(c_data)
                combined_data.update(m_data)
                existing["data"] = combined_data
                existing["updated_at"] = max(c_ts, m_ts)

    return list(merged_by_id.values())


def import_obsidian_folder(
    folder_path: Optional[Union[str, Path]] = None,
    canvas_filename: Optional[str] = None,
    conflict_strategy: str = "last-write-wins",
    vault_root: Optional[Union[str, Path]] = None,
    enforce_vault_root: bool = False,
) -> Dict[str, Any]:
    """Imports all nodes and edges from an Obsidian folder containing .canvas and .md files.

    Args:
        folder_path: Directory to scan. Defaults to canonical task_forest_dir.
        canvas_filename: Optional specific .canvas file to target.
        conflict_strategy: Resolution strategy (default: 'last-write-wins').
        vault_root: Optional canonical vault root.
        enforce_vault_root: If True, validates folder_path against canonical Vault root.

    Returns:
        Dict with 'nodes', 'edges', 'canvas_file', and 'md_files_count'.
    """
    if folder_path is None:
        folder = get_canonical_task_forest_dir(
            Path(os.path.expanduser(str(vault_root))).resolve() if vault_root else None
        )
    elif enforce_vault_root:
        folder = validate_vault_path(folder_path, vault_root=vault_root)
    else:
        folder = Path(os.path.expanduser(str(folder_path))).resolve()

    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Directory not found: {folder_path}")

    # Find canvas file
    canvas_file: Optional[Path] = None
    if canvas_filename:
        target_canvas = folder / canvas_filename
        if target_canvas.exists():
            canvas_file = target_canvas
    else:
        canvases = list(folder.glob("*.canvas"))
        if canvases:
            # Pick first or most recently modified
            canvases.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            canvas_file = canvases[0]

    canvas_nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    if canvas_file:
        parsed_canvas = parse_canvas_file(canvas_file)
        canvas_nodes = parsed_canvas.get("nodes", [])
        edges = parsed_canvas.get("edges", [])

    # Find markdown files
    md_files = list(folder.glob("*.md")) + list(folder.glob("nodes/*.md"))
    # Deduplicate paths
    unique_md_files = {p.resolve(): p for p in md_files}.values()

    md_nodes: List[Dict[str, Any]] = []
    for mp in unique_md_files:
        try:
            parsed_md = parse_markdown_file(mp)
            md_nodes.append(parsed_md)
        except Exception:
            continue

    resolved_nodes = resolve_conflicts(
        canvas_nodes=canvas_nodes,
        md_nodes=md_nodes,
        strategy=conflict_strategy,
    )

    return {
        "nodes": resolved_nodes,
        "edges": edges,
        "canvas_file": str(canvas_file) if canvas_file else None,
        "md_files_count": len(md_nodes),
    }


def import_canvas_and_markdown(
    canvas_source: Optional[Union[str, Path, Dict[str, Any]]] = None,
    markdown_sources: Optional[Union[str, Path, List[Union[str, Path]]]] = None,
    conflict_strategy: str = "last-write-wins",
    vault_root: Optional[Union[str, Path]] = None,
    enforce_vault_root: bool = False,
) -> Dict[str, Any]:
    """Flexible importer supporting explicit canvas source and markdown file/directory sources."""
    if enforce_vault_root:
        if isinstance(canvas_source, (str, Path)):
            canvas_source = validate_vault_path(canvas_source, vault_root=vault_root)
        if isinstance(markdown_sources, (str, Path)):
            markdown_sources = validate_vault_path(markdown_sources, vault_root=vault_root)

    canvas_nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    if canvas_source is not None:
        parsed_c = parse_canvas_file(canvas_source)
        canvas_nodes = parsed_c.get("nodes", [])
        edges = parsed_c.get("edges", [])

    md_nodes: List[Dict[str, Any]] = []
    if markdown_sources is not None:
        if isinstance(markdown_sources, (str, Path)):
            p = Path(markdown_sources)
            if p.is_dir():
                for mp in p.glob("**/*.md"):
                    try:
                        md_nodes.append(parse_markdown_file(mp))
                    except Exception:
                        pass
            elif p.is_file():
                md_nodes.append(parse_markdown_file(p))
        elif isinstance(markdown_sources, list):
            for item in markdown_sources:
                p = Path(item)
                if p.is_file():
                    try:
                        md_nodes.append(parse_markdown_file(p))
                    except Exception:
                        pass

    resolved_nodes = resolve_conflicts(
        canvas_nodes=canvas_nodes,
        md_nodes=md_nodes,
        strategy=conflict_strategy,
    )

    return {
        "nodes": resolved_nodes,
        "edges": edges,
        "node_count": len(resolved_nodes),
        "edge_count": len(edges),
    }
