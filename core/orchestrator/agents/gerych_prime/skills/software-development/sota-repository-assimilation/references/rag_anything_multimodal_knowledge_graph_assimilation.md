# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/rag_anything_multimodal_knowledge_graph_assimilation.md"
# purpose: "Reference architecture, contracts, and patterns for HKUDS/RAG-Anything multimodal RAG assimilation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.5.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🧬 HKUDS/RAG-Anything Multimodal RAG & Knowledge Graph Assimilation Patterns

## 1. Overview & Provenance
- **Source**: `HKUDS/RAG-Anything` (University of Hong Kong Data Intelligence Lab, authors of LightRAG and VideoRAG).
- **License**: **MIT License** -> **Track 1: Direct Template & Hexagonal Adapter Assimilation**.
- **Core Value**: Extends GraphRAG from pure text into full multimodal comprehension (PDFs, diagrams, tables, LaTeX math equations, images) by binding heterogeneous media into a unified knowledge graph.

## 2. Key Architectural Invariants
1. **Multi-Stage Document Decomposition & Extractor Cascade**:
   - Layout analysis via MinerU (`magic-pdf`), Docling, or PaddleOCR.
   - **Zero-Dependency Fallbacks**: In constrained environments without external heavy binaries:
     - **DOCX Extractor**: Parses `.docx` ZIP package via `zipfile` + `xml.etree.ElementTree` without `python-docx`:
       - `w:p` -> Clean paragraph extraction.
       - `w:tbl` -> Markdown formatted tables (`| Col 1 | Col 2 |`).
       - `m:oMath` -> Mathematical expressions serialized into LaTeX `$$...$$`.
       - `word/media/` -> Direct binary extraction of embedded diagrams and images to disk cache.
     - **Pure-Python PDF Extractor**: Uncompresses PDF streams using `zlib` FlateDecode and parses text blocks (`BT ... ET`, `Tj`, `TJ`).
     - **Canvas Visual Extractor**: Parses Canvas / Visual Working Cabinet nodes (`ImageNode`, `TableNode`, `EquationNode`, `DocNode`) into `MultimodalElement` streams with normalized spatial coordinates `{x1, y1, x2, y2}`.
2. **Specialized Modality Processors (`core/rag/processors.py`)**:
   - `DNKImageProcessor`: Spatial coordinate preservation + VLM semantic captioning.
   - `DNKTableProcessor`: Table structure serialization (Markdown / JSON-LD) preserving column-row relationships.
   - `DNKEquationProcessor`: Preserves LaTeX AST and binds formulas to surrounding explanatory prose.
3. **Sidecar Asset Caching Pattern (`SidecarAssetCache`)**:
   - Physical asset storage in `.extracted_assets/<doc_hash>/` (must be added to `.gitignore`).
   - Sidecar manifest `.meta.json` storing SHA-256 hash, extraction timestamp, modality element counts, and bounding box mappings.
4. **Dual-Level Multimodal Knowledge Graph (`core/rag/knowledge_graph.py`)**:
   - **LightRAG Dual-Level Topology**:
     - **High-level (Thematic Layer)**: `THEME` and `DOCUMENT` nodes representing macro-concepts, chapters, and topics.
     - **Low-level (Entity & Artifact Layer)**: `ENTITY`, `ARTIFACT`, and `CHUNK` nodes representing specific named entities, technical acronyms, LaTeX formulas, tables, and images.
   - **Cross-Modal Typed Edges (`GraphEdge`)**:
     - `belongs_to_theme` (weight 1.5): Binds low-level entities and chunks to high-level themes.
     - `illustrates` (weight 2.0): Binds visual figures/images to the text chunks they illustrate.
     - `contains_table` (weight 1.5): Binds structured tabular data to context.
     - `references_math` (weight 1.5): Links LaTeX formulas and equations to text nodes.
     - `precedes` (weight 1.0): Preserves chronological/document narrative order.
5. **Multi-Tenant Knowledge Graphs & Cross-Workspace Retrieval**:
   - **Isolated Workspaces**: The adapter maintains `self.knowledge_graphs: Dict[str, DualLevelKnowledgeGraph]`. Each workspace (`ws-alpha-001`, `ws-reburn-001`, `global-marketing-hub`) has its own discrete, encapsulated graph.
   - **Cross-Workspace Retrieval (`workspace_ids`)**: In `query_dual_level`, passing `workspace_ids: List[str]` queries multiple isolated knowledge graphs simultaneously, deduplicating entities, context, and visual artifacts across tenants without cross-workspace contamination.
