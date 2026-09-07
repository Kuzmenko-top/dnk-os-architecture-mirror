# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-ARCH-019_llamaindex-patterns.md"
# purpose: "Architecture Patterns and Topology Spec for LlamaIndex Framework Assimilation"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

# 🏛️ ARCHITECTURE SPEC: LLAMAINDEX PATTERNS (DNK-ARCH-019)

Architecture patterns, indexing topology, and retrieval pipeline specifications assimilated from `run-llama/llama_index` into `DNK_HUB`.

---

## 📌 Architectural Topology

LlamaIndex decoupling comprises 4 primary pipeline layers:

```
[ Data Sources ] (PDF, Web, Slack, Notion, SQL)
       │
       ▼
 1. INGESTION LAYER ───► [ BaseReader ] ───► Document Stream
                               │
                               ▼
                        [ NodeParser ] ──► Atomic Nodes (with hierarchy & metadata)
                               │
       ┌───────────────────────┴────────────────────────┐
       ▼                                                ▼
 2. STORAGE & INDEXING                          [ Embedding Model ]
       │                                                │
       ▼                                                ▼
   [ BaseIndex ] ◄────────────────────────────── Dense Vectors
   (Vector, Keyword, Tree, Summary)
       │
       ▼
 3. RETRIEVAL & ROUTING LAYER
       │
       ├───────────────────────► [ BaseRetriever ]
       ├───────────────────────► [ RouterQueryEngine ] (Selector Routing)
       └───────────────────────► [ SubQuestionEngine ] (Decomposition Graph)
                               │
                               ▼
 4. POST-PROCESSING & SYNTHESIS
       │
       ├───────────────────────► [ Postprocessor / Reranker ] (Score Filter / Cross-Encoder)
       └───────────────────────► [ ResponseSynthesizer ] ───► Final Response Output
```

---

## 🔑 Core Architectural Patterns

### Pattern 1: Multi-Index Heterogeneous Router Pattern
The `RouterQueryEngine` employs an LLM or vector selector (`LLMSingleSelector` / `LLMMultiSelector`) to direct user queries to the optimal underlying query engine or storage backend (e.g. SQL engine for structured analytics vs Vector store for semantic text search).

### Pattern 2: Sub-Question Query Decomposition
Complex analytical queries are decomposed into atomic sub-questions with assigned metadata targets. Each sub-question executes concurrently across dedicated sub-retrievers, and their results are unified by a synthesis prompt into a consolidated answer.

### Pattern 3: Hierarchical Parent-Child Chunking & Retrieval
Documents are split into a two-tier hierarchy:
- **Parent Nodes:** Large context windows (e.g. 1024-2048 tokens) that preserve global document structure.
- **Child Nodes:** Small granular chunks (e.g. 128-256 tokens) embedded for high-precision vector search.
During retrieval, matching Child Nodes automatically resolve to their Parent Node IDs, sending full context windows to the LLM.

### Pattern 4: Sentence Window & HyDE Query Transformation
- **Sentence Window RAG:** Embedded vectors represent individual sentences. Upon retrieval, the engine fetches a configurable window of surrounding sentences (`window_size=3`) to enrich context without polluting vector representations.
- **HyDE (Hypothetical Document Embedding):** An LLM generates a candidate hypothetical response. The candidate text's embedding vector is then used for nearest-neighbor search, bridging the query-to-doc semantic gap.

### Pattern 5: Two-Stage Re-Ranking Pipeline
First-stage dense vector retrieval yields top-$K$ candidates ($K=50$). Second-stage cross-encoder rerankers (`SentenceTransformerRerank` or `CohereRerank`) calculate full attention scores across query-chunk pairs, selecting top-$N$ ($N=5$) chunks for final LLM synthesis.

---

## 🛡️ Integration Contract with DNK OS Core
In DNK OS (`DNK-DEEP-RAG-2.0`), LlamaIndex patterns map into existing `DNKServices`:
- `SimpleDirectoryReader` & `NodeParser` ➔ `dnk_doc_ingestion_service`
- `VectorStoreIndex` & `KeywordTable` ➔ `dnk_vector_index_service`
- `RouterQueryEngine` & `SubQuestionQueryEngine` ➔ `dnk_rag_router_agent`
