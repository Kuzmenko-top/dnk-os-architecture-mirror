# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-ARCH-039_rag-anything-patterns.md"
# purpose: "Architecture & Structural Patterns: Hexagonal Adapter, Modality Processors, and Cross-Modal Graph Topology for RAG-Anything."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🏗️ DNK-ARCH-039: Multimodal Knowledge Graph RAG Architecture & Patterns

## 1. Hexagonal Integration Topology
The assimilated RAG-Anything architecture is integrated into DNK OS through a strict hexagonal boundary:

```
┌─────────────────────────────────────────────────────────────┐
│                    DNK OS Swarm Layer                       │
│  [gerych_builder]    [gerych_researcher]   [dnk_shopify]    │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / WebSocket / In-Process
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               FastAPI API Layer (apps/api)                  │
│       /api/v1/rag/ingest        /api/v1/rag/query            │
│       /api/v1/rag/ingest-text   /api/v1/rag/query-multimodal │
│       /api/v1/rag/graph/{id}                                │
└──────────────────────────────┬──────────────────────────────┘
                               │ Port Contract (MultimodalRAGPort)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│           Hexagonal Adapter: DNKRAGAnythingAdapter          │
│               (core/adapters/dnk_rag_anything_adapter.py)   │
├──────────────────────────────┬──────────────────────────────┤
│  DocumentDecomposer          │  Cross-Modal Graph Engine    │
│  - Text Chunking             │  - Nodes (Element metadata)  │
│  - DNKImageProcessor         │  - Edges (Context/Expands)   │
│  - DNKTableProcessor         │  - Topology Exporter         │
│  - DNKEquationProcessor      │  - SpendGuard Cost Meter     │
└──────────────────────────────┴──────────────────────────────┘
```

## 2. Core Architectural Components

### 2.1 Modality Processors (`core/rag/processors.py`)
Each non-text element is routed to a specialized domain processor:
- **`DNKImageProcessor`**: Synthesizes descriptive semantic captions, extracts bounding box coordinates, and prepares visual payload for VLM context windows.
- **`DNKTableProcessor`**: Parses Markdown / HTML tables into structured column headers and matrix rows, preventing cell degradation during retrieval.
- **`DNKEquationProcessor`**: Cleans LaTeX mathematical expressions, strips delimiters, and extracts individual symbol variables for AST indexing.

### 2.2 Cross-Modal Graph Topology
Documents are represented as attributed directed graphs:
- **Sequential Context Edges (`precedes`)**: Preserves textual narrative flow between sequential blocks.
- **Semantic Expansion Edges (`illustrates_or_expands`)**: Connects mathematical equations, visual diagrams, and tables to their governing explanatory text blocks.

### 2.3 SpendGuard VLM Protection
VLM multi-modal queries with high image resolutions can incur high token spend. The adapter enforces:
- Dynamic calculation of image token weight ($0.002 per visual element).
- Hard ceiling rejection via `SpendGuard` error before API dispatch if session limit is reached.