6. **Grounded Marketing Banner Synthesizer (`core/rag/marketing_banner.py`)**:
   - **Zero Visual/Copy Hallucination**: Combines global copywriting/marketing patterns (AIDA, PAS, FAB, BAB) with precise domain technical facts and genuine extracted diagram/photo sidecars (`.extracted_assets/`).
   - **Multi-Format Export**: Generates `MarketingBannerSpec` with:
     - Standalone SVG banner with badges and gradients.
     - Dark-mode responsive HTML5 component card.
     - Remotion video props (`title`, `bullets`, `cta_text`, `image_asset_url`) for programmatic video rendering.
     - Visual Shell / CanvasEngine node (React Flow) for live canvas collaboration.
7. **SCONES Memory Engine Synchronization (`sync_to_scones`)**:
   - High-level themes and high-importance multimodal artifacts are automatically synced to SCONES cognitive memory (`ws-alpha-001`).
   - Tags: `rag_knowledge_graph`, `theme`, `artifact`, `multimodal`.
   - Importance weights: `0.9` for macro-themes, `0.7` for multimodal artifacts.
8. **Canvas / Visual Shell Export (`to_canvas_graph`)**:
   - Direct serialization to React Flow / CanvasEngine graph models.
   - Node positioning: 2-column spatial layout (`x: 100` for High-level themes, `x: 600` for Low-level entities/artifacts).
   - Invariant: Nodes must include `"position": {"x": ..., "y": ...}` as well as top-level `"x"` and `"y"`.
   - Invariant: Edges must include `"data": {"relation": ..., "weight": ...}` for UI edge labels.

## 3. DNK OS Swarm Adaptation & Hexagonal Contract

### Hexagonal Port (`core/adapters/dnk_rag_anything_adapter.py`)
```python
from typing import Protocol, List, Dict, Any, Optional
from pydantic import BaseModel, Field
from core.rag.knowledge_graph import DualLevelKnowledgeGraph, GraphNodeType

class RAGConfig(BaseModel):
    storage_dir: str = Field(default="./data/rag_storage")
    cache_dir: str = Field(default=".extracted_assets")
    max_file_size_mb: int = Field(default=25)
    spend_guard_cap_usd: float = Field(default=5.0)
    enable_knowledge_graph: bool = Field(default=True)
    sync_scones: bool = Field(default=False)

class MultimodalRAGPort(ABC):
    @abstractmethod
    def ingest_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None, workspace_id: str = "ws-alpha-001") -> str: ...
    
    @abstractmethod
    def ingest_canvas(self, canvas_data: Any, canvas_id: str = "canvas", metadata: Optional[Dict[str, Any]] = None, workspace_id: str = "ws-alpha-001") -> str: ...
    
    @abstractmethod
    def ingest_text(self, text: str, title: str = "raw_snippet", metadata: Optional[Dict[str, Any]] = None, workspace_id: str = "ws-alpha-001") -> str: ...
    
    @abstractmethod
    def query(self, prompt: str, mode: str = "hybrid") -> Dict[str, Any]: ...
    
    @abstractmethod
    def query_multimodal(self, prompt: str, elements: List[MultimodalElement], mode: str = "hybrid") -> Dict[str, Any]: ...
    
    @abstractmethod
    def get_document_graph(self, doc_id: str) -> Dict[str, Any]: ...

    @abstractmethod
    def query_dual_level(self, query: str, mode: str = "hybrid", max_nodes: int = 15, workspace_id: str = "ws-alpha-001", workspace_ids: Optional[List[str]] = None) -> Dict[str, Any]: ...

    @abstractmethod
    def sync_scones(self, scones_engine: Any = None, workspace_id: str = "ws-alpha-001") -> Dict[str, Any]: ...

    @abstractmethod
    def export_canvas_graph(self, workspace_id: str = "ws-alpha-001") -> Dict[str, Any]: ...
```

### Module Export & Namespace Discovery
Always export port, pipeline, processors, knowledge graph, and marketing synthesizer in `core/rag/__init__.py`:
```python
# core/rag/__init__.py
from core.rag.processors import (
    ModalityType,
    MultimodalElement,
    BaseModalProcessor,
    DNKImageProcessor,
    DNKTableProcessor,
    DNKEquationProcessor,
    DocumentDecomposer,
)
from core.rag.pipeline import (
    MultimodalExtractionPipeline,
    SidecarAssetCache,
    BaseDocumentExtractor,
    PurePythonPDFExtractor,
    DocxExtractor,
    CanvasVisualExtractor,
)
from core.rag.knowledge_graph import (
    GraphNodeType,
    GraphNode,
    GraphEdge,
    DualLevelKnowledgeGraph,
)
from core.rag.marketing_banner import (
    MarketingFramework,
    MarketingBannerSpec,
    GroundedMarketingBannerSynthesizer,
)
```

