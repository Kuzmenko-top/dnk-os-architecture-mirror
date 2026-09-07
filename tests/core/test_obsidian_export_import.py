# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_obsidian_export_import.py"
# purpose: "Unit and integration tests for Obsidian Canvas & Markdown export/import engine."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import json
import time
import pytest
from pathlib import Path

from core.obsidian.export_canvas import (
    export_node_to_markdown,
    export_nodes_to_markdown,
    export_to_obsidian_canvas,
    export_canvas_bundle,
    _sanitize_filename,
    validate_vault_path,
    get_canonical_vault_root,
    get_canonical_task_forest_dir,
    DEFAULT_VAULT_ROOT,
    DEFAULT_TASK_FOREST_DIR,
)
from core.obsidian.import_canvas import (
    parse_canvas_file,
    parse_markdown_file,
    resolve_conflicts,
    import_canvas_and_markdown,
    import_obsidian_folder,
)


def test_sanitize_filename():
    assert _sanitize_filename("Node: 1/2? *test*") == "Node_12_test"
    assert _sanitize_filename("   ") == "unnamed_node"


def test_export_node_to_markdown(tmp_path: Path):
    node = {
        "id": "node_101",
        "type": "text",
        "position": {"x": 100, "y": 200},
        "data": {
            "title": "Architectural Spike",
            "tags": ["core", "architecture"],
            "description": "Short summary of spike",
            "content": "Detailed body content for the architectural spike.",
            "status": "in_progress",
            "priority": "high",
        },
    }

    out_file = export_node_to_markdown(node, output_dir=tmp_path)
    assert out_file.exists()
    assert out_file.suffix == ".md"

    content = out_file.read_text(encoding="utf-8")
    assert "id: node_101" in content
    assert "Architectural Spike" in content
    assert "core" in content
    assert "architecture" in content
    assert "Detailed body content" in content


def test_export_nodes_to_markdown(tmp_path: Path):
    nodes = [
        {"id": f"node_{i}", "type": "text", "data": {"title": f"Task {i}"}}
        for i in range(3)
    ]
    created = export_nodes_to_markdown(nodes, output_dir=tmp_path)
    assert len(created) == 3
    for p in created:
        assert p.exists()


def test_export_to_obsidian_canvas(tmp_path: Path):
    nodes = [
        {
            "id": "n1",
            "x": 50,
            "y": 100,
            "width": 300,
            "height": 200,
            "data": {"title": "Start Node", "text": "Beginning step"},
        },
        {
            "id": "n2",
            "position": {"x": 400, "y": 100},
            "width": 250,
            "height": 180,
            "data": {"title": "End Node", "text": "Completion step"},
        },
    ]
    edges = [
        {
            "id": "e1-2",
            "source": "n1",
            "target": "n2",
            "fromSide": "right",
            "toSide": "left",
            "label": "transitions to",
        }
    ]

    out_canvas = tmp_path / "diagram.canvas"
    doc = export_to_obsidian_canvas(nodes, edges, output_path=out_canvas)

    assert out_canvas.exists()
    assert "nodes" in doc
    assert "edges" in doc
    assert len(doc["nodes"]) == 2
    assert len(doc["edges"]) == 1
    assert doc["edges"][0]["fromNode"] == "n1"
    assert doc["edges"][0]["toNode"] == "n2"
    assert doc["edges"][0]["label"] == "transitions to"


def test_export_canvas_bundle(tmp_path: Path):
    nodes = [
        {"id": "task_a", "data": {"title": "Task Alpha", "content": "Alpha notes"}},
        {"id": "task_b", "data": {"title": "Task Beta", "content": "Beta notes"}},
    ]
    edges = [{"id": "edge_ab", "source": "task_a", "target": "task_b"}]

    res = export_canvas_bundle(
        nodes=nodes,
        edges=edges,
        canvas_name="test_flow",
        output_dir=tmp_path,
        export_individual_md=True,
    )

    assert res["node_count"] == 2
    assert res["edge_count"] == 1
    assert Path(res["canvas_path"]).exists()
    assert len(res["markdown_files"]) == 2


