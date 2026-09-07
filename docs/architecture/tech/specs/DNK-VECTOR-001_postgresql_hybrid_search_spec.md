# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-VECTOR-001_postgresql_hybrid_search_spec.md"
# purpose: "PostgreSQL Hybrid Search (pgvector + tsvector) with Reciprocal Rank Fusion & Cross-Encoder Reranking Architecture Specification"
# canonical_source: true
# alters_files: [
#   "apps/api/db/vector_store.py",
#   "apps/api/services/postgres_dense_vector_search.py",
#   "apps/api/services/postgres_sparse_vector_search.py",
#   "apps/api/services/reciprocal_rank_fusion.py",
#   "apps/api/services/cross_encoder_reranker.py",
#   "apps/api/services/postgres_hybrid_search_engine.py",
#   "apps/api/routers/vector_search.py",
#   "apps/web/components/vector/HybridSearchInterface.tsx",
#   "apps/web/components/vector/SearchResultsList.tsx",
#   "apps/web/components/vector/RerankedResultsCard.tsx",
#   "apps/web/lib/api/vector_client.ts",
#   "tests/vector/test_hybrid_search.py",
#   "tests/vector/test_reciprocal_rank_fusion.py",
#   "tests/vector/test_cross_encoder_reranker.py"
# ]
# triggers_tasks: ["DNK-VECTOR-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# DNK-VECTOR-001: PostgreSQL Hybrid Search (pgvector + tsvector) з Reciprocal Rank Fusion

## 1. Executive Summary
DNK-VECTOR-001 реалізує високопродуктивний, багатотенантний та відмовостійкий гібридний пошуковий рушій на базі PostgreSQL без потреби у зовнішніх векторних базах даних (Zero Dual-Write Architecture).

Рушій об'єднує:
1. **Dense Vector Search**: pgvector (1536-dim, cosine/dot distance, IVFFlat/HNSW індекси).
2. **Sparse Vector Search**: PostgreSQL `tsvector` (BM25 / `ts_rank_cd` full-text search з підтримкою стемінгу).
3. **Reciprocal Rank Fusion (RRF)**: Алгоритм злиття скорів $RRF(d) = \sum_{m \in M} \frac{w_m}{k + r_m(d)}$, де $k=60$ за замовчуванням, з можливістю налаштування ваг ($w_{dense}, w_{sparse}$).
4. **Cross-Encoder Reranking**: Модель попарного скорингу (ms-marco-MiniLM-L-6-v2 / bge-reranker) для фінального Top-K ранжування.
5. **Multi-Tenant & Workspace Isolation**: Жорстка ізоляція на рівні SQL WHERE clauses (`tenant_id`, `workspace_id`).
6. **FastAPI REST API**: Ендпоінти для ingestion (single/batch), hybrid search, pure dense/sparse search, reranking та collection statistics.

---

## 2. TaskDNA Evolutionary DAG

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  Phase 1: Vector Store & Schema Ingestion Layer                             │
│  - SQL Schema: vector_memory_embeddings & vector_collection_stats           │
│  - apps/api/db/vector_store.py (PostgreSQL VectorStore with connection pool)│
│  - Dense & Sparse Ingestion, Multi-tenant filtering                         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Phase 2: Hybrid Query Streams, RRF Engine & Cross-Encoder Reranker          │
│  - apps/api/services/postgres_dense_vector_search.py                        │
│  - apps/api/services/postgres_sparse_vector_search.py                       │
│  - apps/api/services/reciprocal_rank_fusion.py                              │
│  - apps/api/services/cross_encoder_reranker.py                              │
│  - apps/api/services/postgres_hybrid_search_engine.py                       │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Phase 3: FastAPI Router, Web Components, E2E Verification & Evidence       │
│  - apps/api/routers/vector_search.py (REST API)                             │
│  - apps/web/components/vector/ & apps/web/lib/api/vector_client.ts           │
│  - tests/vector/ (Unit, Integration & E2E Tests)                            │
│  - Master Quality Gate & Evidence Certification                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Mandatory Standards & Invariants
- **MRH Headers**: Всі файли Python/TS/Markdown повинні містити `DNK-MRH-HEADER` (DNK-STD-0075).
- **Core Freeze**: Збереження цілісності існуючих моделей та сервісів.
- **Path Hygiene**: Лише відносні шляхи (`./`, `../`).
- **Quality Gate**: 100% проходження тестів (`bash scripts/verify_all.sh`).
