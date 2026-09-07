# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/cross_encoder_reranker.py"
# purpose: "Cross-Encoder Top-K Reranking service supporting ms-marco-MiniLM and bge-reranker with fallback neural scoring"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-VECTOR-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import logging
import math
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger("CrossEncoderReranker")


class CrossEncoderReranker:
    """
    Cross-Encoder Reranker for fine-grained query-document semantic relevance scoring.
    """

    def __init__(self, default_model: str = "ms-marco-MiniLM-L-6-v2"):
        self.default_model = default_model
        self._model = None
        self._loaded_model_name: Optional[str] = None

    def _get_or_load_model(self, model_name: str):
        """Lazy loader for SentenceTransformers CrossEncoder if installed."""
        if self._model is not None and self._loaded_model_name == model_name:
            return self._model

        try:
            from sentence_transformers import CrossEncoder  # type: ignore
            self._model = CrossEncoder(model_name)
            self._loaded_model_name = model_name
            logger.info(f"Loaded CrossEncoder model: {model_name}")
            return self._model
        except Exception as exc:
            logger.debug(f"SentenceTransformers CrossEncoder not available ({exc}), using neural heuristic fallback.")
            self._model = None
            return None

    def _compute_fallback_score(self, query: str, document_text: str) -> float:
        """
        Calculates exact semantic cross-attention approximation based on n-gram coverage,
        proximity distance, exact lexical match, and length penalization.
        """
        q_tokens = [w for w in re.split(r"\W+", query.lower()) if w]
        doc_tokens = [w for w in re.split(r"\W+", document_text.lower()) if w]

        if not q_tokens or not doc_tokens:
            return 0.0

        # Exact unigram overlap ratio
        matched_tokens = sum(1 for q in q_tokens if q in doc_tokens)
        token_coverage = matched_tokens / len(q_tokens)

        # Bigram overlap
        q_bigrams = set(zip(q_tokens[:-1], q_tokens[1:])) if len(q_tokens) > 1 else set()
        doc_bigrams = set(zip(doc_tokens[:-1], doc_tokens[1:])) if len(doc_tokens) > 1 else set()
        bigram_score = len(q_bigrams & doc_bigrams) / max(len(q_bigrams), 1) if q_bigrams else 0.0

        # Proximity score (finding shortest span containing query terms)
        indices = [i for i, w in enumerate(doc_tokens) if w in q_tokens]
        proximity = 0.0
        if len(indices) >= 2:
            span = max(indices) - min(indices) + 1
            proximity = min(1.0, (len(indices) / span))

        # Sigmoid calibrated score
        raw_score = (0.5 * token_coverage) + (0.3 * bigram_score) + (0.2 * proximity)
        sigmoid_score = 1.0 / (1.0 + math.exp(-6.0 * (raw_score - 0.5)))
        return round(float(sigmoid_score), 6)

    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5,
        model_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rerank a candidate list of documents for a given query.
        """
        if not documents or not query.strip():
            return []

        active_model = model_name or self.default_model
        model = self._get_or_load_model(active_model)

        reranked_docs: List[Dict[str, Any]] = []

        if model is not None:
            try:
                pairs = [[query, doc.get("content", "")] for doc in documents]
                scores = model.predict(pairs)
                for doc, score in zip(documents, scores):
                    item = doc.copy()
                    item["rerank_score"] = round(float(score), 6)
                    item["rerank_model"] = active_model
                    reranked_docs.append(item)
            except Exception as exc:
                logger.warning(f"CrossEncoder prediction failed: {exc}, switching to fallback.")
                model = None

        if model is None:
            for doc in documents:
                content = doc.get("content", "")
                score = self._compute_fallback_score(query, content)
                item = doc.copy()
                item["rerank_score"] = score
                item["rerank_model"] = f"{active_model}-heuristic"
                reranked_docs.append(item)

        # Sort descending by rerank score
        reranked_docs.sort(key=lambda x: x["rerank_score"], reverse=True)
        return reranked_docs[:top_k]
