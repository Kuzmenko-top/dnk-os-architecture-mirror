---
name: hybrid-search-and-memory-architecture
description: "Use when designing vector search, hybrid retrieval, and RRF."
version: 1.0.0
author: Gerych Core + Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [vector-search, pgvector, hybrid-search, rrf, qdrant, lancedb, scones, rag]
    category: software-development
    requires_toolsets: [terminal]
---

# Hybrid Search, Vector Stores & Cognitive Memory Architecture

A class-level architectural guide and evaluation framework for choosing and implementing dense vector retrieval, sparse lexical search (BM25/tsvector), Reciprocal Rank Fusion (RRF) reranking, and cognitive memory hierarchies.

## When to Use

Use this skill when:
- Evaluating vector database options for RAG pipelines, agent memory, or semantic search.
- Implementing hybrid search combining dense embeddings with sparse keyword matching.
- Formulating and executing Reciprocal Rank Fusion (RRF) across heterogeneous rank lists.
- Deciding between Unified RDBMS (PostgreSQL + pgvector), Standalone Vector DBs (Qdrant/Milvus), and Embedded stores (LanceDB/DuckDB).
- Architecting multi-tenant memory engines with ACID guarantees and zero dual-write lag.

## Core Architectural Decision Matrix

| Dimension | Unified PostgreSQL (`pgvector` + `tsvector`) | Standalone Vector DB (Qdrant / Milvus) | Embedded Vector Store (LanceDB / SQLite-vec) |
|---|---|---|---|
| **Data Consistency** | 🏆 **100% ACID** (single transaction for entities + vectors) | ⚠️ Eventual consistency (requires Outbox/2PC to avoid sync lag) | 🟢 In-process ACID / single file |
| **Hybrid Search** | 🏆 Native SQL CTE with Cosine Distance + `tsvector` + RRF | ✅ Native multi-vector & sparse payloads | ✅ Native Tantivy / BM25 + Vector |
| **Operational Footprint** | 🏆 **Zero extra services** (uses existing Postgres cluster) | ⚠️ Separate daemon, separate backup, gRPC/HTTP connection pool | 🏆 Zero-ops (embedded C/Rust library) |
| **Query Latency (p95)** | ~2–8 ms (with HNSW index `m=16, ef_construction=64`) | ~5–15 ms (network hop + gRPC serialization) | < 2 ms (in-memory / local disk) |
| **Multi-Tenancy** | Native Row-Level Security (RLS) & tenant isolation | Filter-based namespace partitioning | Directory / table partitioning |
| **Scale Envelope** | 100K – 20M vectors per node | 10M – 1B+ vectors (distributed clustering) | 10K – 50M vectors (local disk/S3) |

## The Reciprocal Rank Fusion (RRF) Model

Reciprocal Rank Fusion unifies ranked result lists from $m$ distinct retrieval strategies (e.g., dense semantic embeddings and sparse BM25 lexical matches) without requiring cross-score calibration.

### Mathematical Formulation
$$RRF(d) = \sum_{j=1}^{m} \frac{1}{k + r_j(d)}$$

Where:
- $k \in \mathbb{N}^+$ is the ranking smoothing constant (standard default: $k = 60$).
- $r_j(d)$ is the 1-based ordinal rank of document $d$ in the $j$-th retrieval candidate list.
- If document $d$ does not appear in candidate list $R_j$, its score contribution from that retriever is $0$.

### Unified PostgreSQL Hybrid Search Implementation (SQL RRF)

