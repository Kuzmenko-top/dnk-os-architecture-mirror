# Cross-Encoder Top-K Reranking Pipeline

## Overview

While Bi-Encoders (dense vectors like `text-embedding-3-large` or `all-MiniLM-L6-v2`) and Lexical BM25 (sparse `tsvector`) independently score candidate documents quickly, they lack cross-attention between query terms and document tokens.

Cross-Encoder models (`cross-encoder/ms-marco-MiniLM-L-6-v2`, `BAAI/bge-reranker-large`) process query and document concatenated together `[CLS] Query [SEP] Document [SEP]`, computing full cross-attention across all token pairs.

## Two-Stage Architecture

```
Query
  │
  ├────────────────────────┬────────────────────────┐
  ▼                        ▼                        ▼
pgvector Dense           tsvector Sparse          Filters (Tenant/Workspace)
(1536-dim Cosine)        (BM25 Lexical)           (Metadata / Category)
  │                        │                        │
  └───────────┬────────────┘                        │
              ▼                                     ▼
     Weighted RRF Fusion ◄──────────────────────────┘
     score = sum( w_j / (k + rank_j) )
              │
              ▼ Top-N Candidates (e.g. N=20)
     Cross-Encoder Reranker
     (ms-marco-MiniLM / bge-reranker)
              │
              ▼ Top-K Final Output (e.g. K=5)
```

## Python Implementation Pattern

```python
from typing import List, Dict, Any

class CrossEncoderReranker:
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None
        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(model_name)
        except Exception:
            self._model = None

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        if not query or not documents:
            return []
        
        if self._model is not None:
            pairs = [[query, doc.get("content", "")] for doc in documents]
            scores = self._model.predict(pairs)
            for doc, score in zip(documents, scores):
                doc["rerank_score"] = float(score)
        else:
            # Token-overlap semantic mimic fallback
            q_tokens = set(query.lower().split())
            for doc in documents:
                content = doc.get("content", "").lower()
                doc_tokens = set(content.split())
                overlap = len(q_tokens & doc_tokens) / max(len(q_tokens), 1)
                doc["rerank_score"] = float(overlap)

        return sorted(documents, key=lambda d: d.get("rerank_score", 0.0), reverse=True)[:top_k]
```
