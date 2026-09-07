# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_hybrid_search.py"
# purpose: "Verification test suite for PostgreSQL Hybrid Search Engine (pgvector + tsvector + SQL RRF)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HYBRID-SEARCH-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from typing import Dict, List, Any
from core.memory.pgvector_store import PgVectorStore, generate_embedding


class TestHybridSearch:
    @pytest.fixture
    def store(self):
        return PgVectorStore(auto_init_schema=False)

    def test_embedding_generation(self):
        emb = generate_embedding("Shopify API token error")
        assert len(emb) == 768
        assert isinstance(emb, list)

    def test_hybrid_search_empty_query(self, store):
        results = store.hybrid_search(query="")
        assert results == []

    def test_hybrid_search_unconnected_fallback(self, store):
        # Store is unconnected, should return empty list gracefully without throwing
        results = store.hybrid_search(
            query="AssertionError Shopify API",
            top_k=5
        )
        assert results == []

    @pytest.mark.asyncio
    async def test_hybrid_search_rrf_structure(self, store):
        # Verify function interface and parameters
        results = store.hybrid_search_error_solutions(
            query="AssertionError in Shopify API token",
            query_vector=generate_embedding("AssertionError in Shopify API token"),
            top_k=10,
            candidate_limit=20,
            rrf_k=60
        )
        assert isinstance(results, list)