def test_parse_canvas_file(tmp_path: Path):
    canvas_dict = {
        "nodes": [
            {
                "id": "c1",
                "x": 100,
                "y": 150,
                "width": 260,
                "height": 140,
                "type": "text",
                "text": "# Header Title\nDescription body goes here.",
            }
        ],
        "edges": [
            {
                "id": "edge1",
                "fromNode": "c1",
                "toNode": "c2",
                "fromSide": "right",
                "toSide": "left",
            }
        ],
    }
    c_file = tmp_path / "sample.canvas"
    c_file.write_text(json.dumps(canvas_dict), encoding="utf-8")

    parsed = parse_canvas_file(c_file)
    assert len(parsed["nodes"]) == 1
    assert len(parsed["edges"]) == 1
    assert parsed["nodes"][0]["id"] == "c1"
    assert parsed["nodes"][0]["data"]["title"] == "Header Title"
    assert "Description body" in parsed["nodes"][0]["data"]["description"]


def test_parse_markdown_file(tmp_path: Path):
    md_content = """---
id: note_42
type: task
title: Deployment Task
tags:
  - devops
  - release
updated_at: 1725400000.0
---

# Deployment Task

**Description:** Execute automated deployment steps.

Detailed checklist and logs. #critical
"""
    md_file = tmp_path / "task_42.md"
    md_file.write_text(md_content, encoding="utf-8")

    parsed = parse_markdown_file(md_file)
    assert parsed["id"] == "note_42"
    assert parsed["title"] == "Deployment Task"
    assert "devops" in parsed["tags"]
    assert "release" in parsed["tags"]
    assert "critical" in parsed["tags"]
    assert "Execute automated deployment steps." in parsed["description"]


def test_resolve_conflicts_last_write_wins():
    now = time.time()
    canvas_nodes = [
        {
            "id": "item_1",
            "type": "text",
            "position": {"x": 50, "y": 50},
            "data": {
                "title": "Canvas Title",
                "tags": ["canvas_tag"],
                "content": "Old canvas content",
            },
            "updated_at": now - 100,
        }
    ]

    # Markdown is newer
    md_nodes = [
        {
            "id": "item_1",
            "type": "text",
            "data": {
                "title": "Markdown Title Updated",
                "tags": ["md_tag"],
                "content": "New markdown content",
            },
            "updated_at": now,
        }
    ]

    merged = resolve_conflicts(canvas_nodes, md_nodes, strategy="last-write-wins")
    assert len(merged) == 1
    assert merged[0]["id"] == "item_1"
    # Position preserved from canvas
    assert merged[0]["position"] == {"x": 50, "y": 50}
    # Title updated from newer markdown
    assert merged[0]["data"]["title"] == "Markdown Title Updated"


def test_import_canvas_and_markdown(tmp_path: Path):
    # 1. Export bundle
    nodes = [
        {
            "id": "sync_node",
            "x": 120,
            "y": 240,
            "width": 280,
            "height": 160,
            "data": {"title": "Sync Node", "text": "Sync content", "tags": ["sync"]},
        }
    ]
    edges = []
    bundle = export_canvas_bundle(nodes, edges, "sync_test", output_dir=tmp_path)

    # 2. Import back
    imported = import_canvas_and_markdown(
        canvas_source=bundle["canvas_path"],
        markdown_sources=bundle["markdown_files"],
    )

    assert len(imported["nodes"]) == 1
    node = imported["nodes"][0]
    assert node["id"] == "sync_node"
    assert node["x"] == 120
    assert node["y"] == 240


def test_canonical_vault_paths_and_env_overrides(monkeypatch, tmp_path: Path):
    # Base canonical root
    vault_root = get_canonical_vault_root()
    assert vault_root.name == "DNK_HUB My Notes"
    task_forest = get_canonical_task_forest_dir()
    assert task_forest.name == "TaskForest"
    assert task_forest.parent == vault_root

    # Test environment variable overrides
    custom_vault = tmp_path / "CustomVault"
    custom_vault.mkdir()
    monkeypatch.setenv("DNK_OBSIDIAN_VAULT_ROOT", str(custom_vault))
    assert get_canonical_vault_root() == custom_vault.resolve()

    custom_tf = custom_vault / "MyForest"
    monkeypatch.setenv("DNK_OBSIDIAN_TASK_FOREST_DIR", str(custom_tf))
    assert get_canonical_task_forest_dir() == custom_tf.resolve()


def test_validate_vault_path_success(tmp_path: Path):
    vault_root = tmp_path / "MyVault"
    vault_root.mkdir()

    # None defaults to TaskForest inside vault_root
    default_res = validate_vault_path(None, vault_root=vault_root)
    assert default_res == (vault_root / "TaskForest").resolve()

    # Subdirectory within vault_root succeeds
    sub_dir = vault_root / "Notes" / "Daily"
    res = validate_vault_path(sub_dir, vault_root=vault_root)
    assert res == sub_dir.resolve()


