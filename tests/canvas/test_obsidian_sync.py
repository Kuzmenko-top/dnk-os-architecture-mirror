# --- DNK-MRH-HEADER ---
# mrh_id: "tests/canvas/test_obsidian_sync.py"
# purpose: "E2E tests for Phase 11 Stage 3 Obsidian Canvas synchronization, export, import, and conflict resolution."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import json
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from core.obsidian.export_canvas import (
    export_to_obsidian_canvas,
    export_canvas_bundle,
    export_node_to_markdown,
    validate_vault_path,
    get_canonical_vault_root,
)
from core.obsidian.import_canvas import (
    parse_canvas_file,
    parse_markdown_file,
    resolve_conflicts,
    import_obsidian_folder,
)


@pytest.fixture
def five_nodes_and_edges():
    nodes = [
        {
            "id": "node-1",
            "type": "task",
            "position": {"x": 100, "y": 100},
            "width": 260,
            "height": 140,
            "data": {
                "title": "Architecture Design",
                "label": "Architecture Design",
                "description": "Initial design specs for task forest",
                "status": "completed",
                "tags": ["architecture", "core"],
            },
        },
        {
            "id": "node-2",
            "type": "task",
            "position": {"x": 450, "y": 100},
            "width": 260,
            "height": 140,
            "data": {
                "title": "Backend Sync Engine",
                "label": "Backend Sync Engine",
                "description": "Python modules for export and import",
                "status": "completed",
                "tags": ["backend", "python"],
            },
        },
        {
            "id": "node-3",
            "type": "task",
            "position": {"x": 800, "y": 100},
            "width": 260,
            "height": 140,
            "data": {
                "title": "Frontend SyncBar UI",
                "label": "Frontend SyncBar UI",
                "description": "React component and Zustand store actions",
                "status": "in_progress",
                "tags": ["frontend", "react"],
            },
        },
        {
            "id": "node-4",
            "type": "decision",
            "position": {"x": 450, "y": 350},
            "width": 240,
            "height": 120,
            "data": {
                "title": "Conflict Strategy Gate",
                "label": "Conflict Strategy Gate",
                "description": "Evaluate last-write-wins vs merge-tags",
                "status": "pending",
                "tags": ["decision", "quality"],
            },
        },
        {
            "id": "node-5",
            "type": "milestone",
            "position": {"x": 800, "y": 350},
            "width": 280,
            "height": 160,
            "data": {
                "title": "E2E Verification & Release",
                "label": "E2E Verification & Release",
                "description": "Full end-to-end sync verification",
                "status": "pending",
                "tags": ["milestone", "release"],
            },
        },
    ]

    edges = [
        {"id": "e1-2", "source": "node-1", "target": "node-2", "label": "enables"},
        {"id": "e2-3", "source": "node-2", "target": "node-3", "label": "powers"},
        {"id": "e2-4", "source": "node-2", "target": "node-4", "label": "informs"},
        {"id": "e4-5", "source": "node-4", "target": "node-5", "label": "certifies"},
    ]
    return nodes, edges


def test_export_five_nodes_to_canvas(tmp_path: Path, five_nodes_and_edges):
    """Test export: 5 nodes -> .canvas file -> verify valid JSON canvas structure."""
    nodes, edges = five_nodes_and_edges
    canvas_path = tmp_path / "task_forest_e2e.canvas"

    canvas_doc = export_to_obsidian_canvas(nodes, edges, output_path=canvas_path)

    # 1. Verify returned dictionary structure
    assert "nodes" in canvas_doc
    assert "edges" in canvas_doc
    assert len(canvas_doc["nodes"]) == 5
    assert len(canvas_doc["edges"]) == 4

    # 2. Verify file on disk
    assert canvas_path.exists()
    content = json.loads(canvas_path.read_text(encoding="utf-8"))
    assert len(content["nodes"]) == 5
    assert len(content["edges"]) == 4

    # 3. Verify node coordinate and text attributes
    node_map = {n["id"]: n for n in content["nodes"]}
    assert "node-1" in node_map
    n1 = node_map["node-1"]
    assert n1["x"] == 100
    assert n1["y"] == 100
    assert n1["width"] == 260
    assert n1["height"] == 140
    assert "Architecture Design" in n1["text"]
    assert "Initial design specs" in n1["text"]


def test_import_canvas_to_five_nodes(tmp_path: Path, five_nodes_and_edges):
    """Test import: .canvas file -> 5 nodes -> verify restored positions and data."""
    nodes, edges = five_nodes_and_edges
    canvas_path = tmp_path / "task_forest_import.canvas"

    # Export first
    export_to_obsidian_canvas(nodes, edges, output_path=canvas_path)

    # Now parse back
    parsed = parse_canvas_file(canvas_path)
    imported_nodes = parsed["nodes"]
    imported_edges = parsed["edges"]

    assert len(imported_nodes) == 5
    assert len(imported_edges) == 4

    imported_map = {n["id"]: n for n in imported_nodes}
    for orig in nodes:
        node_id = orig["id"]
        assert node_id in imported_map
        imp = imported_map[node_id]

        # Verify position
        assert imp["position"]["x"] == orig["position"]["x"]
        assert imp["position"]["y"] == orig["position"]["y"]

        # Verify reconstructed data from canvas text
        assert imp["data"]["title"] == orig["data"]["title"]
        assert imp["data"]["description"] == orig["data"]["description"]

    # Verify edge connectivity
    edge_ids = {e["id"] for e in imported_edges}
    assert "e1-2" in edge_ids
    assert "e2-3" in edge_ids


