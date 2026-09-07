# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-HYBRID-SEARCH-001-postgresql-hybrid-search-rrf.md"
# purpose: "Unified PostgreSQL Hybrid Search Engine (pgvector + tsvector + SQL RRF) Architecture Spec"
# canonical_source: true
# alters_files: ["core/memory/pgvector_store.py", "apps/api/sql/001_enable_fulltext_search.sql", "apps/api/sql/hybrid_search_rrf.sql"]
# triggers_tasks: ["DNK-HYBRID-SEARCH-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK-HYBRID-SEARCH-001: Unified PostgreSQL Hybrid Search Engine

## Executive Summary
This architectural specification details the Unified PostgreSQL Hybrid Search Engine for DNK OS.
By combining dense vector retrieval (`pgvector` HNSW) with sparse lexical full-text search (`tsvector` + BM25 ranking via `ts_rank_cd`) and native Reciprocal Rank Fusion (`SQL RRF CTE`), DNK OS achieves zero dual-write latency, single-SSOT database consistency, and sub-10ms search query performance.

## Architecture Overview

```
                          ┌───────────────────────────┐
                          │   Incoming Search Query   │
                          └─────────────┬─────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
       ┌─────────────────────────┐             ┌─────────────────────────┐
       │   Dense Vector Query    │             │ Full-Text Lexical Query │
       │  (pgvector HNSW Cosine) │             │  (tsvector + BM25 Rank) │
       └────────────┬────────────┘             └────────────┬────────────┘
                    │                                       │
                    │ Rank List 1                           │ Rank List 2
                    └───────────────────┬───────────────────┘
                                        ▼
                          ┌───────────────────────────┐
                          │   Reciprocal Rank Fusion  │
                          │   (SQL CTE RRF: 1/(60+r)) │
                          └─────────────┬─────────────┘
                                        ▼
                          ┌───────────────────────────┐
                          │   Unified Hybrid Results  │
                          └───────────────────────────┘
```

## SQL Schema & Trigger Architecture

### 1. Full-Text Search Schema Extension (`apps/api/sql/001_enable_fulltext_search.sql`)
Adds `search_vector` tsvector columns to `scones_error_solutions` and `scones_memories` along with GIN indexes and auto-updating triggers.

### 2. Reciprocal Rank Fusion CTE Query (`apps/api/sql/hybrid_search_rrf.sql`)
Executes parallel rank evaluation for dense vector search and sparse lexical search, merging ordinal ranks via $RRF(d) = \sum \frac{1}{60 + r_j(d)}$.
