# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/langchain/RN-019_llamaindex-research.md"
# purpose: "SOTA Research and Pattern Extraction for run-llama/llama_index"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Research: LlamaIndex Framework Assimilation (RN-019)

In-depth technical research and architectural pattern extraction of `run-llama/llama_index` (15,000+ stars, MIT license) for integration into the DNK OS RAG and Knowledge Graph engine (`DNK-DEEP-RAG-2.0`).

## 📋 Research Metadata
- **Donor Repository:** `run-llama/llama_index`
- **Task ID:** `DNK-ASSIM-019`
- **Domain:** `langchain`
- **License:** MIT
- **Key Modules Analyzed:**
  - `llama_index.core.indices` — VectorIndex, KeywordTableIndex, TreeIndex, SummaryIndex
  - `llama_index.core.readers` — SimpleDirectoryReader, Web, Notion, Slack, GitHub connectors
  - `llama_index.core.query_engine` — RouterQueryEngine, SubQuestionQueryEngine, RetrieverQueryEngine
  - `llama_index.core.node_parser` — HierarchicalNodeParser, SentenceSplitter, CodeSplitter
  - `llama_index.core.embeddings` — Multi-modal, Cosine/Dot product, MMR similarity
  - `llama_index.core.postprocessor` — SimilarityPostprocessor, SentenceTransformerRerank, LLMRerank

---

## 🏗️ Key Patterns Extracted

### 1. Index Structures Taxonomy
LlamaIndex organizes unstructured text into structured representations optimized for retrieval:
- **VectorStoreIndex:** Converts Nodes into dense vector embeddings and stores them in a Vector Store (Milvus, Qdrant, PGVector). Fast semantic retrieval.
- **SummaryIndex (ListIndex):** Sequence of Nodes; iterates through all nodes or uses LLM summary generation during query execution.
- **TreeIndex:** Hierarchical tree of parent-child summaries. Querying traverses top-down from root to leaves for multi-document synthesis.
- **KeywordTableIndex:** Extracts keywords from Nodes into an inverted index. Fast keyword lookup without heavy embedding costs.

### 2. Data Connectors (Readers)
Connectors ingest data from heterogeneous sources (PDF, Web, Slack, Notion, S3, GitHub) into standardized `Document` objects containing `text`, `metadata`, and `doc_id`.

```python
# 🧬 [DONOR START: run-llama/llama_index]
from llama_index.core import SimpleDirectoryReader

reader = SimpleDirectoryReader(
    input_dir="./data",
    recursive=True,
    required_exts=[".pdf", ".md", ".py"]
)
documents = reader.load_data()
# 🧬 [DONOR END: run-llama/llama_index]
```

### 3. Advanced Node Parsers & Chunking
Node parsers decompose `Document` objects into atomic `Node` instances with parent-child relationships and metadata preservation:
- **SentenceSplitter:** Respects sentence boundaries while respecting `chunk_size` and `chunk_overlap`.
- **HierarchicalNodeParser:** Creates multi-level chunk hierarchies (e.g., 2048-token parent chunks down to 128-token leaf chunks) with `parent_node` references.
- **CodeSplitter:** AST-aware code parser for Python, TypeScript, and Rust that maintains function and class boundaries.

### 4. Query Engines & Retrieval Routing
- **RouterQueryEngine:** Routes queries to specialized query engines or indexes based on query intent using LLM or selector models (`LLMSingleSelector`).
- **SubQuestionQueryEngine:** Decomposes complex multi-part queries into atomic sub-questions, executes sub-queries against relevant sub-indexes, and synthesizes a composite response.
- **RecursiveRetriever:** Recursively traverses Node relationships (e.g. from parent chunk to child chunk or table reference) during retrieval.

```python
# 🧬 [DONOR START: run-llama/llama_index]
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata

query_engine_tools = [
    QueryEngineTool(
        query_engine=vector_query_engine,
        metadata=ToolMetadata(name="financial_docs", description="Quarterly financial statements")
    )
]
sub_question_engine = SubQuestionQueryEngine.from_defaults(query_engine_tools=query_engine_tools)
response = sub_question_engine.query("Compare revenue growth between Q1 and Q2")
# 🧬 [DONOR END: run-llama/llama_index]
```

### 5. Multi-Modal Embeddings & Similarity Reranking
- **Multi-Modal Embeddings:** Joint embedding spaces for text + images (CLIP, OpenCLIP) allowing text-to-image and image-to-text semantic matching.
- **Maximal Marginal Relevance (MMR):** Balances relevance with diversity to eliminate redundant retrieved context chunks.
- **Post-Processing & Reranking:** Postprocessors filter chunks by score thresholds or apply cross-encoder rerankers (Cohere Rerank, BGE Reranker) before LLM prompt construction.

### 6. RAG Optimizations (HyDE & Query Rewriting)
- **HyDE (Hypothetical Document Embeddings):** Generates a hypothetical answer string with an LLM, embeds the hypothetical text, and retrieves actual documents matching the hypothetical answer.
- **Sentence Window RAG:** Embeds small sentence windows for precise vector matching, but expands context to surrounding sentence windows during generation.

---

## 🛡️ License & Clean-Room Compliance
- **License:** MIT License.
- **Compliance:** All contracts and patterns assimilated into `DNK_HUB` use pure abstract interface definitions (`abc.ABC`) without direct third-party proprietary dependencies.
