---
name: "llamaindex_assimilated"
description: "SOTA indices, patterns, and executable recipes for run-llama/llama_index framework assimilation."
version: "1.0.0"
category: "research"
assimilated_at: "2026-08-16"
triggers:
  - "llamaindex"
  - "llama_index"
  - "vector_index"
  - "router_query_engine"
  - "sub_question_query_engine"
  - "node_parser"
---

# 🌐 LlamaIndex Framework Assimilation Index

Meta-index tracking RAG architecture, query routing engines, node parsers, and component contracts assimilated from `run-llama/llama_index`.

## 📁 Core Specifications

1. **[Research & Evidence Trail](../../docs/reports/rd_assimilation/langchain/RN-019_llamaindex-research.md)**
   - Analysis of Index structures, 20+ data connectors, SubQuestion & Router engines, HyDE, and reranking.

2. **[Architecture Patterns Specification](../../docs/tech/specs/DNK-ARCH-019_llamaindex-patterns.md)**
   - Architectural topology, parent-child chunking, sentence window RAG, and two-stage cross-encoder reranking.

3. **[Component Interfaces & Contracts](../../docs/tech/specs/DNK-COMP-019_llamaindex-contracts.md)**
   - Type-safe abstract Python contracts (`BaseNode`, `QueryBundle`, `BaseReader`, `BaseRetriever`, `BaseQueryEngine`).

## 🛠️ Executable Recipes

### Recipe 1: Quick Verification
Run path hygiene verification across all assimilated specifications:
```bash
PYTHONPATH=. uv run pytest tests/verification/test_path_hygiene.py
```

### Recipe 2: Python Contracts Verification
Verify interface contracts in python:
```python
from docs.tech.specs.DNK_COMP_019_llamaindex_contracts import Document, QueryBundle, BaseRetriever
doc = Document(text="Sample text", doc_id="doc_1")
print(f"Document initialized: {doc.doc_id}")
```