def test_validate_vault_path_traversal_attacks(tmp_path: Path):
    vault_root = tmp_path / "SecureVault"
    vault_root.mkdir()

    # Relative path traversal outside vault
    with pytest.raises(ValueError, match="Path traversal forbidden"):
        validate_vault_path(vault_root / ".." / "outside", vault_root=vault_root)

    # String with ../.. escape
    with pytest.raises(ValueError, match="Path traversal forbidden"):
        validate_vault_path("../../etc/passwd", vault_root=vault_root)

    # Absolute path outside vault
    with pytest.raises(ValueError, match="Path traversal forbidden"):
        validate_vault_path("/etc/hosts", vault_root=vault_root)

    with pytest.raises(ValueError, match="Path traversal forbidden"):
        validate_vault_path(tmp_path / "other_dir", vault_root=vault_root)


def test_deterministic_lww_tie_breaker_revision():
    # Equal timestamps, different revisions
    ts = 1700000000.0
    c_node = {
        "id": "item_rev",
        "updated_at": ts,
        "revision": 1,
        "data": {"title": "Canvas Title Rev 1", "revision": 1, "updated_at": ts},
    }
    m_node = {
        "id": "item_rev",
        "updated_at": ts,
        "revision": 2,
        "data": {"title": "MD Title Rev 2", "revision": 2, "updated_at": ts},
    }

    # Markdown has higher revision -> MD wins
    merged_m = resolve_conflicts([c_node], [m_node], strategy="last-write-wins")
    assert merged_m[0]["data"]["title"] == "MD Title Rev 2"
    assert merged_m[0]["revision"] == 2

    # Canvas has higher revision -> Canvas wins
    c_node_high = {
        "id": "item_rev",
        "updated_at": ts,
        "revision": 5,
        "data": {"title": "Canvas Title Rev 5", "revision": 5, "updated_at": ts},
    }
    merged_c = resolve_conflicts([c_node_high], [m_node], strategy="last-write-wins")
    assert merged_c[0]["data"]["title"] == "Canvas Title Rev 5"
    assert merged_c[0]["revision"] == 5


def test_deterministic_lww_tie_breaker_content_hash():
    # Equal timestamps and revisions, different content_hash
    ts = 1700000000.0
    rev = 1
    # Hash A > Hash B lexicographically
    c_node = {
        "id": "item_hash",
        "updated_at": ts,
        "revision": rev,
        "content_hash": "aaaa",
        "data": {"title": "Canvas Title A", "content_hash": "aaaa", "updated_at": ts},
    }
    m_node = {
        "id": "item_hash",
        "updated_at": ts,
        "revision": rev,
        "content_hash": "bbbb",
        "data": {"title": "MD Title B", "content_hash": "bbbb", "updated_at": ts},
    }

    # 'bbbb' > 'aaaa', so Markdown wins
    merged = resolve_conflicts([c_node], [m_node], strategy="last-write-wins")
    assert merged[0]["data"]["title"] == "MD Title B"
    assert merged[0]["content_hash"] == "bbbb"

    # Reverse: Canvas has higher hash 'zzzz' > 'bbbb' -> Canvas wins
    c_node_high = {
        "id": "item_hash",
        "updated_at": ts,
        "revision": rev,
        "content_hash": "zzzz",
        "data": {"title": "Canvas Title Z", "content_hash": "zzzz", "updated_at": ts},
    }
    merged_z = resolve_conflicts([c_node_high], [m_node], strategy="last-write-wins")
    assert merged_z[0]["data"]["title"] == "Canvas Title Z"
    assert merged_z[0]["content_hash"] == "zzzz"


def test_export_import_with_revision_and_content_hash(tmp_path: Path):
    node = {
        "id": "hash_node_1",
        "type": "task",
        "revision": 3,
        "updated_at": 1725000000.0,
        "data": {
            "title": "Hashed Task",
            "content": "Secret Task Content",
            "revision": 3,
            "updated_at": 1725000000.0,
        },
    }
    md_file = export_node_to_markdown(node, output_dir=tmp_path)
    content = md_file.read_text(encoding="utf-8")
    assert "revision: 3" in content
    assert "content_hash:" in content

    # Parse back
    parsed = parse_markdown_file(md_file)
    assert parsed["id"] == "hash_node_1"
    assert parsed["revision"] == 3
    assert len(parsed["content_hash"]) == 64  # sha256 hex string
