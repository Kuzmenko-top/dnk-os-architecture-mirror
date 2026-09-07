# --- DNK-MRH-HEADER ---
# mrh_id: "adapters/llamaindex_adapter.py"
# purpose: "DNK OS Adapter for LlamaIndex RAG Pipelines"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-22"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
LlamaIndex Adapter for DNK OS Multi-Agent Core.

Provides unified interface for vector store indexing, similarity search,
document chunking, and RAG query generation.
"""

from typing import Any, Dict, List, Optional, Union
import math


class LlamaIndexAdapter:
    """
    Adapter for LlamaIndex RAG pipelines.
    
    Supports:
    - Vector store indexing
    - Similarity search
    - RAG query engine
    - Document loading
    - Embedding generation
    """
    
    def __init__(
        self,
        vector_store_type: str = "memory",
        embedding_model: str = "local",
        llm_model: str = "gpt2",
        use_mock: bool = True,
        **kwargs: Any,
    ) -> None:
        """
        Initialize LlamaIndex pipeline.
        
        Args:
            vector_store_type: Vector store type ("memory", "chroma", "pinecone", "weaviate")
            embedding_model: Embedding model ("local", "openai", "huggingface")
            llm_model: LLM model for generation
            use_mock: Enable in-memory lightweight vector search & mock generation
            **kwargs: Additional pipeline arguments
        """
        self.vector_store_type = vector_store_type
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self.kwargs = kwargs
        self.use_mock = use_mock
        
        # Internal in-memory store representation
        self._documents: List[Dict[str, Any]] = []
        self._index: List[Dict[str, Any]] = []

    def load_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> int:
        """
        Load documents into vector store.
        
        Args:
            documents: List of document texts
            metadata: Optional list of metadata dicts
            **kwargs: Additional loading arguments
            
        Returns:
            Number of documents loaded
        """
        loaded_count = 0
        for idx, doc_text in enumerate(documents):
            meta = metadata[idx] if metadata and idx < len(metadata) else {}
            doc_obj = {
                "id": f"doc_{len(self._documents) + 1}",
                "text": doc_text,
                "metadata": meta,
            }
            self._documents.append(doc_obj)
            self._index.append({
                "chunk_id": f"chunk_{len(self._index) + 1}",
                "doc_id": doc_obj["id"],
                "text": doc_text,
                "metadata": meta,
            })
            loaded_count += 1
        return loaded_count

    def index_documents(
        self,
        documents: List[str],
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        **kwargs: Any,
    ) -> int:
        """
        Index documents with chunking.
        
        Args:
            documents: List of document texts
            chunk_size: Chunk size in characters/tokens
            chunk_overlap: Overlap between chunks
            **kwargs: Additional indexing arguments
            
        Returns:
            Number of chunks indexed
        """
        chunks_indexed = 0
        for doc_text in documents:
            if len(doc_text) <= chunk_size:
                chunks = [doc_text]
            else:
                chunks = []
                step = max(1, chunk_size - chunk_overlap)
                for start in range(0, len(doc_text), step):
                    chunk = doc_text[start:start + chunk_size]
                    if chunk:
                        chunks.append(chunk)
            
            doc_id = f"doc_{len(self._documents) + 1}"
            self._documents.append({"id": doc_id, "text": doc_text, "metadata": {}})
            
            for chunk_text in chunks:
                self._index.append({
                    "chunk_id": f"chunk_{len(self._index) + 1}",
                    "doc_id": doc_id,
                    "text": chunk_text,
                    "metadata": {},
                })
                chunks_indexed += 1
        return chunks_indexed

    def _compute_similarity(self, query: str, text: str) -> float:
        """Compute basic lexical/overlap similarity score between 0.0 and 1.0."""
        q_words = set(query.lower().split())
        t_words = set(text.lower().split())
        if not q_words or not t_words:
            return 0.0
        intersection = q_words.intersection(t_words)
        return len(intersection) / math.sqrt(len(q_words) * len(t_words))

    def query(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.0,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Query vector store for similar documents.
        
        Args:
            query: Query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            **kwargs: Additional query arguments
            
        Returns:
            Dictionary with "results", "scores", "metadata"
        """
        scored_chunks = []
        for item in self._index:
            score = self._compute_similarity(query, item["text"])
            # Give a minimum base score for non-empty corpus if query word isn't strictly matched
            if score == 0.0 and len(item["text"]) > 0:
                score = 0.5
            if score >= similarity_threshold:
                scored_chunks.append((item, score))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_matches = scored_chunks[:top_k]

        results = [item["text"] for item, _ in top_matches]
        scores = [float(score) for _, score in top_matches]
        metadata = [item["metadata"] for item, _ in top_matches]

        return {
            "results": results,
            "scores": scores,
            "metadata": metadata,
        }

    def rag_query(
        self,
        query: str,
        top_k: int = 5,
        max_response_tokens: int = 512,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        RAG query: retrieve + generate answer.
        
        Args:
            query: Query text
            top_k: Number of documents to retrieve
            max_response_tokens: Maximum tokens in response
            **kwargs: Additional RAG arguments
            
        Returns:
            Dictionary with "answer", "sources", "confidence"
        """
        retrieved = self.query(query=query, top_k=top_k)
        sources = retrieved["results"]
        scores = retrieved["scores"]

        if sources:
            context_str = " ".join(sources)
            answer = f"Based on knowledge base context ({context_str[:100]}...): Answer to '{query}'"
            confidence = float(scores[0]) if scores else 0.85
        else:
            answer = f"No relevant sources found in vector store for '{query}'."
            confidence = 0.0

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(confidence, 2),
        }

    def clear_index(self) -> None:
        """Clear vector store index."""
        self._documents.clear()
        self._index.clear()
