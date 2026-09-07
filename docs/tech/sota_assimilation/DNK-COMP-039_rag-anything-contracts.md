# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-COMP-039_rag-anything-contracts.md"
# purpose: "Component & API Contracts: Pydantic schemas, Port definitions, and endpoints for Multimodal RAG."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 📋 DNK-COMP-039: Multimodal RAG Contracts & Data Specifications

## 1. Domain Types & Enums (`core.rag.processors`)

### `ModalityType`
```python
class ModalityType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    TABLE = "table"
    EQUATION = "equation"
```

### `MultimodalElement`
```python
class MultimodalElement(BaseModel):
    id: str = Field(default_factory=lambda: f"elem_{uuid.uuid4().hex[:8]}")
    type: ModalityType
    content: str
    caption: Optional[str] = None
    bounding_box: Optional[Dict[str, float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

## 2. Hexagonal Port Contract (`core.adapters.dnk_rag_anything_adapter`)

```python
class MultimodalRAGPort(ABC):
    @abstractmethod
    def ingest_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Parses document, decomposes modalities, and indexes knowledge graph. Returns doc_id."""
        pass

    @abstractmethod
    def query(self, prompt: str, mode: str = "hybrid") -> RAGQueryResult:
        """Executes text or hybrid graph-vector query."""
        pass

    @abstractmethod
    def query_multimodal(
        self,
        prompt: str,
        elements: List[MultimodalElement],
        mode: str = "hybrid"
    ) -> RAGQueryResult:
        """Executes query with direct VLM visual element injection."""
        pass

    @abstractmethod
    def get_document_graph(self, doc_id: str) -> Dict[str, Any]:
        """Retrieves nodes and edges for visualization in Canvas / Visual Shell."""
        pass
```

## 3. REST API Specifications (`apps/api/routers/rag.py`)

- `POST /api/v1/rag/ingest`: Ingest document by relative path.
- `POST /api/v1/rag/ingest-text`: Ingest raw markdown or formula snippet.
- `POST /api/v1/rag/query`: Hybrid search across knowledge graph.
- `POST /api/v1/rag/query-multimodal`: Direct VLM query with visual elements.
- `GET /api/v1/rag/graph/{doc_id}`: Topology graph export for Visual Shell / Canvas.