def test_conflict_resolution_last_write_wins(tmp_path: Path, five_nodes_and_edges):
    """Test conflict resolution: concurrent edits in canvas and Obsidian markdown resolve to last-write-wins."""
    nodes, edges = five_nodes_and_edges
    export_dir = tmp_path / "vault_sync"
    export_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initial export of bundle (markdowns + canvas)
    bundle = export_canvas_bundle(nodes, edges, output_dir=export_dir, canvas_name="test_sync")
    canvas_file = Path(bundle["canvas_path"])
    assert canvas_file.exists()
    assert len(bundle["markdown_files"]) == 5

    # 2. Simulate Markdown update in Obsidian with newer timestamp
    md_files = [Path(p) for p in bundle["markdown_files"]]
    node1_file = next(p for p in md_files if "node-1" in p.name)
    assert node1_file.exists()
    time.sleep(0.05)

    updated_md_content = """---
id: node-1
title: Architecture Design (Obsidian v2)
status: in_progress
tags:
  - architecture
  - core
  - obsidian-updated
---
# Architecture Design (Obsidian v2)

Updated directly inside Obsidian note with new architectural specs.
"""
    node1_file.write_text(updated_md_content, encoding="utf-8")

    # 3. Simulate Canvas local change for a different node
    canvas_parsed = parse_canvas_file(canvas_file)
    canvas_nodes = canvas_parsed["nodes"]
    for cn in canvas_nodes:
        if cn["id"] == "node-3":
            cn["data"]["title"] = "Frontend SyncBar UI (Canvas v2)"
            cn["position"]["x"] = 850

    # 4. Read markdowns and run conflict resolution
    md_nodes = []
    for f in export_dir.glob("*.md"):
        parsed = parse_markdown_file(f)
        if parsed:
            md_nodes.append(parsed)

    merged_nodes = resolve_conflicts(canvas_nodes, md_nodes, strategy="last-write-wins")
    merged_map = {n["id"]: n for n in merged_nodes}

    # Node-1 was updated in markdown (newer mtime) -> should adopt markdown updates
    assert "node-1" in merged_map
    n1 = merged_map["node-1"]
    assert "Obsidian v2" in n1["data"]["title"]
    assert "obsidian-updated" in n1["data"]["tags"]

    # Node-3 was modified in canvas -> preserves canvas position and title
    assert "node-3" in merged_map
    n3 = merged_map["node-3"]
    assert n3["data"]["title"] == "Frontend SyncBar UI (Canvas v2)"
    assert n3["position"]["x"] == 850


def test_websocket_obsidian_sync_path_traversal_rejected():
    """Verify that WebSocket OBSIDIAN_SYNC_REQUEST rejects path traversal attempts."""
    client = TestClient(app)
    with client.websocket_connect("/api/v3/ws/canvas/ws-test-security") as websocket:
        # Initial user connection message
        presence = websocket.receive_json()
        assert presence.get("type") == "CONNECTED"

        # Attempt path traversal via relative escape
        websocket.send_json({
            "type": "OBSIDIAN_SYNC_REQUEST",
            "direction": "export",
            "target_dir": "../../../../../etc",
            "canvas_name": "malicious",
            "nodes": [{"id": "n1", "type": "task", "data": {"title": "Exploit"}}],
        })

        resp = websocket.receive_json()
        assert resp.get("type") == "OBSIDIAN_SYNC_STATUS"
        assert resp.get("status") == "error"
        assert "Path traversal forbidden" in resp.get("error", "")

        # Attempt path traversal via absolute path outside vault
        websocket.send_json({
            "type": "OBSIDIAN_SYNC_REQUEST",
            "direction": "export",
            "target_dir": "/tmp/unauthorized_vault",
            "canvas_name": "malicious2",
            "nodes": [{"id": "n1", "type": "task", "data": {"title": "Exploit2"}}],
        })

        resp2 = websocket.receive_json()
        assert resp2.get("type") == "OBSIDIAN_SYNC_STATUS"
        assert resp2.get("status") == "error"
        assert "Path traversal forbidden" in resp2.get("error", "")


def test_websocket_obsidian_sync_canonical_vault_success(monkeypatch, tmp_path: Path):
    """Verify that WebSocket OBSIDIAN_SYNC_REQUEST succeeds when target_dir is within canonical Vault root."""
    vault_root = tmp_path / "DNK_HUB My Notes"
    vault_root.mkdir()
    monkeypatch.setenv("DNK_OBSIDIAN_VAULT_ROOT", str(vault_root))

    client = TestClient(app)
    with client.websocket_connect("/api/v3/ws/canvas/ws-test-valid") as websocket:
        presence = websocket.receive_json()
        assert presence.get("type") == "CONNECTED"

        # Valid subfolder inside vault root
        target_dir = vault_root / "TaskForest"
        websocket.send_json({
            "type": "OBSIDIAN_SYNC_REQUEST",
            "direction": "export",
            "target_dir": str(target_dir),
            "canvas_name": "valid_export",
            "nodes": [{"id": "n1", "type": "task", "data": {"title": "Valid Node"}}],
        })

        resp = websocket.receive_json()
        assert resp.get("type") == "OBSIDIAN_SYNC_STATUS"
        assert resp.get("status") == "success"
        assert resp.get("direction") == "export"
        assert (target_dir / "valid_export.canvas").exists()
