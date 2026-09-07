# --- DNK-MRH-HEADER ---
# mrh_id: "tests/adapters/test_llamaindex_adapter.py"
# purpose: "Unit Test Suite for LlamaIndexAdapter"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""Unit tests for Adapters: LlamaIndexAdapter."""

import pytest
from adapters.llamaindex_adapter import LlamaIndexAdapter


class TestLlamaIndexAdapter:
    """Test suite for LlamaIndexAdapter."""

    def test_init_default(self) -> None:
        """Test initialization with default parameters."""
        adapter = LlamaIndexAdapter()
        assert adapter is not None
        assert adapter.vector_store_type == "memory"
        assert adapter.embedding_model == "local"

    def test_load_documents(self) -> None:
        """Test document loading."""
        adapter = LlamaIndexAdapter(vector_store_type="memory")
        docs = ["Document 1", "Document 2"]
        count = adapter.load_documents(documents=docs)
        assert count == 2

    def test_index_documents(self) -> None:
        """Test document indexing with chunking."""
        adapter = LlamaIndexAdapter(vector_store_type="memory")
        docs = ["Long document text..." * 100]
        count = adapter.index_documents(documents=docs, chunk_size=256, chunk_overlap=50)
        assert count > 0

    def test_query_similarity(self) -> None:
        """Test similarity search."""
        adapter = LlamaIndexAdapter(vector_store_type="memory")
        docs = ["Paris is the capital of France.", "Berlin is the capital of Germany."]
        adapter.load_documents(documents=docs)
        result = adapter.query(query="What is the capital of France?", top_k=1)
        assert "results" in result
        assert len(result["results"]) > 0

    def test_rag_query(self) -> None:
        """Test RAG query."""
        adapter = LlamaIndexAdapter(vector_store_type="memory", llm_model="gpt2")
        docs = ["Paris is the capital and largest city of France."]
        adapter.load_documents(documents=docs)
        result = adapter.rag_query(query="What is the capital of France?", top_k=1)
        assert "answer" in result
        assert "sources" in result
        assert len(result["sources"]) > 0

    def test_clear_index(self) -> None:
        """Test clearing vector store index."""
        adapter = LlamaIndexAdapter(vector_store_type="memory")
        docs = ["Doc A", "Doc B"]
        adapter.load_documents(documents=docs)
        adapter.clear_index()
        result = adapter.query(query="Doc A", top_k=5)
        assert len(result["results"]) == 0
