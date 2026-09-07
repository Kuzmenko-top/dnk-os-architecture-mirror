# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/postgres_hybrid_search_engine.py"
# purpose: "Unified PostgreSQL Hybrid Search Engine coordinating Dense pgvector, Sparse tsvector, Reciprocal Rank Fusion and Cross-Encoder reranking"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-VECTOR-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import time
import logging
from typing import List, Dict, Any, Optional
from apps.api.db.vector_store import VectorStore
from apps.api.services.postgres_dense_vector_search import PostgresDenseVectorSearch
from apps.api.services.postgres_sparse_vector_search import PostgresSparseVectorSearch
from apps.api.services.reciprocal_rank_fusion import ReciprocalRankFusion
from apps.api.services.cross_encoder_reranker import CrossEncoderReranker

logger = logging.getLogger("PostgresHybridSearchEngine")


class PostgresHybridSearchEngine:
    """
    Main Orchestrator for PostgreSQL-native Hybrid Search.
    Executes parallel Dense + Sparse streams, applies RRF Fusion, and optionally performs Cross-Encoder Reranking.
    """

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        rrf_engine: Optional[ReciprocalRankFusion] = None,
        reranker: Optional[CrossEncoderReranker] = None,
    ):
        self.vector_store = vector_store or VectorStore()
        self.dense_search = PostgresDenseVectorSearch(self.vector_store)
        self.sparse_search = PostgresSparseVectorSearch(self.vector_store)
        self.rrf_engine = rrf_engine or ReciprocalRankFusion(default_k=60)
        self.reranker = reranker or CrossEncoderReranker()

    def search(
        self,
        query_text: str,
        query_dense_vector: Optional[List[float]],
        tenant_id: str,
        workspace_id: str,
        top_k: int = 10,
        rrf_k: int = 60,
        dense_weight: float = 1.0,
        sparse_weight: float = 1.0,
        rerank: bool = False,
        rerank_top_k: int = 5,
        memory_type: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute full-pipeline hybrid search with latency breakdown and provenance tracking.
        """
        start_time = time.perf_counter()

        # Step 1: Retrieve Dense candidates (fetch 2x top_k for high recall prior to fusion)
        dense_start = time.perf_counter()
        dense_results: List[Dict[str, Any]] = []
        if query_dense_vector:
            dense_results = self.dense_search.search(
                query_vector=query_dense_vector,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                top_k=top_k * 2,
                memory_type=memory_type,
                filter_metadata=filter_metadata,
            )
        dense_latency_ms = round((time.perf_counter() - dense_start) * 1000, 2)

        # Step 2: Retrieve Sparse candidates (fetch 2x top_k)
        sparse_start = time.perf_counter()
        sparse_results: List[Dict[str, Any]] = []
        if query_text:
            sparse_results = self.sparse_search.search(
                query_text=query_text,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                top_k=top_k * 2,
                memory_type=memory_type,
                filter_metadata=filter_metadata,
            )
        sparse_latency_ms = round((time.perf_counter() - sparse_start) * 1000, 2)

        # Step 3: Reciprocal Rank Fusion
        fusion_start = time.perf_counter()
        fused_results = self.rrf_engine.fuse(
            dense_results=dense_results,
            sparse_results=sparse_results,
            k=rrf_k,
            dense_weight=dense_weight,
            sparse_weight=sparse_weight,
            top_k=top_k if not rerank else max(top_k, rerank_top_k * 2),
        )
        fusion_latency_ms = round((time.perf_counter() - fusion_start) * 1000, 2)

        # Step 4: Optional Cross-Encoder Reranking
        final_results = fused_results
        rerank_latency_ms = 0.0
        if rerank and fused_results:
            rerank_start = time.perf_counter()
            final_results = self.reranker.rerank(
                query=query_text,
                documents=fused_results,
                top_k=rerank_top_k,
            )
            rerank_latency_ms = round((time.perf_counter() - rerank_start) * 1000, 2)

        total_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return {
            "query": query_text,
            "tenant_id": tenant_id,
            "workspace_id": workspace_id,
            "results": final_results,
            "total_count": len(final_results),
            "reranked": rerank,
            "metrics": {
                "dense_latency_ms": dense_latency_ms,
                "sparse_latency_ms": sparse_latency_ms,
                "fusion_latency_ms": fusion_latency_ms,
                "rerank_latency_ms": rerank_latency_ms,
                "total_latency_ms": total_latency_ms,
                "dense_candidates_count": len(dense_results),
                "sparse_candidates_count": len(sparse_results),
            },
        }
