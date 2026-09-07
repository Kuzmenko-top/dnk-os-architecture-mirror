# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_rag_adapter.py"
# purpose: "Hexagonal contract and interface unit tests for MultimodalRAGPort & DNKRAGAnythingAdapter"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (gerych_prime & gerych_auditor)"
# --- END DNK-MRH-HEADER ---

import pytest
import tempfile
import os

from core.adapters import (
    MultimodalRAGPort,
    DNKRAGAnythingAdapter,
    RAGConfig,
    RAGQueryResult,
)
from core.rag.processors import (
    ModalityType,
    MultimodalElement,
)


def test_rag_port_contract_conformance():
    """Verify that DNKRAGAnythingAdapter fulfills the MultimodalRAGPort ABC contract."""
    adapter = DNKRAGAnythingAdapter()
    assert isinstance(adapter, MultimodalRAGPort)
    assert hasattr(adapter, "ingest_document")
    assert hasattr(adapter, "query")
    assert hasattr(adapter, "query_multimodal")
    assert hasattr(adapter, "get_document_graph")


def test_adapter_text_ingest_and_retrieval():
    """Verify in-memory snippet ingestion and hybrid search retrieval."""
    adapter = DNKRAGAnythingAdapter(config=RAGConfig(hybrid_top_k=3))
    sample_text = """# SCONES Multimodal Architecture
SCONES provides episodic, semantic, and procedural long-term cognitive memory.
Multimodal elements such as circuit diagrams and LaTeX equations are linked via belongs_to edges.
"""
    doc_id = adapter.ingest_text(sample_text, title="scones_multimodal_spec")
    assert doc_id.startswith("snippet_")

    res = adapter.query("SCONES memory")
    assert isinstance(res, RAGQueryResult)
    assert res.confidence_score > 0.0
    assert "SCONES" in res.answer
    assert len(res.referenced_nodes) > 0


def test_adapter_file_ingest_and_graph_topology():
    """Verify physical markdown file ingestion and knowledge graph topology generation."""
    adapter = DNKRAGAnythingAdapter()

    sample_md = """# Transformer Attention
The scaled dot-product attention formulation:
$$\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V$$

| Symbol | Meaning |
| --- | --- |
| Q | Query vector |
| K | Key vector |

![Attention Map](assets/attention.png)
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(sample_md)
        temp_path = f.name

    try:
        doc_id = adapter.ingest_document(temp_path, metadata={"domain": "deep_learning"})
        assert doc_id.startswith("doc_")

        graph = adapter.get_document_graph(doc_id)
        assert graph["doc_id"] == doc_id
        assert graph["total_nodes"] >= 4
        assert graph["total_edges"] >= 3

        node_types = {n["type"] for n in graph["nodes"]}
        assert "text" in node_types
        assert "equation" in node_types
        assert "table" in node_types
        assert "image" in node_types

        # Check edge relations
        relations = {e["relation"] for e in graph["edges"]}
        assert "precedes" in relations or "illustrates_or_expands" in relations
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_adapter_multimodal_query_and_spendguard():
    """Verify direct VLM multimodal element injection and SpendGuard enforcement."""
    config = RAGConfig(spendguard_budget_usd=0.005)  # Very low cap to test guard
    adapter = DNKRAGAnythingAdapter(config=config)

    elements = [
        MultimodalElement(
            type=ModalityType.IMAGE,
            content="https://example.com/diagram1.png",
            caption="Overview Diagram"
        ),
        MultimodalElement(
            type=ModalityType.IMAGE,
            content="https://example.com/diagram2.png",
            caption="Flowchart"
        ),
    ]

    res = adapter.query_multimodal("Explain the architecture", elements=elements)
    assert res.mode == "hybrid_multimodal_vlm"
    assert "https://example.com/diagram1.png" in res.visual_evidence_urls

    # Exceed budget
    expensive_elements = [
        MultimodalElement(type=ModalityType.IMAGE, content=f"img_{i}.png")
        for i in range(10)
    ]
    with pytest.raises(RuntimeError, match="SpendGuard Error"):
        adapter.query_multimodal("High budget query", elements=expensive_elements)


def test_adapter_path_traversal_security():
    """Verify that path traversal attempts raise security errors."""
    adapter = DNKRAGAnythingAdapter()
    with pytest.raises(ValueError, match="Path traversal detected"):
        adapter.ingest_document("../../etc/passwd")
