# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/dnk_rag_anything_adapter.py"
# purpose: "Hexagonal Port and Adapter for HKUDS/RAG-Anything multimodal knowledge graph RAG"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import time
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from core.rag.processors import (
    ModalityType,
    MultimodalElement,
    DocumentDecomposer,
)
from core.rag.pipeline import (
    MultimodalExtractionPipeline,
)
from core.rag.knowledge_graph import (
    DualLevelKnowledgeGraph,
)

logger = logging.getLogger("dnk.adapters.rag_anything")


class RAGConfig(BaseModel):
    storage_dir: str = Field(default="./data/rag_storage", description="Root directory for indexed artifacts")
    cache_dir: str = Field(default=".extracted_assets", description="Sidecar visual assets cache directory")
    workspace_id: str = Field(default="ws-alpha-001", description="Target DNK workspace identifier")
    max_file_size_mb: int = Field(default=25, description="Maximum allowed file size for document ingestion")
    spendguard_budget_usd: float = Field(default=5.0, description="Session VLM SpendGuard token budget cap")
    enable_vlm_direct_injection: bool = Field(default=True, description="Inject visual elements directly to VLM")
    hybrid_top_k: int = Field(default=5, description="Top-k nodes to retrieve in hybrid search")


class RAGQueryResult(BaseModel):
    """Structured response from Multimodal RAG retrieval."""
    query: str
    answer: str
    referenced_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    visual_evidence_urls: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=1.0)
    execution_time_ms: float = Field(default=0.0)
    mode: str = Field(default="hybrid")


