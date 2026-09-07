# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/postgres_dense_vector_search.py"
# purpose: "PostgreSQL Dense Vector Search service for pgvector 1536-dimensional embeddings with cosine/dot distance"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-VECTOR-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import logging
from typing import List, Dict, Any, Optional
from apps.api.db.vector_store import VectorStore

logger = logging.getLogger("PostgresDenseVectorSearch")


class PostgresDenseVectorSearch:
    """
    Dedicated Dense Vector Search service powered by pgvector (1536-dim embeddings).
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def search(
        self,
        query_vector: List[float],
        tenant_id: str,
        workspace_id: str,
        top_k: int = 10,
        memory_type: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute dense vector similarity search with tenant and workspace isolation.
        """
        if not query_vector:
            logger.warning("Empty dense query vector provided.")
            return []

        results = self.vector_store.query_dense(
            query_dense_vector=query_vector,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            top_k=top_k,
            memory_type=memory_type,
            filter_metadata=filter_metadata,
        )

        return results
