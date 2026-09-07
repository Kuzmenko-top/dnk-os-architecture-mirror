# --- DNK-MRH-HEADER ---
# mrh_id: "tests/rag/test_multimodal_pipeline.py"
# purpose: "Unit and integration tests for multimodal extraction pipeline, Docx, Canvas, PDF, and sidecar caching"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (gerych_prime & gerych_auditor)"
# --- END DNK-MRH-HEADER ---

import os
import json
import zlib
import zipfile
import tempfile
import pytest

from core.rag.processors import ModalityType, MultimodalElement
from core.rag.pipeline import (
    SidecarAssetCache,
    PurePythonPDFExtractor,
    DocxExtractor,
    CanvasVisualExtractor,
    MultimodalExtractionPipeline,
)
from core.adapters.dnk_rag_anything_adapter import DNKRAGAnythingAdapter, RAGConfig


def test_sidecar_asset_cache(tmp_path):
    cache = SidecarAssetCache(base_cache_dir=str(tmp_path))
    doc_dir = cache.get_document_cache_dir("sample_doc_key_123")
    assert os.path.isdir(doc_dir)

    elements = [
        MultimodalElement(type=ModalityType.TEXT, content="Intro paragraph"),
        MultimodalElement(
            type=ModalityType.IMAGE,
            content="path/to/img.png",
            caption="Arch Diagram",
            bounding_box={"x1": 0.1, "y1": 0.2, "x2": 0.8, "y2": 0.9},
        ),
    ]

    meta_path = cache.save_sidecar(doc_dir, "test.md", elements, metadata={"author": "DNK"})
    assert os.path.exists(meta_path)
    assert meta_path.endswith(".meta.json")

    loaded = cache.load_sidecar(doc_dir)
    assert loaded is not None
    assert loaded["source_path"] == "test.md"
    assert loaded["total_elements"] == 2
    assert loaded["modality_counts"]["text"] == 1
    assert loaded["modality_counts"]["image"] == 1
    assert loaded["metadata"]["author"] == "DNK"


