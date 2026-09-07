# --- DNK-MRH-HEADER ---
# mrh_id: "tests/rag/test_knowledge_graph_scones.py"
# purpose: "Unit & Integration test suite for Dual-Level Knowledge Graph and SCONES Memory Sync"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import pytest
from core.rag.processors import ModalityType, MultimodalElement
from core.rag.knowledge_graph import (
    GraphNodeType,
    GraphNode,
    GraphEdge,
    DualLevelKnowledgeGraph,
)
from core.adapters.dnk_rag_anything_adapter import DNKRAGAnythingAdapter, RAGConfig
from core.scones_memory import SCONESMemoryEngine


class MockSCONESMemoryEngine:
    def __init__(self):
        self.memories = []

    def add_memory(self, topic: str, content: str, importance: float = 0.5, workspace_id: str = "ws-alpha-001", metadata=None, tags=None, **kwargs):
        mem_id = f"mock_mem_{len(self.memories) + 1}"
        effective_tags = tags or (metadata.get("tags") if metadata else []) or []
        self.memories.append({
            "id": mem_id,
            "topic": topic,
            "content": content,
            "importance": importance,
            "workspace_id": workspace_id,
            "metadata": metadata or {},
            "tags": effective_tags,
        })
        return mem_id


@pytest.fixture
def sample_elements():
    return [
        MultimodalElement(
            id="txt_001",
            type=ModalityType.TEXT,
            content="Transformer attention mechanism computed with Q, K, V matrices and softmax scaling.",
            caption="Overview of Attention",
            metadata={"source_doc": "attention_paper.pdf", "heading": "Attention Mechanism"}
        ),
        MultimodalElement(
            id="eq_001",
            type=ModalityType.EQUATION,
            content=r"\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V",
            caption="Scaled Dot-Product Attention Equation",
            metadata={"source_doc": "attention_paper.pdf", "heading": "Attention Formula"}
        ),
        MultimodalElement(
            id="tbl_001",
            type=ModalityType.TABLE,
            content="| Model | BLEU | FLOPs |\n|---|---|---|\n| Transformer-Base | 27.3 | 3.3e18 |\n| Transformer-Big | 28.4 | 2.3e19 |",
            caption="WMT 2014 English-to-German Results Table",
            metadata={"source_doc": "attention_paper.pdf", "heading": "Empirical Benchmark Results"}
        ),
        MultimodalElement(
            id="img_001",
            type=ModalityType.IMAGE,
            content="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            caption="Architecture Diagram of Multi-Head Attention",
            metadata={"source_doc": "attention_paper.pdf", "image_url": "assets/arch.png"}
        )
    ]


def test_dual_level_graph_ingestion(sample_elements):
    graph = DualLevelKnowledgeGraph(workspace_id="ws-alpha-001")
    stats = graph.ingest_multimodal_elements(
        elements=sample_elements,
        doc_id="doc_attention_001",
        title="Attention Is All You Need",
        metadata={"domain": "Deep Learning"}
    )

    assert stats["nodes_created"] > 0
    assert stats["edges_created"] > 0
    assert stats["total_nodes"] >= 4
    assert stats["total_edges"] >= 3

    # Verify high-level theme nodes and low-level entity nodes exist
    nodes = list(graph.nodes.values())
    theme_nodes = [n for n in nodes if n.node_type == GraphNodeType.THEME]
    entity_nodes = [n for n in nodes if n.node_type == GraphNodeType.ENTITY]
    artifact_nodes = [n for n in nodes if n.node_type == GraphNodeType.ARTIFACT]

    assert len(theme_nodes) >= 1
    assert len(artifact_nodes) == 3
    assert len(entity_nodes) >= 1

    # Verify cross-level edge: belongs_to_theme
    theme_edges = [e for e in graph.edges if e.relation == "belongs_to_theme"]
    assert len(theme_edges) >= 1


def test_dual_level_query_modes(sample_elements):
    graph = DualLevelKnowledgeGraph(workspace_id="ws-alpha-001")
    graph.ingest_multimodal_elements(
        elements=sample_elements,
        doc_id="doc_attention_001",
        title="Attention Is All You Need"
    )

    # 1. Global query - should prioritize high-level themes
    res_global = graph.query_dual_level("Attention Mechanism Overview", mode="global", top_k=3)
    assert res_global["mode"] == "global"
    assert len(res_global["themes"]) >= 1

    # 2. Local query - should prioritize specific entities/equations/tables
    res_local = graph.query_dual_level("Scaled Dot-Product Attention Equation", mode="local", top_k=3)
    assert res_local["mode"] == "local"
    assert len(res_local["entities"]) >= 1

    # 3. Hybrid query - combines themes and entities
    res_hybrid = graph.query_dual_level("Transformer BLEU score results", mode="hybrid", top_k=5)
    assert res_hybrid["mode"] == "hybrid"
    assert "combined_context" in res_hybrid
    assert len(res_hybrid["combined_context"]) > 0