## 4. FastAPI Endpoints & Swarm Tooling Invariants

### 1. FastAPI Dependency Injection (`apps/api/routers/rag.py`)
- **Strict Invariant**: Route handlers MUST declare adapter dependencies using FastAPI `Depends(get_rag_adapter)`:
  ```python
  @router.post("/query-dual-level", response_model=DualLevelQueryResponse)
  async def query_dual_level(
      request: DualLevelQueryRequest,
      adapter: DNKRAGAnythingAdapter = Depends(get_rag_adapter)
  ):
      ...
  ```
- **Marketing Banner Endpoint**:
  ```python
  @router.post("/marketing-banner", response_model=MarketingBannerResponse)
  async def generate_marketing_banner(
      request: MarketingBannerRequest,
      adapter: DNKRAGAnythingAdapter = Depends(get_rag_adapter)
  ):
      ...
  ```

### 2. Git-Tracked Swarm Tools Location (`core/orchestrator/tools/`)
- Production tools live in `core/orchestrator/tools/dnk_rag_tool.py`:
  - `dnk_rag_query` -> Multimodal hybrid query with optional cross-workspace `workspace_ids`.
  - `dnk_rag_ingest` -> Text, PDF, DOCX, and Canvas document ingestion into workspace.
  - `dnk_generate_marketing_banner` -> Zero-hallucination banner synthesis combining marketing framework and product specs.
- Register all swarm tools in `core/orchestrator/tool_aliases.py`:
  - `rag.query` -> `core/orchestrator/tools/dnk_rag_tool.py:dnk_rag_query`
  - `rag.ingest` -> `core/orchestrator/tools/dnk_rag_tool.py:dnk_rag_ingest`
  - `marketing.generate_banner` -> `core/orchestrator/tools/dnk_rag_tool.py:dnk_generate_marketing_banner`

## 5. Security & Operational Guards (Mandatory Invariants)
1. **Path Traversal Sanitization**:
   - Every file ingestion must pass through `_sanitize_path`:
   ```python
   def _sanitize_path(self, path_str: str) -> Path:
       p = Path(path_str).resolve()
       if ".." in path_str or not p.exists():
           raise ValueError(f"Path traversal detected or invalid path: {path_str}")
       return p
   ```
2. **SpendGuard Token Budgeting**:
   - VLM queries and image captioning can cause token spikes. Guard all calls with pre-flight token estimations and strict workspace spend caps (`spendguard_budget_usd=25.0`).
3. **Sidecar Cache Hygiene**:
   - Always ensure `.extracted_assets/` is in `.gitignore` so generated cache assets and extracted images do not dirty the git tree.
4. **Canvas Visual Contract**:
   - When converting graph nodes to Canvas/React Flow representations, ensure nodes contain `position: {"x": ..., "y": ...}` and edges carry `data: {"relation": ..., "weight": ...}` to avoid front-end renderer crashes.
5. **Git Workspace Hygiene Preflight Gate**:
   - `scripts/verify_all.sh` stage `[2.1/4]` enforces git workspace hygiene.
   - Always run `git add <test_files> <target_files>` before running verification suites.

## 6. Verification & Test Suites (35/35 Tests Passing)
- `tests/core/test_rag_adapter.py`: Protocol contracts, ABC validation, SpendGuard caps, topology retrieval (5 tests).
- `tests/rag/test_rag_anything_adapter.py`: End-to-end multi-modal decomposition, processors, API route validation (7 tests).
- `tests/rag/test_multimodal_pipeline.py`: Sidecar cache, pure-Python PDF/DOCX extractors, Canvas visual extractor, orchestration (6 tests).
- `tests/rag/test_knowledge_graph_scones.py`: Dual-level graph ingestion, query modes (hybrid/local/global), SCONES memory sync, Canvas export, and adapter integration (5 tests).
- `tests/rag/test_rag_router_and_tools.py`: FastAPI endpoints (/ingest-canvas, /query-dual-level, /scones-sync, /canvas-graph) and Hermes Swarm Tools (8 tests).
- `tests/rag/test_cross_workspace_marketing.py`: Cross-workspace retrieval, marketing copywriting frameworks (AIDA, PAS), artifact binding, Remotion props, and Canvas export validation (4 tests).