def test_pure_python_pdf_extractor(tmp_path):
    pdf_path = tmp_path / "test_doc.pdf"
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Build a minimal valid PDF-like byte structure with a text stream
    text_content = b"BT\n/F1 12 Tf\n(HKUDS RAG-Anything assimilation in DNK OS) Tj\nET"
    compressed = zlib.compress(text_content)
    pdf_bytes = (
        b"%PDF-1.4\n1 0 obj\n<< /Length "
        + str(len(compressed)).encode("ascii")
        + b" /Filter /FlateDecode >>\nstream\n"
        + compressed
        + b"\nendstream\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    )
    pdf_path.write_bytes(pdf_bytes)

    extractor = PurePythonPDFExtractor()
    elements = extractor.extract(str(pdf_path), str(cache_dir))

    assert len(elements) >= 1
    assert elements[0].type == ModalityType.TEXT
    assert "HKUDS RAG-Anything" in elements[0].content


def test_docx_extractor(tmp_path):
    docx_path = tmp_path / "sample.docx"
    cache_dir = tmp_path / "cache_docx"
    cache_dir.mkdir()

    # Create synthetic docx zip package
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
      <w:body>
        <w:p>
          <w:r><w:t>Overview of Multimodal Architecture</w:t></w:r>
        </w:p>
        <w:p>
          <m:oMath>
            <m:r><w:t>E = mc^2</w:t></m:r>
          </m:oMath>
        </w:p>
        <w:tbl>
          <w:tr>
            <w:tc><w:p><w:r><w:t>Metric</w:t></w:r></w:p></w:tc>
            <w:tc><w:p><w:r><w:t>Score</w:t></w:r></w:p></w:tc>
          </w:tr>
          <w:tr>
            <w:tc><w:p><w:r><w:t>Latency</w:t></w:r></w:p></w:tc>
            <w:tc><w:p><w:r><w:t>12ms</w:t></w:r></w:p></w:tc>
          </w:tr>
        </w:tbl>
        <w:p>
          <w:r><w:t>Concluding analysis.</w:t></w:r>
        </w:p>
      </w:body>
    </w:document>"""

    with zipfile.ZipFile(docx_path, "w") as zf:
        zf.writestr("word/document.xml", document_xml)
        zf.writestr("word/media/image1.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDRmock_png_bytes")

    extractor = DocxExtractor()
    elements = extractor.extract(str(docx_path), str(cache_dir))

    types = [el.type for el in elements]
    assert ModalityType.IMAGE in types
    assert ModalityType.TEXT in types
    assert ModalityType.EQUATION in types
    assert ModalityType.TABLE in types

    # Verify cached image exists
    img_element = next(el for el in elements if el.type == ModalityType.IMAGE)
    assert os.path.exists(img_element.content)

    # Verify table formatting
    table_element = next(el for el in elements if el.type == ModalityType.TABLE)
    assert "| Metric | Score |" in table_element.content
    assert "| Latency | 12ms |" in table_element.content

    # Verify formula extraction
    equation_element = next(el for el in elements if el.type == ModalityType.EQUATION)
    assert "$$E = mc^2$$" in equation_element.content


def test_canvas_visual_extractor():
    extractor = CanvasVisualExtractor()
    sample_canvas = {
        "nodes": [
            {
                "id": "node-101",
                "type": "DocNode",
                "name": "System Architecture",
                "x": 100.0,
                "y": 200.0,
                "metadata": {"content": "Decentralized autonomous node tree"},
            },
            {
                "id": "node-102",
                "type": "ImageNode",
                "name": "Pipeline Diagram",
                "x": 350.0,
                "y": 200.0,
                "metadata": {"image_url": "https://assets.dnk-e.com/diag1.svg", "caption": "Execution DAG"},
            },
            {
                "id": "node-103",
                "type": "EquationNode",
                "name": "Loss Function",
                "x": 600.0,
                "y": 200.0,
                "metadata": {"latex": "\\mathcal{L}_{RAG} = \\alpha L_{text} + \\beta L_{visual}"},
            },
        ]
    }

    elements = extractor.extract_from_dict(sample_canvas, source_id="canvas-space-01")
    assert len(elements) == 3

    text_el = elements[0]
    assert text_el.type == ModalityType.TEXT
    assert text_el.bounding_box["x1"] == 100.0
    assert text_el.metadata["canvas_node_id"] == "node-101"

    img_el = elements[1]
    assert img_el.type == ModalityType.IMAGE
    assert img_el.content == "https://assets.dnk-e.com/diag1.svg"
    assert img_el.caption == "Execution DAG"

    eq_el = elements[2]
    assert eq_el.type == ModalityType.EQUATION
    assert "\\mathcal{L}_{RAG}" in eq_el.content


def test_multimodal_extraction_pipeline_orchestration(tmp_path):
    pipeline = MultimodalExtractionPipeline(cache_dir=str(tmp_path / "assets_cache"))

    # Test Markdown file extraction
    md_file = tmp_path / "report.md"
    md_file.write_text(
        "# RAG System\n\n![Visual Graph](https://dnk.ai/graph.png)\n\nSome text.\n\n$$S = \\sum x_i$$\n",
        encoding="utf-8",
    )

    elements, meta_path = pipeline.extract(str(md_file))
    assert os.path.exists(meta_path)
    types = [el.type for el in elements]
    assert ModalityType.TEXT in types
    assert ModalityType.IMAGE in types
    assert ModalityType.EQUATION in types


def test_adapter_canvas_ingestion(tmp_path):
    adapter = DNKRAGAnythingAdapter(RAGConfig(cache_dir=str(tmp_path / "adapter_cache")))
    canvas_data = {
        "nodes": [
            {
                "id": "canvas-n1",
                "type": "DocNode",
                "name": "Step 1",
                "metadata": {"content": "Extract features from multi-modal inputs."},
            },
            {
                "id": "canvas-n2",
                "type": "ImageNode",
                "name": "Feature Map",
                "metadata": {"image_url": "canvas://maps/feat.png", "caption": "Extracted feature map"},
            },
        ]
    }

    doc_id = adapter.ingest_canvas(canvas_data, canvas_id="workspace_alpha_canvas")
    assert doc_id.startswith("canvas_")

    graph = adapter.get_document_graph(doc_id)
    assert graph["doc_id"] == doc_id
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) >= 1

    # Verify edge relations
    assert graph["edges"][0]["relation"] == "precedes"
    illustrates_edge = next((e for e in graph["edges"] if e["relation"] == "illustrates_or_expands"), None)
    assert illustrates_edge is not None
    assert illustrates_edge["weight"] == 2.0