def test_scones_memory_synchronization(sample_elements):
    graph = DualLevelKnowledgeGraph(workspace_id="ws-alpha-001")
    graph.ingest_multimodal_elements(
        elements=sample_elements,
        doc_id="doc_attention_001",
        title="Attention Is All You Need"
    )

    mock_scones = MockSCONESMemoryEngine()
    sync_res = graph.sync_to_scones(mock_scones)

    assert sync_res["status"] == "success"
    assert sync_res["synced_memories_count"] > 0
    assert len(mock_scones.memories) == sync_res["synced_memories_count"]

    # Verify memory structure
    first_mem = mock_scones.memories[0]
    assert "topic" in first_mem
    assert "content" in first_mem
    assert first_mem["workspace_id"] == "ws-alpha-001"
    assert "rag_knowledge_graph" in first_mem["tags"]


def test_canvas_graph_export(sample_elements):
    graph = DualLevelKnowledgeGraph(workspace_id="ws-alpha-001")
    graph.ingest_multimodal_elements(
        elements=sample_elements,
        doc_id="doc_attention_001",
        title="Attention Is All You Need"
    )

    canvas_graph = graph.to_canvas_graph()
    assert "nodes" in canvas_graph
    assert "edges" in canvas_graph
    assert canvas_graph["metadata"]["total_nodes"] == len(canvas_graph["nodes"])
    assert canvas_graph["metadata"]["total_edges"] == len(canvas_graph["edges"])

    # Verify Canvas node shape
    for node in canvas_graph["nodes"]:
        assert "id" in node
        assert "type" in node
        assert "data" in node
        assert "position" in node
        assert "x" in node["position"]
        assert "y" in node["position"]

    # Verify Canvas edge shape
    for edge in canvas_graph["edges"]:
        assert "id" in edge
        assert "source" in edge
        assert "target" in edge
        assert "data" in edge


def test_adapter_dual_level_and_scones_integration(tmp_path):
    storage_dir = str(tmp_path / "rag_storage")
    cache_dir = str(tmp_path / "extracted_assets")
    adapter = DNKRAGAnythingAdapter(RAGConfig(storage_dir=storage_dir, cache_dir=cache_dir))

    # Ingest markdown text
    md_content = r"""# DeepSeek-R1 Architecture
The model uses Multi-Head Latent Attention (MLA) and Mixture of Experts (MoE).

$$MLA(X) = W_O (Softmax(Q K^T / \sqrt{d}) V)$$

| Model | AIME 2024 | MATH 500 |
|---|---|---|
| DeepSeek-R1 | 79.8% | 97.3% |
"""
    doc_id = adapter.ingest_text(md_content, title="DeepSeek-R1 Tech Report")
    assert doc_id.startswith("snippet_")

    # Ingest canvas data
    canvas_mock = {
        "nodes": [
            {"id": "c1", "type": "doc", "data": {"text": "Reasoning Core and RL Harness"}},
            {"id": "c2", "type": "image", "data": {"src": "https://example.com/fig1.png", "title": "RL Pipeline"}}
        ],
        "edges": [
            {"source": "c1", "target": "c2", "label": "illustrates"}
        ]
    }
    canvas_id = adapter.ingest_canvas(canvas_mock, canvas_id="reasoning_canvas")
    assert canvas_id.startswith("canvas_")

    # Query dual-level
    hybrid_res = adapter.query_dual_level("Multi-Head Latent Attention equation", mode="hybrid")
    assert hybrid_res["mode"] == "hybrid"
    assert len(hybrid_res["entities"]) >= 1

    # Export Canvas Graph
    full_canvas_graph = adapter.export_canvas_graph()
    assert len(full_canvas_graph["nodes"]) >= 4
    assert len(full_canvas_graph["edges"]) >= 3

    # Sync to SCONES
    mock_scones = MockSCONESMemoryEngine()
    sync_report = adapter.sync_scones(mock_scones)
    assert sync_report["status"] == "success"
    assert sync_report["synced_memories_count"] > 0
