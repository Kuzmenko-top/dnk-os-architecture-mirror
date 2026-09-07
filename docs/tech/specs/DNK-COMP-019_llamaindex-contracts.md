# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-COMP-019_llamaindex-contracts.md"
# purpose: "Component Interfaces and Abstract Contracts for LlamaIndex Framework Assimilation"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-16"
# --- END DNK-MRH-HEADER ---

# 🧩 COMPONENT CONTRACTS: LLAMAINDEX INTERFACES (DNK-COMP-019)

Abstract Python contracts (`abc.ABC`) defining type-safe interface boundaries for LlamaIndex indexing, node parsing, retrieval, and query engine components.

---

## 📐 Base Data Structures & Contracts

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Sequence, Union

class Document:
    """Canonical Document container ingested by data connectors."""
    def __init__(
        self,
        text: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        extra_info: Optional[Dict[str, Any]] = None
    ) -> None:
        self.text = text
        self.doc_id = doc_id
        self.metadata = metadata or {}
        self.extra_info = extra_info or {}


class BaseNode(ABC):
    """Atomic Node unit produced by NodeParsers."""
    node_id: str
    text: str
    metadata: Dict[str, Any]
    parent_node_id: Optional[str]
    child_node_ids: List[str]


class QueryBundle:
    """Encapsulates query string, embedding vector, and search parameters."""
    def __init__(
        self,
        query_str: str,
        custom_embedding_strs: Optional[List[str]] = None,
        embedding: Optional[List[float]] = None
    ) -> None:
        self.query_str = query_str
        self.custom_embedding_strs = custom_embedding_strs
        self.embedding = embedding


class NodeWithScore:
    """Wrapper binding a BaseNode with a retrieval similarity score."""
    def __init__(self, node: BaseNode, score: float) -> None:
        self.node = node
        self.score = score


class Response:
    """Synthesized response payload returned by BaseQueryEngine."""
    def __init__(
        self,
        response: str,
        source_nodes: List[NodeWithScore],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.response = response
        self.source_nodes = source_nodes
        self.metadata = metadata or {}
```

---

## 🛠️ Abstract Component Interfaces

```python
class BaseReader(ABC):
    """Abstract Data Connector contract."""

    @abstractmethod
    def load_data(self, *args: Any, **kwargs: Any) -> List[Document]:
        """Loads raw data sources into a list of Document instances."""
        ...


class BaseNodeParser(ABC):
    """Abstract Document-to-Nodes Chunking contract."""

    @abstractmethod
    def get_nodes_from_documents(
        self,
        documents: Sequence[Document],
        show_progress: bool = False
    ) -> List[BaseNode]:
        """Parses a sequence of Document objects into atomic BaseNode chunks."""
        ...


class BaseRetriever(ABC):
    """Abstract Retrieval contract."""

    @abstractmethod
    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        """Internal retrieval implementation returning ranked NodeWithScore items."""
        ...

    def retrieve(self, str_or_query_bundle: Union[str, QueryBundle]) -> List[NodeWithScore]:
        """Public retrieval interface accepting raw query string or QueryBundle."""
        if isinstance(str_or_query_bundle, str):
            query_bundle = QueryBundle(query_str=str_or_query_bundle)
        else:
            query_bundle = str_or_query_bundle
        return self._retrieve(query_bundle)


class BasePostprocessor(ABC):
    """Abstract Post-Processor and Re-Ranker contract."""

    @abstractmethod
    def postprocess_nodes(
        self,
        nodes: List[NodeWithScore],
        query_bundle: Optional[QueryBundle] = None
    ) -> List[NodeWithScore]:
        """Filters or reranks NodeWithScore items prior to LLM synthesis."""
        ...


class BaseQueryEngine(ABC):
    """Abstract End-to-End Query Execution contract."""

    @abstractmethod
    def _query(self, query_bundle: QueryBundle) -> Response:
        """Internal query execution logic returning synthesized Response."""
        ...

    def query(self, str_or_query_bundle: Union[str, QueryBundle]) -> Response:
        """Public query interface."""
        if isinstance(str_or_query_bundle, str):
            query_bundle = QueryBundle(query_str=str_or_query_bundle)
        else:
            query_bundle = str_or_query_bundle
        return self._query(query_bundle)


class BaseIndex(ABC):
    """Abstract Index Storage and Construction contract."""

    @abstractmethod
    def as_retriever(self, **kwargs: Any) -> BaseRetriever:
        """Constructs a BaseRetriever instance backed by this Index."""
        ...

    @abstractmethod
    def as_query_engine(self, **kwargs: Any) -> BaseQueryEngine:
        """Constructs a BaseQueryEngine instance backed by this Index."""
        ...
```
