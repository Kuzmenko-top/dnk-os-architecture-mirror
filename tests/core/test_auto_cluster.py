# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_auto_cluster.py"
# purpose: "Unit tests for AI Mind Map Auto-Clusterization (DoD: 10+ nodes -> 3-5 clusters in <2-3s)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import time
import pytest
from core.mindmap.auto_cluster import auto_cluster_engine, MindMapAutoClusterEngine
from core.mindmap.cluster_names import cluster_name_synthesizer
from core.orchestrator.swarm_coordinator import swarm_coordinator


SAMPLE_NODES_12 = [
    # Cluster Domain: Architecture & Database
    {
        "id": "node-1",
        "type": "mindmap_task",
        "data": {
            "title": "PostgreSQL Schema Setup",
            "content": "Configure pgvector extension and relational schemas for hub memory",
            "tags": ["database", "postgres", "infrastructure"]
        },
        "position": {"x": 100, "y": 100}
    },
    {
        "id": "node-2",
        "type": "mindmap_idea",
        "data": {
            "title": "Redis Cache Invalidation",
            "content": "Low-latency pub/sub buffer and session cache tier",
            "tags": ["redis", "backend", "cache"]
        },
        "position": {"x": 150, "y": 120}
    },
    {
        "id": "node-3",
        "type": "mindmap_task",
        "data": {
            "title": "FastAPI REST Router",
            "content": "Core backend API endpoints and WebSocket connection hub",
            "tags": ["api", "fastapi", "server"]
        },
        "position": {"x": 120, "y": 200}
    },

    # Cluster Domain: Frontend Canvas UI
    {
        "id": "node-4",
        "type": "mindmap_idea",
        "data": {
            "title": "React Flow Canvas Stage",
            "content": "Infinite zoom and pan dot-grid interface with obsidian theme",
            "tags": ["frontend", "canvas", "react", "ui"]
        },
        "position": {"x": 800, "y": 100}
    },
    {
        "id": "node-5",
        "type": "mindmap_task",
        "data": {
            "title": "Stitch Spatial Toolbar",
            "content": "Floating vertical action bar with selection, draw, and cluster controls",
            "tags": ["ui", "toolbar", "component", "design"]
        },
        "position": {"x": 850, "y": 150}
    },
    {
        "id": "node-6",
        "type": "mindmap_idea",
        "data": {
            "title": "Tailwind Color Palette",
            "content": "Dark graphite background styling and translucent handles",
            "tags": ["css", "style", "theme", "design"]
        },
        "position": {"x": 820, "y": 220}
    },

    # Cluster Domain: AI Swarm & Agents
    {
        "id": "node-7",
        "type": "mindmap_agent",
        "data": {
            "title": "Gerych Swarm Coordinator",
            "content": "Autonomous LLM worker dispatch and subagent task orchestration",
            "tags": ["swarm", "agent", "ai", "orchestrator"]
        },
        "position": {"x": 200, "y": 800}
    },
    {
        "id": "node-8",
        "type": "mindmap_idea",
        "data": {
            "title": "SCONES Vector Memory",
            "content": "Long-term episodic knowledge retrieval and tenant workspace context",
            "tags": ["rag", "memory", "ai", "model"]
        },
        "position": {"x": 250, "y": 850}
    },
    {
        "id": "node-9",
        "type": "mindmap_task",
        "data": {
            "title": "LLM Inference Pipeline",
            "content": "Gemini and Vertex AI prompt completions with SpendGuard token caps",
            "tags": ["llm", "inference", "prompt", "worker"]
        },
        "position": {"x": 220, "y": 920}
    },

    # Cluster Domain: Security & Quality Gate
    {
        "id": "node-10",
        "type": "mindmap_goal",
        "data": {
            "title": "100% Pytest Green Gate",
            "content": "Automated verification suite ensuring zero regression before PR",
            "tags": ["test", "verification", "pytest", "audit"]
        },
        "position": {"x": 800, "y": 800}
    },
    {
        "id": "node-11",
        "type": "mindmap_task",
        "data": {
            "title": "Adversarial Security Scan",
            "content": "Auditor vs Builder fail-closed gate scanning secret hygiene and AST",
            "tags": ["security", "firewall", "audit", "compliance"]
        },
        "position": {"x": 850, "y": 850}
    },
    {
        "id": "node-12",
        "type": "mindmap_evidence",
        "data": {
            "title": "Master Evidence JSON",
            "content": "Signed cryptographic proof report for release compliance",
            "tags": ["audit", "evidence", "report", "gate"]
        },
        "position": {"x": 820, "y": 920}
    },
]


