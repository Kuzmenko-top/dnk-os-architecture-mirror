# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/postgres_sparse_vector_search.py"
# purpose: "PostgreSQL Sparse Lexical Search service using tsvector, tsquery, and BM25 ranking"
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

logger = logging.getLogger("PostgresSparseVectorSearch")


class PostgresSparseVectorSearch:
    """
    Dedicated Sparse Lexical Search service powered by PostgreSQL tsvector & ts_rank_cd / BM25.
    """

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def search(
        self,
        query_text: str,
        tenant_id: str,
        workspace_id: str,
        top_k: int = 10,
        memory_type: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute sparse lexical search with tenant and workspace isolation.
        """
        if not query_text or not query_text.strip():
            logger.warning("Empty query text provided for sparse search.")
            return []

        results = self.vector_store.query_sparse(
            query_text=query_text,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            top_k=top_k,
            memory_type=memory_type,
            filter_metadata=filter_metadata,
        )

        return results
