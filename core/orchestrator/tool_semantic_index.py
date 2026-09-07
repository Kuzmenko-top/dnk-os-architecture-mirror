# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/tool_semantic_index.py"
# purpose: "Semantic vector search for tool retrieval to eliminate upfront schema tax."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Antigravity Mentor"
# --- END DNK-MRH-HEADER ---

import re
from typing import List, Dict, Any, Optional

try:
    import numpy as np
except ImportError:
    np = None

# Class-level model cache to guarantee shared model instance across indices
_EMBEDDING_MODEL_CACHE = None
_EMBEDDING_MODEL_LOADED = False


class ToolSemanticIndex:
    """
    Semantic search for tools using vector embeddings with instant keyword fallback.
    
    Before: Model sees 60+ full schemas upfront (17,500 tokens)
    After: Model sees 3 meta-tools (150 tokens) + semantic on-demand search
    """

    def __init__(self, tool_registry: Dict[str, Any]):
        self.tool_registry = tool_registry or {}
        self.tool_names = list(self.tool_registry.keys())
        self.tool_descriptions = []

        for name, spec in self.tool_registry.items():
            if hasattr(spec, "summary"):
                desc = spec.summary
            elif isinstance(spec, dict):
                desc = spec.get("description") or spec.get("summary") or ""
            else:
                desc = str(spec)
            self.tool_descriptions.append(f"{name}: {desc}")

        self.model = self._load_embedding_model()
        self.embeddings = self._build_embeddings()

    def _load_embedding_model(self):
        """
        Loads lightweight embedding model (cached globally).
        Model: sentence-transformers/all-MiniLM-L6-v2 (~80MB, fast).
        """
        global _EMBEDDING_MODEL_CACHE, _EMBEDDING_MODEL_LOADED
        if _EMBEDDING_MODEL_LOADED:
            return _EMBEDDING_MODEL_CACHE

        try:
            from sentence_transformers import SentenceTransformer
            _EMBEDDING_MODEL_CACHE = SentenceTransformer("all-MiniLM-L6-v2", cache_folder="cache/models")
            _EMBEDDING_MODEL_LOADED = True
            return _EMBEDDING_MODEL_CACHE
        except Exception:
            _EMBEDDING_MODEL_CACHE = None
            _EMBEDDING_MODEL_LOADED = True
            return None

    def _build_embeddings(self):
        """Builds embeddings for all tool descriptions."""
        if self.model is None or np is None or not self.tool_descriptions:
            if np is not None:
                return np.zeros((len(self.tool_descriptions), 384))
            return []
        try:
            return self.model.encode(self.tool_descriptions)
        except Exception:
            return []

    def search(self, query: str, top_k: int = 5) -> List[str]:
        """
        Semantic search for tools by query string.
        Falls back seamlessly to weighted keyword search if embeddings are not active.
        """
        if not self.tool_names:
            return []

        if self.model is None or np is None or len(self.embeddings) == 0:
            return self._keyword_search(query, top_k)

        try:
            query_embedding = self.model.encode([query])
            similarities = self._cosine_similarity(query_embedding, self.embeddings)
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            return [self.tool_names[i] for i in top_indices]
        except Exception:
            return self._keyword_search(query, top_k)

    def _keyword_search(self, query: str, top_k: int) -> List[str]:
        """
        Weighted token keyword search fallback.
        Ranks exact name matches, domain terms, and description overlaps.
        """
        query_clean = query.lower().strip()
        query_words = set(re.findall(r"\w+", query_clean))
        scores: List[tuple[int, float]] = []

        for i, name in enumerate(self.tool_names):
            desc = self.tool_descriptions[i].lower()
            name_lower = name.lower()
            name_words = set(re.findall(r"\w+", name_lower))
            desc_words = set(re.findall(r"\w+", desc))

            score = 0.0

            # Direct substring in tool name
            if query_clean in name_lower:
                score += 10.0

            # Word overlaps
            for w in query_words:
                if w in name_words:
                    score += 5.0
                elif w in name_lower:
                    score += 3.0
                elif w in desc_words:
                    score += 2.0
                elif w in desc:
                    score += 1.0

            # Additional domain matches
            if "shopify" in query_words and ("shopify" in name_lower or "liquid" in name_lower):
                score += 4.0
            if "liquid" in query_words and "liquid" in name_lower:
                score += 4.0
            if "video" in query_words and ("video" in name_lower or "remotion" in name_lower or "composition" in name_lower):
                score += 4.0
            if "file" in query_words and ("file" in name_lower or "read" in name_lower or "write" in name_lower):
                score += 2.0
            if "read" in query_words and ("read" in name_lower or "file.read" in name_lower or "read_file" in name_lower):
                score += 5.0

            scores.append((i, score))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        top_candidates = [self.tool_names[i] for i, s in scores[:top_k] if s > 0]
        if not top_candidates:
            top_candidates = self.tool_names[:top_k]
        return top_candidates

    def _cosine_similarity(self, a, b):
        """Computes cosine similarity between vector a and matrix b."""
        if np is None:
            return []
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b, axis=1)
        norm_b = np.where(norm_b == 0, 1e-9, norm_b)
        dot_product = np.dot(b, a.T).flatten()
        return dot_product / (norm_a * norm_b)