class MultimodalRAGPort(ABC):
    """Hexagonal Port defining Multimodal Knowledge Graph RAG contracts."""

    @abstractmethod
    def ingest_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> str:
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
    def ingest_text(
        self,
        text: str,
        title: str = "raw_snippet",
        metadata: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> str:
        """Parses raw text / markdown into multimodal graph entities."""
        pass

    @abstractmethod
    def ingest_canvas(
        self,
        canvas_data: Any,
        canvas_id: str = "canvas",
        metadata: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> str:
        """Ingests visual context and nodes directly from Canvas graph."""
        pass

    def sync_scones(
        self,
        scones_engine: Optional[Any] = None,
        workspace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronizes high-level themes and artifacts from knowledge graph to SCONES."""
        return {}

    def query_dual_level(
        self,
        prompt: str,
        mode: str = "hybrid",
        top_k: int = 5,
        workspace_id: Optional[str] = None,
        workspace_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Dual-level query across themes (high) and entities/artifacts (low). Supports cross-workspace search."""
        return {}

    def export_canvas_graph(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Exports complete dual-level knowledge graph for Canvas visualization."""
        return {}


class DNKRAGAnythingAdapter(MultimodalRAGPort):
    """
    DNK OS Adapter integrating HKUDS/RAG-Anything patterns.
    Implements multi-stage document decomposition, cross-modal graph indexing,
    and hybrid retrieval with direct VLM visual injection.
    """

    def __init__(self, config: Optional[RAGConfig] = None):
        self.config = config or RAGConfig()
        self.decomposer = DocumentDecomposer()
        self.pipeline = MultimodalExtractionPipeline(cache_dir=self.config.cache_dir)
        self.knowledge_graph = DualLevelKnowledgeGraph(workspace_id=self.config.workspace_id)
        self._workspace_graphs: Dict[str, DualLevelKnowledgeGraph] = {
            self.config.workspace_id: self.knowledge_graph
        }
        # In-memory graph storage: doc_id -> {"elements": [...], "edges": [...], "metadata": {...}}
        self._documents: Dict[str, Dict[str, Any]] = {}
        self._cumulative_spend_usd: float = 0.0

    def get_knowledge_graph(self, workspace_id: Optional[str] = None) -> DualLevelKnowledgeGraph:
        """Retrieves or instantiates a DualLevelKnowledgeGraph for the target workspace."""
        ws_id = workspace_id or self.config.workspace_id
        if ws_id not in self._workspace_graphs:
            self._workspace_graphs[ws_id] = DualLevelKnowledgeGraph(workspace_id=ws_id)
        return self._workspace_graphs[ws_id]

    def _sanitize_path(self, file_path: str) -> str:
        """Guards against path traversal security attacks."""
        normalized = os.path.normpath(file_path)
        if normalized.startswith("..") or "/../" in normalized:
            raise ValueError(f"Security Alert: Path traversal detected in file path: {file_path}")
        return normalized

    def ingest_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> str:
        start_time = time.time()
        safe_path = self._sanitize_path(file_path)

        if not os.path.exists(safe_path):
            raise FileNotFoundError(f"Document not found: {safe_path}")

        file_size_mb = os.path.getsize(safe_path) / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise ValueError(
                f"File size {file_size_mb:.2f}MB exceeds configured limit of {self.config.max_file_size_mb}MB"
            )

        doc_id = f"doc_{int(time.time())}_{abs(hash(safe_path)) % 10000}"
        elements, sidecar_meta_path = self.pipeline.extract(safe_path, metadata=metadata)

        # Build cross-modal graph edges
        edges = []
        for i, el in enumerate(elements):
            if i > 0:
                # Sequential context edge
                edges.append({
                    "source": elements[i - 1].id,
                    "target": el.id,
                    "relation": "precedes",
                    "weight": 1.0
                })
            if el.type in (ModalityType.IMAGE, ModalityType.TABLE, ModalityType.EQUATION):
                # Bind multimodal element to previous text element if available
                if i > 0 and elements[i - 1].type == ModalityType.TEXT:
                    edges.append({
                        "source": el.id,
                        "target": elements[i - 1].id,
                        "relation": "illustrates_or_expands",
                        "weight": 2.0
                    })

        self._documents[doc_id] = {
            "doc_id": doc_id,
            "file_path": safe_path,
            "elements": elements,
            "edges": edges,
            "sidecar_manifest": sidecar_meta_path,
            "metadata": metadata or {},
            "ingested_at": time.time(),
            "duration_ms": (time.time() - start_time) * 1000,
            "workspace_id": workspace_id or self.config.workspace_id,
        }

        # Dual-level knowledge graph ingestion for target workspace
        target_kg = self.get_knowledge_graph(workspace_id)
        target_kg.ingest_multimodal_elements(
            elements=elements,
            doc_id=doc_id,
            title=os.path.basename(safe_path),
            metadata=metadata
        )

        logger.info(
            f"Successfully ingested {safe_path}: {len(elements)} elements, {len(edges)} graph edges"
        )
        return doc_id

    def ingest_canvas(
        self,
        canvas_data: Any,
        canvas_id: str = "canvas",
        metadata: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> str:
        """Directly ingests visual context and nodes from Canvas graph."""
        start_time = time.time()
        doc_id = f"canvas_{int(time.time())}_{abs(hash(canvas_id)) % 10000}"
        elements, sidecar_meta_path = self.pipeline.extract(
            canvas_data if isinstance(canvas_data, str) else json.dumps(canvas_data),
            file_type="canvas",
            metadata=metadata,
        )

        edges = []
        for i, el in enumerate(elements):
            if i > 0:
                edges.append({
                    "source": elements[i - 1].id,
                    "target": el.id,
                    "relation": "precedes",
                    "weight": 1.0
                })
            if el.type in (ModalityType.IMAGE, ModalityType.TABLE, ModalityType.EQUATION):
                if i > 0 and elements[i - 1].type == ModalityType.TEXT:
                    edges.append({
                        "source": el.id,
                        "target": elements[i - 1].id,
                        "relation": "illustrates_or_expands",
                        "weight": 2.0
                    })

        self._documents[doc_id] = {
            "doc_id": doc_id,
            "file_path": f"canvas://{canvas_id}",
            "elements": elements,
            "edges": edges,
            "sidecar_manifest": sidecar_meta_path,
            "metadata": metadata or {},
            "ingested_at": time.time(),
            "duration_ms": (time.time() - start_time) * 1000,
            "workspace_id": workspace_id or self.config.workspace_id,
        }

        # Dual-level knowledge graph ingestion
        target_kg = self.get_knowledge_graph(workspace_id)
        target_kg.ingest_multimodal_elements(
            elements=elements,
            doc_id=doc_id,
            title=canvas_id,
            metadata=metadata
        )
        return doc_id

    def ingest_text(
        self,
        text: str,
        title: str = "raw_snippet",
        metadata: Optional[Dict[str, Any]] = None,
        workspace_id: Optional[str] = None,
    ) -> str:
        """Direct text / snippet ingestion without disk file requirement."""
        start_time = time.time()
        doc_id = f"snippet_{int(time.time())}_{abs(hash(title)) % 10000}"
        elements = self.decomposer.decompose_markdown(text, source_doc=title)

        edges = []
        for i, el in enumerate(elements):
            if i > 0:
                edges.append({
                    "source": elements[i - 1].id,
                    "target": el.id,
                    "relation": "precedes",
                    "weight": 1.0
                })
                if el.type != ModalityType.TEXT and elements[i - 1].type == ModalityType.TEXT:
                    edges.append({
                        "source": el.id,
                        "target": elements[i - 1].id,
                        "relation": "illustrates_or_expands",
                        "weight": 2.0
                    })

        self._documents[doc_id] = {
            "doc_id": doc_id,
            "file_path": title,
            "elements": elements,
            "edges": edges,
            "metadata": metadata or {},
            "ingested_at": time.time(),
            "duration_ms": (time.time() - start_time) * 1000,
            "workspace_id": workspace_id or self.config.workspace_id,
        }

        # Dual-level knowledge graph ingestion
        target_kg = self.get_knowledge_graph(workspace_id)
        target_kg.ingest_multimodal_elements(
            elements=elements,
            doc_id=doc_id,
            title=title,
            metadata=metadata
        )
        return doc_id

    def query(self, prompt: str, mode: str = "hybrid") -> RAGQueryResult:
        start_time = time.time()
        tokens = set(prompt.lower().split())

        matched_elements: List[MultimodalElement] = []
        visual_urls: List[str] = []

        for doc in self._documents.values():
            for el in doc["elements"]:
                # Content match or caption match
                searchable = (el.content + " " + (el.caption or "")).lower()
                overlap = len(tokens.intersection(searchable.split()))
                if overlap > 0 or not tokens:
                    matched_elements.append(el)
                    if el.type == ModalityType.IMAGE:
                        visual_urls.append(el.content)

        # Sort by relevance heuristics
        matched_elements.sort(
            key=lambda e: len(tokens.intersection((e.content + " " + (e.caption or "")).lower().split())),
            reverse=True
        )
        top_elements = matched_elements[: self.config.hybrid_top_k]

        nodes_summary = [
            {
                "id": el.id,
                "type": el.type.value,
                "caption": el.caption,
                "content_preview": el.content[:120]
            }
            for el in top_elements
        ]

        if top_elements:
            synthesized_context = "\n\n".join(
                [f"[{el.type.value.upper()}: {el.caption or 'element'}]\n{el.content}" for el in top_elements]
            )
            answer = f"Retrieved {len(top_elements)} multimodal nodes relevant to '{prompt}':\n\n{synthesized_context}"
            confidence = min(1.0, 0.5 + (len(top_elements) * 0.1))
        else:
            answer = f"No relevant multimodal knowledge graph nodes found for query: '{prompt}'."
            confidence = 0.0

        return RAGQueryResult(
            query=prompt,
            answer=answer,
            referenced_nodes=nodes_summary,
            visual_evidence_urls=visual_urls,
            confidence_score=confidence,
            execution_time_ms=(time.time() - start_time) * 1000,
            mode=mode
        )

    def query_multimodal(
        self,
        prompt: str,
        elements: List[MultimodalElement],
        mode: str = "hybrid"
    ) -> RAGQueryResult:
        start_time = time.time()

        # SpendGuard cost calculation
        vlm_cost = len([e for e in elements if e.type == ModalityType.IMAGE]) * 0.002
        if (self._cumulative_spend_usd + vlm_cost) > self.config.spendguard_budget_usd:
            raise RuntimeError(
                f"SpendGuard Error: Query would exceed budget limit (${self.config.spendguard_budget_usd:.2f})"
            )
        self._cumulative_spend_usd += vlm_cost

        # Base text retrieval
        base_res = self.query(prompt, mode=mode)

        # Inject multimodal elements into evidence
        injected_visuals = [e.content for e in elements if e.type == ModalityType.IMAGE]
        combined_visuals = list(set(base_res.visual_evidence_urls + injected_visuals))

        synthesized_multimodal_answer = (
            f"[VLM Multimodal Query Mode: {mode.upper()}]\n"
            f"Prompt: {prompt}\n"
            f"Injected Elements: {len(elements)} items "
            f"({len(injected_visuals)} images, {len([e for e in elements if e.type == ModalityType.TABLE])} tables)\n\n"
            f"Synthesized Response: {base_res.answer}"
        )

        return RAGQueryResult(
            query=prompt,
            answer=synthesized_multimodal_answer,
            referenced_nodes=base_res.referenced_nodes,
            visual_evidence_urls=combined_visuals,
            confidence_score=min(1.0, base_res.confidence_score + 0.15),
            execution_time_ms=(time.time() - start_time) * 1000,
            mode=f"{mode}_multimodal_vlm"
        )

    def get_document_graph(self, doc_id: str) -> Dict[str, Any]:
        if doc_id not in self._documents:
            raise KeyError(f"Document ID not found in knowledge graph: {doc_id}")

        doc = self._documents[doc_id]
        nodes = [
            {
                "id": el.id,
                "label": el.caption or f"{el.type.value}:{el.id[:6]}",
                "type": el.type.value,
                "content": el.content,
                "metadata": el.metadata,
                "bounding_box": el.bounding_box
            }
            for el in doc["elements"]
        ]

        return {
            "doc_id": doc_id,
            "file_path": doc["file_path"],
            "nodes": nodes,
            "edges": doc["edges"],
            "total_nodes": len(nodes),
            "total_edges": len(doc["edges"])
        }

    def sync_scones(
        self,
        scones_engine: Optional[Any] = None,
        workspace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synchronizes high-level themes and artifacts from knowledge graph to SCONES."""
        if scones_engine is None:
            try:
                from core.scones_memory import SCONESMemoryEngine
                scones_engine = SCONESMemoryEngine(enable_pgvector=False)
            except Exception as e:
                logger.warning(f"Could not initialize SCONESMemoryEngine fallback: {e}")
                return {"status": "error", "synced_nodes": 0, "message": str(e)}
        target_kg = self.get_knowledge_graph(workspace_id)
        return target_kg.sync_to_scones(scones_engine)

    def query_dual_level(
        self,
        prompt: str,
        mode: str = "hybrid",
        top_k: int = 5,
        workspace_id: Optional[str] = None,
        workspace_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Dual-level query across themes (high) and entities/artifacts (low). Supports cross-workspace multi-base retrieval."""
        target_ws_ids = workspace_ids or ([workspace_id] if workspace_id else [self.config.workspace_id])
        if not target_ws_ids:
            target_ws_ids = [self.config.workspace_id]

        if len(target_ws_ids) == 1:
            target_kg = self.get_knowledge_graph(target_ws_ids[0])
            res = target_kg.query_dual_level(prompt=prompt, mode=mode, top_k=top_k)
            res["workspace_ids"] = target_ws_ids
            return res

        # Cross-workspace aggregation
        aggregated_themes: List[Dict[str, Any]] = []
        aggregated_entities: List[Dict[str, Any]] = []
        aggregated_primary: List[Dict[str, Any]] = []
        aggregated_expanded: List[Dict[str, Any]] = []
        seen_node_ids = set()

        for ws in target_ws_ids:
            target_kg = self.get_knowledge_graph(ws)
            sub_res = target_kg.query_dual_level(prompt=prompt, mode=mode, top_k=top_k)
            for theme in sub_res.get("themes", []):
                t_id = f"{ws}:{theme.get('id')}"
                if t_id not in seen_node_ids:
                    seen_node_ids.add(t_id)
                    item = dict(theme)
                    item["workspace_id"] = ws
                    aggregated_themes.append(item)
            for entity in sub_res.get("entities", []):
                e_id = f"{ws}:{entity.get('id')}"
                if e_id not in seen_node_ids:
                    seen_node_ids.add(e_id)
                    item = dict(entity)
                    item["workspace_id"] = ws
                    aggregated_entities.append(item)
            for pm in sub_res.get("primary_matches", []):
                pm_id = f"{ws}:{pm.get('id')}"
                if pm_id not in seen_node_ids:
                    seen_node_ids.add(pm_id)
                    item = dict(pm)
                    item["workspace_id"] = ws
                    aggregated_primary.append(item)
            for exp in sub_res.get("expanded_neighbors", []):
                exp_id = f"{ws}:{exp.get('id')}"
                if exp_id not in seen_node_ids:
                    seen_node_ids.add(exp_id)
                    item = dict(exp)
                    item["workspace_id"] = ws
                    aggregated_expanded.append(item)

        aggregated_themes = aggregated_themes[:top_k]
        aggregated_entities = aggregated_entities[:top_k]
        aggregated_primary = aggregated_primary[:top_k]

        context_lines = [f"=== Cross-Workspace Retrieval Query: '{prompt}' (Mode: {mode}) ==="]
        context_lines.append(f"Workspaces Queried: {', '.join(target_ws_ids)}\n")
        if aggregated_themes:
            context_lines.append("--- High-Level Thematic Context ---")
            for t in aggregated_themes:
                context_lines.append(f"• [{t.get('workspace_id', '')}] {t.get('label', '')}: {t.get('content', '')}")
            context_lines.append("")
        if aggregated_entities:
            context_lines.append("--- Low-Level Entity & Artifact Details ---")
            for e in aggregated_entities:
                context_lines.append(f"• [{e.get('workspace_id', '')}] {e.get('label', '')} ({e.get('modality', '')}): {e.get('content', '')}")
            context_lines.append("")
        if aggregated_expanded:
            context_lines.append("--- Cross-Modal 1-Hop Connected Neighbors ---")
            for n in aggregated_expanded[:top_k]:
                context_lines.append(f"• [{n.get('workspace_id', '')}] {n.get('label', '')} ({n.get('modality', '')}): {n.get('content', '')}")

        return {
            "mode": mode,
            "query": prompt,
            "workspace_ids": target_ws_ids,
            "themes": aggregated_themes,
            "entities": aggregated_entities,
            "primary_matches": aggregated_primary,
            "expanded_neighbors": aggregated_expanded,
            "combined_context": "\n".join(context_lines),
            "synthesized_context": "\n".join(context_lines),
            "total_retrieved": len(aggregated_primary) + len(aggregated_expanded[:top_k]),
        }

    def export_canvas_graph(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """Exports complete dual-level knowledge graph for Canvas visualization."""
        target_kg = self.get_knowledge_graph(workspace_id)
        return target_kg.to_canvas_graph()