def test_auto_cluster_dod_10_plus_nodes():
    """
    DoD Test:
    - 10+ nodes input (12 nodes)
    - Produces 3-5 clusters
    - Execution time < 2-3 seconds (target < 500ms)
    """
    start_time = time.perf_counter()
    result = auto_cluster_engine.cluster_nodes(SAMPLE_NODES_12)
    elapsed = time.perf_counter() - start_time

    assert result["status"] == "success"
    assert result["total_nodes"] == 12

    # DoD 1: 3-5 clusters
    clusters = result["clusters"]
    assert 3 <= len(clusters) <= 5, f"Expected 3-5 clusters, got {len(clusters)}"

    # DoD 2: Execution time < 2.0s
    assert elapsed < 2.0, f"Clustering took {elapsed:.3f}s, exceeding 2.0s DoD!"

    # Check each cluster structure
    all_assigned_ids = []
    for cl in clusters:
        assert cl["cluster_id"].startswith("cluster_")
        assert len(cl["name"]) > 0
        assert cl["color"].startswith("#")
        assert len(cl["node_ids"]) > 0
        assert "centroid" in cl
        assert "bounding_box" in cl
        bbox = cl["bounding_box"]
        assert bbox["width"] > 0
        assert bbox["height"] > 0
        all_assigned_ids.extend(cl["node_ids"])

    # All 12 nodes must be accounted for
    assert set(all_assigned_ids) == {n["id"] for n in SAMPLE_NODES_12}


def test_auto_cluster_spatial_repositioning():
    """Verifies that nodes are spatially repositioned and assigned cluster metadata."""
    result = auto_cluster_engine.cluster_nodes(SAMPLE_NODES_12, auto_layout=True)
    repositioned = result["repositioned_nodes"]
    assert len(repositioned) == 12

    for node in repositioned:
        assert "position" in node
        assert "x" in node["position"]
        assert "y" in node["position"]
        assert "clusterId" in node["data"]
        assert "clusterName" in node["data"]
        assert "clusterColor" in node["data"]


def test_cluster_names_synthesis_en_and_uk():
    """Verifies semantic theme naming in both English and Ukrainian."""
    arch_nodes = SAMPLE_NODES_12[:3]
    ui_nodes = SAMPLE_NODES_12[3:6]

    name_en = cluster_name_synthesizer.synthesize_cluster_name(arch_nodes, language="en")
    assert any(term in name_en.lower() for term in ["architecture", "infrastructure", "backend", "db", "cluster"])

    name_ui = cluster_name_synthesizer.synthesize_cluster_name(ui_nodes, language="en")
    assert any(term in name_ui.lower() for term in ["frontend", "canvas", "ui", "design", "cluster"])

    # Ukrainian test nodes
    uk_nodes = [
        {"title": "База даних Postgres", "content": "Таблиці для пам'яті агентів", "type": "mindmap_task"},
        {"title": "Архітектура сервера", "content": "Бекенд двигун та сервіси", "type": "mindmap_idea"},
    ]
    name_uk = cluster_name_synthesizer.synthesize_cluster_name(uk_nodes, language="uk")
    assert any(term in name_uk.lower() for term in ["архітектура", "інфраструктура", "бекенд", "кластер"])


def test_swarm_coordinator_auto_cluster_integration():
    """Verifies integration with GerychSwarmCoordinator."""
    result = swarm_coordinator.auto_cluster_mindmap(SAMPLE_NODES_12)
    assert result["status"] == "success"
    assert 3 <= len(result["clusters"]) <= 5
    assert result["total_nodes"] == 12


def test_auto_cluster_edge_cases():
    """Tests empty list, single node, and 2 nodes."""
    empty_res = auto_cluster_engine.cluster_nodes([])
    assert empty_res["status"] == "empty"
    assert empty_res["clusters"] == []
    assert empty_res["total_nodes"] == 0

    single_node = [SAMPLE_NODES_12[0]]
    single_res = auto_cluster_engine.cluster_nodes(single_node)
    assert single_res["status"] == "success"
    assert len(single_res["clusters"]) == 1
    assert single_res["total_nodes"] == 1

    two_nodes = SAMPLE_NODES_12[:2]
    two_res = auto_cluster_engine.cluster_nodes(two_nodes)
    assert two_res["status"] == "success"
    assert len(two_res["clusters"]) == 1
