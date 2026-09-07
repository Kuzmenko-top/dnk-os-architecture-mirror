# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_pgvector_scones.py"
# purpose: "Comprehensive unit and resilience tests for SCONES pgvector memory engine, dual-write fallback, and error distillation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import time
import pytest
from core.scones_memory import SCONESMemoryEngine
from core.memory.pgvector_store import (
    PgVectorStore,
    generate_embedding,
    cosine_similarity,
    VECTOR_DIMENSION,
    HNSW_M,
    HNSW_EF_CONSTRUCTION,
    DEFAULT_QUERY_TIMEOUT_MS
)

TEST_STORAGE_PATH = "tests/fixtures/scones_pgvector_test_storage.json"


@pytest.fixture
def clean_scones_engine():
    # Setup
    for p in [TEST_STORAGE_PATH, TEST_STORAGE_PATH.replace(".json", "_error_solutions.json")]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass

    engine = SCONESMemoryEngine(storage_path=TEST_STORAGE_PATH, enable_pgvector=True)
    yield engine

    # Teardown
    for p in [TEST_STORAGE_PATH, TEST_STORAGE_PATH.replace(".json", "_error_solutions.json")]:
        if os.path.exists(p):
            try:
                os.remove(p)
            except Exception:
                pass


def test_embedding_generation_and_cosine_similarity():
    """Verify deterministic embedding generation, dimension=768, and cosine similarity metric."""
    vec1 = generate_embedding("Shopify Liquid AST asset rewriting pipeline")
    vec2 = generate_embedding("Shopify Liquid AST asset rewriting pipeline")
    vec3 = generate_embedding("PostgreSQL cross-region replication lag")

    assert len(vec1) == VECTOR_DIMENSION
    assert len(vec1) == 768

    # Exact match similarity must be 1.0
    sim_exact = cosine_similarity(vec1, vec2)
    assert pytest.approx(sim_exact, 0.001) == 1.0

    # Cross-domain text should have lower similarity
    sim_diff = cosine_similarity(vec1, vec3)
    assert sim_diff < sim_exact


def test_pgvector_store_invariants():
    """Verify default invariants for HNSW index and timeout parameters."""
    store = PgVectorStore(host="invalid-test-host", port=59999, connect_timeout_s=1)
    assert store.vector_dim == 768
    assert store.query_timeout_ms == DEFAULT_QUERY_TIMEOUT_MS
    assert store.query_timeout_ms == 500
    assert HNSW_M == 16
    assert HNSW_EF_CONSTRUCTION == 64
    assert store.is_healthy() is False


def test_scones_dual_write_and_local_persistence(clean_scones_engine):
    """Verify dual-write to local JSON storage with metadata and tenant isolation."""
    engine = clean_scones_engine

    entry = engine.add_memory(
        topic="scaling",
        content="Cross-region replication latency p95 < 200ms achieved via Cloudflare Edge Worker",
        importance=1.9,
        metadata={"tenant_id": "tenant-alpha-001", "workspace_id": "ws-alpha-001"}
    )

    assert entry["id"].startswith("SCONES-MEM-")
    assert len(entry["embedding"]) == 768

    # Verify retrieval with metadata filters
    mems_tenant = engine.get_memories(tenant_id="tenant-alpha-001")
    assert len(mems_tenant) == 1
    assert mems_tenant[0]["content"] == entry["content"]

    mems_other_tenant = engine.get_memories(tenant_id="tenant-other")
    assert len(mems_other_tenant) == 0


def test_scones_semantic_search(clean_scones_engine):
    """Verify semantic search retrieves relevant memories by cosine similarity."""
    engine = clean_scones_engine

    engine.add_memory(
        topic="shopify-cdn",
        content="Shopify CDN asset sync with SRI SHA-384 integrity verification.",
        importance=1.5
    )
    engine.add_memory(
        topic="media-engine",
        content="Video frame rendering using Remotion and FrameCN canvas pipeline.",
        importance=1.2
    )

    results = engine.search_semantic("Shopify integrity hash sync", limit=2, min_similarity=0.2)
    assert len(results) > 0
    top_match = results[0]
    assert "Shopify" in top_match["content"]
    assert top_match["similarity"] > 0.3


def test_scones_error_solution_distillation(clean_scones_engine):
    """Verify distillation of error signatures and solutions for instant self-healing."""
    engine = clean_scones_engine

    error_text = "AssertionError: IntegrityMap SRI checksum missing for bundle.js"
    solution_text = "Inject integrity attribute with sha384 base64 digest in LiquidASTAssetRewriter."

    recorded = engine.record_error_solution(
        error_text=error_text,
        solution_text=solution_text,
        root_cause="Unrewritten script tag in product.liquid",
        metadata={"service": "liquid_ast_asset_rewriter"}
    )

    assert recorded["id"].startswith("SCONES-ERR-")
    assert recorded["success_rate"] == 1.0

    # Search for matching error
    matches = engine.search_error_solution("SRI checksum missing for bundle.js", limit=1, min_similarity=0.4)
    assert len(matches) == 1
    assert matches[0]["solution_text"] == solution_text
    assert matches[0]["root_cause"] == "Unrewritten script tag in product.liquid"


def test_scones_log_compaction_and_model_routing(clean_scones_engine):
    """Verify log compaction and self-healing proxy fallback."""
    engine = clean_scones_engine

    # Log compaction
    bloated = "\n".join([f"Log trace line {i}" for i in range(100)])
    compact = engine.compact_log_context(bloated, max_lines=10)
    assert "TRUNCATED" in compact

    # Model routing
    healthy = engine.route_model("gemini-3.7-flash")
    assert healthy["status"] == "ok"

    fallback = engine.route_model("gemini-3.7-flash", error_code=500)
    assert fallback["status"] == "healed"
    assert "mistralai/codestral-22b-instruct" in fallback["active_model"]


def test_semantic_search_timeout(clean_scones_engine):
    """Verify semantic search query completes within 500ms timeout constraint."""
    engine = clean_scones_engine
    start = time.time()
    results = engine.search_semantic("AssertionError in Shopify API", limit=5)
    elapsed = time.time() - start
    assert elapsed < 0.5, f"Query took {elapsed}s, expected < 500ms"
    assert isinstance(results, list)