```sql
WITH vector_matches AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY embedding <=> %(query_embedding)s) AS vector_rank
    FROM scones_memories
    WHERE tenant_id = %(tenant_id)s AND workspace_id = %(workspace_id)s
    LIMIT %(candidate_limit)s
),
text_matches AS (
    SELECT id, ROW_NUMBER() OVER (ORDER BY ts_rank_cd(text_vector, plainto_tsquery('english', %(keyword_query)s)) DESC) AS text_rank
    FROM scones_memories
    WHERE tenant_id = %(tenant_id)s AND workspace_id = %(workspace_id)s 
      AND text_vector @@ plainto_tsquery('english', %(keyword_query)s)
    LIMIT %(candidate_limit)s
)
SELECT 
    COALESCE(v.id, t.id) AS id,
    (
        COALESCE(1.0 / (%(rrf_k)s + v.vector_rank), 0.0) + 
        COALESCE(1.0 / (%(rrf_k)s + t.text_rank), 0.0)
    ) AS rrf_score
FROM vector_matches v
FULL OUTER JOIN text_matches t ON v.id = t.id
ORDER BY rrf_score DESC
LIMIT %(top_k)s;
```

## Python High-Speed In-Memory RRF Reranker

```python
from typing import List, Dict, Any

def reciprocal_rank_fusion(
    ranked_lists: List[List[Dict[str, Any]]],
    id_key: str = "id",
    k: int = 60,
    top_k: int = 20
) -> List[Dict[str, Any]]:
    """
    Applies Reciprocal Rank Fusion across multiple candidate result lists.
    """
    scores: Dict[str, float] = {}
    doc_lookup: Dict[str, Dict[str, Any]] = {}

    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            doc_id = str(item[id_key])
            if doc_id not in doc_lookup:
                doc_lookup[doc_id] = item
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    results = []
    for doc_id, score in sorted_docs[:top_k]:
        doc = dict(doc_lookup[doc_id])
        doc["rrf_score"] = score
        results.append(doc)
    return results
```

## SCONES Cognitive Memory Layering (L0–L3)

- **L0 (Working Context)**: In-memory active scratchpad / session KV store.
- **L1 (AST CodeGraph & LLM-Wiki)**: Deterministic code entity symbol graph, caller/callee trees, and cross-linked topic digests.
- **L2 (Episodic Solutions)**: Distilled error-solution mappings (`scones_error_solutions`) with pgvector HNSW semantic retrieval.
- **L3 (Semantic Domain & Personalized Long-Term Memory)**: Long-term tenant/workspace isolated facts (`scones_longterm_memories`) queried via Unified Hybrid RRF, adjusted with Temporal Recency Decay ($\text{RRF} \times e^{-\lambda \cdot \Delta t}$) and maintained via Agentic Sleep Consolidation (L2 $\rightarrow$ L3 semantic distillation).

## Additional Reference Guides

- [Cross-Encoder Top-K Reranking Pipeline](references/cross_encoder_reranking_pipeline.md): Two-stage retrieval architecture with ms-marco-MiniLM / bge-reranker and graceful fallback.
- [PostgreSQL tsvector Triggers & UNION ALL RRF SQL CTE Pattern](references/postgresql_tsvector_rrf_triggers.md): Complete DDL trigger definitions and resilient UNION ALL RRF queries.
- [Temporal Recency Decay & Sleep Consolidation](references/temporal_decay_and_sleep_consolidation.md): Exponential age decay ($Score = RRF \times e^{-\lambda \Delta t}$) and L2 -> L3 Agentic Sleep semantic distillation.
- [Vector DB Tradeoffs & Benchmarks](references/vector_db_tradeoffs_and_benchmarks.md): Detailed comparative benchmarks between PostgreSQL pgvector, Qdrant, and LanceDB.

## Pitfalls & Anti-Patterns

1. **Premature Standalone Vector DB Adoption**: Introducing external vector stores (like Qdrant or Milvus) when dataset size is < 20M vectors introduces dual-write inconsistencies, requires distributed transactions, and adds infrastructure complexity.
2. **Raw Cosine Distance Merging**: Never sum or average raw Cosine distances ($0.0 \dots 2.0$) with BM25 scores ($0.0 \dots \infty$). Always convert raw retriever outputs to ordinal ranks and apply **Reciprocal Rank Fusion (RRF)**.
3. **Missing Tenant Filter in CTE**: When running hybrid SQL queries, ensure tenant and workspace isolation predicates are present in **both** vector and text search CTE blocks to prevent cross-tenant data leakage.
