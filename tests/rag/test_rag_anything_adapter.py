# --- DNK-MRH-HEADER ---
# mrh_id: "tests/rag/test_rag_anything_adapter.py"
# purpose: "Unit and integration tests for DNKRAGAnythingAdapter and Multimodal RAG API"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (gerych_auditor & Gerych Prime)"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from core.adapters.dnk_rag_anything_adapter import (
    DNKRAGAnythingAdapter,
    RAGConfig,
)
from core.rag.processors import (
    ModalityType,
    MultimodalElement,
    DocumentDecomposer,
    DNKTableProcessor,
    DNKEquationProcessor,
    DNKImageProcessor,
)


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def rag_adapter():
    return DNKRAGAnythingAdapter(config=RAGConfig(spendguard_budget_usd=1.0))


def test_individual_modality_processors():
    # Table Processor
    table_proc = DNKTableProcessor()
    sample_table = "| Col1 | Col2 |\n| --- | --- |\n| Val1 | Val2 |"
    table_el = MultimodalElement(type=ModalityType.TABLE, content=sample_table)
    processed_table = table_proc.process(table_el)
    assert processed_table.metadata["is_processed"] is True
    assert processed_table.metadata["row_count"] == 1
    assert processed_table.metadata["headers"] == ["Col1", "Col2"]

    # Equation Processor
    eq_proc = DNKEquationProcessor()
    sample_eq = "$$E = mc^2$$"
    eq_el = MultimodalElement(type=ModalityType.EQUATION, content=sample_eq)
    processed_eq = eq_proc.process(eq_el)
    assert processed_eq.metadata["is_processed"] is True
    assert "clean_latex" in processed_eq.metadata
    assert "E = mc^2" in processed_eq.metadata["clean_latex"]

    # Image Processor
    img_proc = DNKImageProcessor()
    sample_img = "assets/diagram.png"
    img_el = MultimodalElement(type=ModalityType.IMAGE, content=sample_img, caption="System Architecture")
    processed_img = img_proc.process(img_el)
    assert processed_img.metadata["is_processed"] is True
    assert processed_img.caption == "System Architecture"
    assert processed_img.bounding_box is not None


def test_document_decomposer():
    decomposer = DocumentDecomposer()
    markdown_doc = """# Introduction to Quantum Circuits

Here is the fundamental state vector formulation:
$$|\\psi\\rangle = \\alpha |0\\rangle + \\beta |1\\rangle$$

Refer to the gate matrix table below:
| Gate | Matrix |
| --- | --- |
| Pauli-X | [[0, 1], [1, 0]] |

![Quantum Architecture](assets/circuit_diagram.png)
"""
    elements = decomposer.decompose_markdown(markdown_doc, source_doc="quantum.md")
    assert len(elements) >= 4

    types = {el.type for el in elements}
    assert ModalityType.TEXT in types
    assert ModalityType.EQUATION in types
    assert ModalityType.TABLE in types
    assert ModalityType.IMAGE in types


def test_rag_adapter_ingest_and_query(rag_adapter):
    sample_text = """# Architecture Overview
DNK OS utilizes hexagonal architecture for decoupling external frameworks.
The unified kernel connects swarm agents via event-driven pub-sub buses.
"""
    doc_id = rag_adapter.ingest_text(sample_text, title="arch_doc")
    assert doc_id.startswith("snippet_")

    # Query with relevant terms
    res = rag_adapter.query("hexagonal architecture")
    assert res.confidence_score > 0.0
    assert len(res.referenced_nodes) > 0
    assert "hexagonal architecture" in res.answer.lower()
    assert res.execution_time_ms >= 0.0

    # Query with non-matching terms
    res_empty = rag_adapter.query("xyznonexistentterm123")
    assert res_empty.confidence_score == 0.0


def test_rag_adapter_multimodal_query(rag_adapter):
    sample_text = "# Visual Ingestion\nProcessing visual layouts and canvas state."
    rag_adapter.ingest_text(sample_text, title="canvas_notes")

    image_element = MultimodalElement(
        type=ModalityType.IMAGE,
        content="https://cdn.dnk.ai/diagrams/canvas_nodes.png",
        caption="Canvas Flow Diagram"
    )

    res = rag_adapter.query_multimodal(
        prompt="Explain canvas flow",
        elements=[image_element],
        mode="hybrid"
    )
    assert "multimodal_vlm" in res.mode
    assert len(res.visual_evidence_urls) > 0
    assert "Canvas Flow Diagram" in res.answer or "Explain canvas flow" in res.answer


def test_rag_adapter_path_traversal_guard(rag_adapter):
    with pytest.raises(ValueError, match="Path traversal detected"):
        rag_adapter.ingest_document("../../../etc/passwd")


def test_rag_adapter_graph_topology(rag_adapter):
    sample_text = """# Knowledge Flow
Text section leading to mathematical proof.
$$f(x) = \\int_{-\\infty}^\\infty g(t) e^{-i\\omega t} dt$$
"""
    doc_id = rag_adapter.ingest_text(sample_text, title="fourier_notes")
    graph = rag_adapter.get_document_graph(doc_id)

    assert graph["doc_id"] == doc_id
    assert graph["total_nodes"] >= 2
    assert graph["total_edges"] >= 1
    assert any(e["relation"] == "illustrates_or_expands" for e in graph["edges"])


def test_api_endpoints(test_client):
    # Test Ingest Text
    ingest_payload = {
        "text": "# DNK Swarm Mesh\nAgents coordinate via asynchronous event loops.\n$$N = k \\cdot 2^m$$",
        "title": "swarm_mesh_spec",
        "metadata": {"author": "Gerych Prime"}
    }
    resp = test_client.post("/api/v1/rag/ingest-text", json=ingest_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    doc_id = data["doc_id"]

    # Test Query
    query_payload = {"query": "event loops", "mode": "hybrid"}
    resp_query = test_client.post("/api/v1/rag/query", json=query_payload)
    assert resp_query.status_code == 200
    res_data = resp_query.json()
    assert "event loops" in res_data["answer"].lower()
    assert res_data["confidence_score"] > 0.0

    # Test Multimodal Query
    mm_payload = {
        "query": "Synthesize swarm equations",
        "elements": [
            {
                "type": "equation",
                "content": "$$\\Delta t < \\frac{\\epsilon}{\\lambda}$$",
                "caption": "Convergence Bound"
            }
        ],
        "mode": "hybrid"
    }
    resp_mm = test_client.post("/api/v1/rag/query-multimodal", json=mm_payload)
    assert resp_mm.status_code == 200
    assert "multimodal_vlm" in resp_mm.json()["mode"]

    # Test Graph Topology
    resp_graph = test_client.get(f"/api/v1/rag/graph/{doc_id}")
    assert resp_graph.status_code == 200
    graph_data = resp_graph.json()
    assert graph_data["total_nodes"] >= 2
    assert graph_data["total_edges"] >= 1
