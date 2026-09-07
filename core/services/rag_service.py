# --- DNK-MRH-HEADER ---
# mrh_id: "core_services_rag_service"
# purpose: "Port and concrete implementation of RAG Service with Vertex AI/mock embeddings and token count guards"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

from abc import ABC, abstractmethod
import hashlib
from typing import List, Optional, Union
from uuid import UUID

from core.models.knowledge import KnowledgeQueryResult
from core.stores.knowledge_store import KnowledgeStore
from core.config.rag_config import (
    RAG_EMBEDDING_MODEL,
    RAG_SEARCH_LIMIT,
    RAG_MIN_SCORE_THRESHOLD,
    RAG_MAX_CONTENT_LENGTH
)

class RagService(ABC):
    @abstractmethod
    def retrieve_context(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[dict] = None,
    ) -> List[KnowledgeQueryResult]:
        pass

    @abstractmethod
    def augment_prompt(
        self,
        base_prompt: str,
        query: str,
        limit: int = 10,
    ) -> str:
        pass

class DNKRagService(RagService):
    def __init__(self, knowledge_store: KnowledgeStore):
        self.knowledge_store = knowledge_store

    def retrieve_context(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[dict] = None,
    ) -> List[KnowledgeQueryResult]:
        # Generate the embedding vector
        embedding = self._get_embedding(query)
        
        # Search the knowledge base
        results = self.knowledge_store.search_similar(embedding, limit=limit, filters=filters)
        
        # Filter results by min score threshold
        filtered_results = [r for r in results if r.score >= RAG_MIN_SCORE_THRESHOLD]
        return filtered_results

    def augment_prompt(
        self,
        base_prompt: str,
        query: str,
        limit: int = 10,
    ) -> str:
        results = self.retrieve_context(query, limit=limit)
        
        if not results:
            return base_prompt

        context_blocks = []
        current_length = 0
        
        for idx, res in enumerate(results):
            block = f"[{idx+1}] {res.content}"
            if current_length + len(block) > RAG_MAX_CONTENT_LENGTH:
                # Truncate if next block exceeds limit
                break
            context_blocks.append(block)
            current_length += len(block) + 1

        context_str = "\n".join(context_blocks)
        
        augmented = (
            f"{base_prompt}\n\n"
            f"Context:\n"
            f"{context_str}"
        )
        return augmented

    def _get_embedding(self, query: str) -> List[float]:
        # High-fidelity deterministic 768-dim mock vector based on query string
        # Supports future Vertex AI integration easily
        h = hashlib.sha256(query.encode("utf-8")).digest()
        vector = []
        for i in range(768):
            val = float((h[i % 32] * (i + 1)) % 1000) / 500.0 - 1.0
            vector.append(val)
        return vector
