# --- DNK-MRH-HEADER ---
# mrh_id: "tests/core/test_tool_semantic_index.py"
# purpose: "Unit tests for ToolSemanticIndex: semantic search, keyword fallback, and embedding cache."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from core.orchestrator.tool_semantic_index import ToolSemanticIndex
from core.orchestrator.tool_registry import TOOL_REGISTRY


def test_semantic_index_search():
    index = ToolSemanticIndex(TOOL_REGISTRY)
    results = index.search("Shopify Liquid validation")
    assert "dnk_shopify_validate_liquid" in results
    assert len(results) <= 5


def test_semantic_index_fallback():
    # Test without sentence-transformers (keyword search)
    index = ToolSemanticIndex(TOOL_REGISTRY)
    index.model = None  # Force fallback
    results = index.search("file read")
    assert "file.read" in results


def test_embedding_cache():
    # Verify model is cached
    index1 = ToolSemanticIndex(TOOL_REGISTRY)
    index2 = ToolSemanticIndex(TOOL_REGISTRY)
    assert index1.model is index2.model  # Same cached instance


def test_custom_registry():
    custom_registry = {
        "custom.ping": {
            "name": "custom.ping",
            "description": "Network latency ping checker",
            "parameters": {"type": "object"},
        }
    }
    index = ToolSemanticIndex(custom_registry)
    index.model = None
    results = index.search("latency ping")
    assert "custom.ping" in results
