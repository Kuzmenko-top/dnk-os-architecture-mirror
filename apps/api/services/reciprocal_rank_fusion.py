# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/reciprocal_rank_fusion.py"
# purpose: "Reciprocal Rank Fusion (RRF) algorithm implementation for multi-retrieval channel score combination"
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

logger = logging.getLogger("ReciprocalRankFusion")


class ReciprocalRankFusion:
    """
    Reciprocal Rank Fusion (RRF) Engine.
    Combines ranked candidate lists from Dense and Sparse retrievers:
      RRF_Score(d) = sum_{m in models} (weight_m / (k + rank_m(d)))
    """

    def __init__(self, default_k: int = 60):
        self.default_k = default_k

    def fuse(
        self,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: Optional[int] = None,
        dense_weight: float = 1.0,
        sparse_weight: float = 1.0,
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Merge and rank dense and sparse retrieval results using weighted RRF.
        """
        k_val = k if k is not None and k > 0 else self.default_k
        fused_scores: Dict[str, float] = {}
        item_data: Dict[str, Dict[str, Any]] = {}
        dense_ranks: Dict[str, int] = {}
        sparse_ranks: Dict[str, int] = {}

        # 1. Process Dense Results (1-based rank index)
        for rank, item in enumerate(dense_results, start=1):
            doc_id = str(item["id"])
            if doc_id not in item_data:
                item_data[doc_id] = item.copy()
            dense_ranks[doc_id] = rank
            rrf_delta = dense_weight / (k_val + rank)
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + rrf_delta

        # 2. Process Sparse Results (1-based rank index)
        for rank, item in enumerate(sparse_results, start=1):
            doc_id = str(item["id"])
            if doc_id not in item_data:
                item_data[doc_id] = item.copy()
            sparse_ranks[doc_id] = rank
            rrf_delta = sparse_weight / (k_val + rank)
            fused_scores[doc_id] = fused_scores.get(doc_id, 0.0) + rrf_delta

        # 3. Sort merged candidates by RRF score descending
        sorted_doc_ids = sorted(
            fused_scores.keys(),
            key=lambda x: fused_scores[x],
            reverse=True,
        )

        # 4. Construct final output with provenance ranks
        fused_list: List[Dict[str, Any]] = []
        for doc_id in sorted_doc_ids[:top_k]:
            doc_info = item_data[doc_id].copy()
            doc_info["rrf_score"] = round(fused_scores[doc_id], 6)
            doc_info["dense_rank"] = dense_ranks.get(doc_id)
            doc_info["sparse_rank"] = sparse_ranks.get(doc_id)
            fused_list.append(doc_info)

        return fused_list
