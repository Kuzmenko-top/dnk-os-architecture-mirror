# --- DNK-MRH-HEADER ---
# mrh_id: "tests/canvas/test_mindmap_auto_cluster.py"
# purpose: "Integration and contract tests for Phase 11.2 AI Auto-Clusterization (frontend node, backend k-means, toolbar trigger, store persistence)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

from pathlib import Path
import pytest
from core.mindmap.auto_cluster import auto_cluster_engine, MindMapAutoClusterEngine
from core.mindmap.cluster_names import cluster_name_synthesizer

REPO_ROOT = Path(__file__).resolve().parents[2]
WEB_CANVAS_DIR = REPO_ROOT / "apps" / "web" / "components" / "canvas"


def test_cluster_node_component_exists_and_has_mrh():
    """Verify MindMapClusterNode.tsx exists and adheres to DNK-MRH-HEADER standard."""
    cluster_node_file = WEB_CANVAS_DIR / "nodes" / "MindMapClusterNode.tsx"
    assert cluster_node_file.is_file(), "MindMapClusterNode.tsx missing"
    content = cluster_node_file.read_text(encoding="utf-8")
    assert "DNK-MRH-HEADER" in content, "MRH header missing in MindMapClusterNode.tsx"
    assert "export default function MindMapClusterNode" in content
    assert "export interface MindMapClusterData" in content


def test_canvas_engine_registers_cluster_node():
    """Verify CanvasEngine.tsx imports and registers MindMapClusterNode in nodeTypes."""
    engine_file = WEB_CANVAS_DIR / "CanvasEngine.tsx"
    assert engine_file.is_file(), "CanvasEngine.tsx missing"
    content = engine_file.read_text(encoding="utf-8")
    assert "MindMapClusterNode" in content, "MindMapClusterNode not imported in CanvasEngine"
    assert "mindMapCluster: MindMapClusterNode" in content or "MindMapClusterNode," in content


def test_canvas_store_has_autocluster_methods():
    """Verify canvasStore.ts declares isClustering and autoClusterMindMap."""
    store_file = REPO_ROOT / "apps" / "web" / "store" / "canvasStore.ts"
    assert store_file.is_file(), "canvasStore.ts missing"
    content = store_file.read_text(encoding="utf-8")
    assert "isClustering: boolean" in content
    assert "autoClusterMindMap" in content


def test_toolbar_has_autocluster_button():
    """Verify StitchSpatialToolbar.tsx provides the auto-cluster button with data-testid."""
    toolbar_file = WEB_CANVAS_DIR / "StitchSpatialToolbar.tsx"
    assert toolbar_file.is_file(), "StitchSpatialToolbar.tsx missing"
    content = toolbar_file.read_text(encoding="utf-8")
    assert 'data-testid="btn-auto-cluster"' in content
    assert "handleAutoCluster" in content
    assert "autoClusterMindMap" in content


def test_backend_clustering_pipeline_e2e():
    """Verify end-to-end clustering algorithm with 12 heterogeneous nodes."""
    raw_nodes = [
        {"id": "n1", "data": {"title": "Shopify Theme Redesign", "description": "Liquid AST modernization", "tags": ["ecommerce"]}},
        {"id": "n2", "data": {"title": "Product Catalog Sync", "description": "Shopify admin API inventory", "tags": ["ecommerce"]}},
        {"id": "n3", "data": {"title": "Checkout UI Extension", "description": "Custom checkout discounts", "tags": ["ecommerce"]}},
        {"id": "n4", "data": {"title": "TikTok UGC Video", "description": "Vertical 9:16 reels for hook", "tags": ["media"]}},
        {"id": "n5", "data": {"title": "Motion Ad Generation", "description": "Remotion video rendering pipeline", "tags": ["media"]}},
        {"id": "n6", "data": {"title": "Audio Track Voiceover", "description": "AI voice dubbing for video ads", "tags": ["media"]}},
        {"id": "n7", "data": {"title": "Email Drip Campaign", "description": "Klaviyo abandoned cart flow", "tags": ["marketing"]}},
        {"id": "n8", "data": {"title": "Meta Ad Creative", "description": "Facebook dynamic product ads", "tags": ["marketing"]}},
        {"id": "n9", "data": {"title": "SEO Backlinks Strategy", "description": "High DA guest posting outreach", "tags": ["marketing"]}},
        {"id": "n10", "data": {"title": "Customer Survey Analysis", "description": "Voice of customer insights", "tags": ["research"]}},
        {"id": "n11", "data": {"title": "Competitor Benchmarking", "description": "Price matching research", "tags": ["research"]}},
        {"id": "n12", "data": {"title": "Brand Positioning Document", "description": "Core value proposition synthesis", "tags": ["research"]}},
    ]

    result = auto_cluster_engine.cluster_nodes(raw_nodes, language="uk")
    assert result["status"] == "success"
    assert len(result["clusters"]) >= 2
    assert len(result["clusters"]) <= 5
    assert len(result["repositioned_nodes"]) == 12

    # Verify cluster naming
    for c in result["clusters"]:
        assert c["name"]
        assert len(c["node_ids"]) > 0
