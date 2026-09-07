# --- DNK-MRH-HEADER ---
# mrh_id: "core/rag/knowledge_graph.py"
# purpose: "Dual-level Multimodal Knowledge Graph for SCONES and LightRAG assimilation (Low-level entities + High-level themes)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (gerych_prime & dnk_scones_memory)"
# --- END DNK-MRH-HEADER ---

import re
import time
import math
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from core.rag.processors import ModalityType, MultimodalElement

logger = logging.getLogger("DNK.RAG.KnowledgeGraph")


class GraphNodeType(str):
    ENTITY = "entity"       # Low-level entity (concept, formula, table, image)
    THEME = "theme"         # High-level theme / topic abstraction
    CHUNK = "chunk"         # Raw document or multimodal chunk
    ARTIFACT = "artifact"   # Extracted sidecar asset


class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str = GraphNodeType.ENTITY
    modality: str = "text"
    content: str = ""
    level: str = "low"      # "low" (entities/chunks) or "high" (themes/domains)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    created_at: float = Field(default_factory=time.time)


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str           # e.g., "belongs_to_theme", "illustrates", "precedes", "references"
    weight: float = 1.0
    attributes: Dict[str, Any] = Field(default_factory=dict)


class DualLevelKnowledgeGraph:
    """
    Two-Level Multimodal Knowledge Graph assimilated from HKUDS/RAG-Anything & LightRAG:
    - Level 1 (Low-level): Specific entities, equations, visual cards, tables, chunks.
    - Level 2 (High-level): Abstract themes, document clusters, cross-cutting topics.
    - SCONES Engine Integration: Two-way synchronization with cognitive memory.
    """

    def __init__(self, workspace_id: str = "ws-alpha-001"):
        self.workspace_id = workspace_id
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._adjacency: Dict[str, Set[str]] = {}

    def add_node(self, node: GraphNode) -> GraphNode:
        self.nodes[node.id] = node
        if node.id not in self._adjacency:
            self._adjacency[node.id] = set()
        return node

    def add_edge(self, source: str, target: str, relation: str, weight: float = 1.0, **attributes) -> GraphEdge:
        if source not in self.nodes or target not in self.nodes:
            logger.debug("Skipping edge between missing nodes: %s -> %s", source, target)
        edge = GraphEdge(source=source, target=target, relation=relation, weight=weight, attributes=attributes)
        self.edges.append(edge)
        self._adjacency.setdefault(source, set()).add(target)
        self._adjacency.setdefault(target, set()).add(source)
        return edge

    def extract_low_level_entities(self, text: str) -> List[str]:
        """Extracts technical terms, symbols, acronyms, and capitalized entities."""
        candidates = set()
        # Acronyms (e.g. MLA, MoE, RAG, SCONES, BLEU)
        for m in re.finditer(r"\b[A-Z]{2,}(?:_[A-Z0-9]+)*\b", text):
            candidates.add(m.group(0))
        # Words with CamelCase e.g. LightRAG, SCONES, FastPath
        for m in re.finditer(r"\b[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+\b", text):
            candidates.add(m.group(0))
        # Technical keywords with dashes or dots e.g. dot-product, multi-head
        for m in re.finditer(r"\b[a-zA-Z]{2,}(?:-[a-zA-Z0-9]+)+\b", text):
            candidates.add(m.group(0))
        # Capitalized multi-word concepts (e.g. "Attention Mechanism", "Transformer Model")
        for m in re.finditer(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", text):
            candidates.add(m.group(0))
        # Key mathematical symbols (single uppercase like Q, K, V) if mentioned in math context
        for m in re.finditer(r"\b[QKVWXYZ]\b", text):
            candidates.add(f"Symbol_{m.group(0)}")
        return list(candidates)[:15]

    def extract_high_level_themes(self, elements: List[MultimodalElement], title: str = "") -> List[str]:
        """Clusters multimodal content into 1-4 high-level conceptual themes."""
        themes = set()
        if title:
            cleaned_title = re.sub(r"[#_\-\.\/\\]", " ", title).strip()
            if cleaned_title:
                themes.add(cleaned_title)

        all_text = " ".join([el.content for el in elements if el.type == ModalityType.TEXT])
        # Look for headers
        headers = re.findall(r"^#+\s+(.+)$", all_text, re.MULTILINE)
        for h in headers[:3]:
            theme = h.strip()
            if len(theme) > 3 and len(theme) < 60:
                themes.add(theme)

        # Fallback theme if none discovered
        if not themes:
            themes.add("General Knowledge Domain")

        return list(themes)

    def ingest_multimodal_elements(
        self,
        elements: List[MultimodalElement],
        doc_id: str,
        title: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Builds a dual-level graph from a stream of MultimodalElements.
        Creates Low-level nodes (chunks, entities, images, equations, tables)
        and High-level theme nodes, linking them with semantic edges.
        """
        doc_meta = metadata or {}
        # 1. High-level Themes (Level 2)
        discovered_themes = self.extract_high_level_themes(elements, title=title)
        theme_nodes = []
        for theme_title in discovered_themes:
            theme_id = f"theme_{abs(hash(theme_title)) % 100000}"
            theme_node = GraphNode(
                id=theme_id,
                label=theme_title,
                node_type=GraphNodeType.THEME,
                modality="text",
                content=f"High-level theme covering {theme_title}",
                level="high",
                attributes={"workspace_id": self.workspace_id, "doc_id": doc_id, **doc_meta},
            )
            self.add_node(theme_node)
            theme_nodes.append(theme_node)

        # Link themes together if multiple
        for i in range(len(theme_nodes) - 1):
            self.add_edge(
                theme_nodes[i].id,
                theme_nodes[i + 1].id,
                relation="related_theme",
                weight=1.5,
            )

        # 2. Low-level Entities & Elements (Level 1)
        prev_node_id: Optional[str] = None
        created_element_nodes = []

        for idx, el in enumerate(elements):
            element_node_id = f"node_{doc_id}_{idx}"
            node_label = f"[{el.type.upper()}] {el.caption or el.content[:30]}..."

            el_node = GraphNode(
                id=element_node_id,
                label=node_label,
                node_type=GraphNodeType.CHUNK if el.type == ModalityType.TEXT else GraphNodeType.ARTIFACT,
                modality=str(el.type),
                content=el.content,
                level="low",
                attributes={
                    "doc_id": doc_id,
                    "element_id": el.id,
                    "caption": el.caption,
                    "bounding_box": el.bounding_box,
                    "metadata": el.metadata,
                },
            )
            self.add_node(el_node)
            created_element_nodes.append(el_node)

            # Sequential flow edge
            if prev_node_id:
                self.add_edge(prev_node_id, element_node_id, relation="precedes", weight=1.0)
            prev_node_id = element_node_id

            # Cross-modal semantics: image/table illustrates preceding text
            if el.type in (ModalityType.IMAGE, ModalityType.TABLE, ModalityType.EQUATION) and idx > 0:
                self.add_edge(
                    element_node_id,
                    created_element_nodes[idx - 1].id,
                    relation="illustrates_or_expands",
                    weight=2.5,
                )

            # Link low-level node to parent themes (belongs_to_theme)
            for theme_node in theme_nodes:
                self.add_edge(
                    element_node_id,
                    theme_node.id,
                    relation="belongs_to_theme",
                    weight=1.2,
                )

            # 3. Extract sub-entities from text
            if el.type == ModalityType.TEXT:
                sub_entities = self.extract_low_level_entities(el.content)
                for ent_name in sub_entities:
                    ent_id = f"ent_{abs(hash(ent_name)) % 100000}"
                    if ent_id not in self.nodes:
                        ent_node = GraphNode(
                            id=ent_id,
                            label=ent_name,
                            node_type=GraphNodeType.ENTITY,
                            modality="text",
                            content=ent_name,
                            level="low",
                            attributes={"entity_text": ent_name, "doc_id": doc_id},
                        )
                        self.add_node(ent_node)
                    # Link chunk to entity
                    self.add_edge(element_node_id, ent_id, relation="references_entity", weight=1.8)

        return {
            "doc_id": doc_id,
            "themes": [t.label for t in theme_nodes],
            "nodes_created": len(created_element_nodes) + len(theme_nodes),
            "edges_created": len(self.edges),
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "high_level_nodes": len([n for n in self.nodes.values() if n.level == "high"]),
            "low_level_nodes": len([n for n in self.nodes.values() if n.level == "low"]),
        }

    def sync_to_scones(self, scones_engine: Any) -> Dict[str, Any]:
        """
        Synchronizes high-level themes and key cross-modal entities into SCONES long-term memory.
        """
        synced_count = 0
        for node in self.nodes.values():
            if node.node_type == GraphNodeType.THEME:
                # Store high-level thematic memory in SCONES
                try:
                    scones_engine.add_memory(
                        topic=f"Theme: {node.label}",
                        content=f"High-level theme in workspace {self.workspace_id}. Covers: {node.content}",
                        importance=0.9,
                        workspace_id=self.workspace_id,
                        metadata={
                            "node_id": node.id,
                            "level": node.level,
                            "modality": node.modality,
                            "tags": ["rag_knowledge_graph", "theme"],
                        },
                        tags=["rag_knowledge_graph", "theme"],
                    )
                    synced_count += 1
                except TypeError:
                    try:
                        scones_engine.add_memory(
                            topic=f"Theme: {node.label}",
                            content=f"High-level theme in workspace {self.workspace_id}. Covers: {node.content}",
                            importance=0.9,
                            metadata={
                                "node_id": node.id,
                                "level": node.level,
                                "modality": node.modality,
                                "tags": ["rag_knowledge_graph", "theme"],
                            },
                        )
                        synced_count += 1
                    except TypeError:
                        scones_engine.add_memory(
                            topic=f"Theme: {node.label}",
                            content=f"High-level theme in workspace {self.workspace_id}. Covers: {node.content}",
                            importance=0.9,
                        )
                        synced_count += 1
                except Exception as e:
                    logger.warning(f"Failed to sync theme {node.id} to SCONES: {e}")
            elif node.modality in ("image", "equation", "table"):
                # Store multimodal artifact index in SCONES
                try:
                    scones_engine.add_memory(
                        topic=f"Artifact: {node.label}",
                        content=f"Multimodal artifact ({node.modality}): {node.content[:200]}",
                        importance=0.7,
                        workspace_id=self.workspace_id,
                        metadata={
                            "node_id": node.id,
                            "level": node.level,
                            "modality": node.modality,
                            "tags": ["rag_knowledge_graph", "artifact"],
                        },
                        tags=["rag_knowledge_graph", "artifact"],
                    )
                    synced_count += 1
                except TypeError:
                    try:
                        scones_engine.add_memory(
                            topic=f"Artifact: {node.label}",
                            content=f"Multimodal artifact ({node.modality}): {node.content[:200]}",
                            importance=0.7,
                            metadata={
                                "node_id": node.id,
                                "level": node.level,
                                "modality": node.modality,
                                "tags": ["rag_knowledge_graph", "artifact"],
                            },
                        )
                        synced_count += 1
                    except TypeError:
                        scones_engine.add_memory(
                            topic=f"Artifact: {node.label}",
                            content=f"Multimodal artifact ({node.modality}): {node.content[:200]}",
                            importance=0.7,
                        )
                        synced_count += 1
                except Exception as e:
                    logger.warning(f"Failed to sync artifact {node.id} to SCONES: {e}")

        return {
            "status": "success",
            "synced_memories_count": synced_count,
            "workspace_id": self.workspace_id,
        }

    def query_dual_level(
        self,
        prompt: str,
        mode: str = "hybrid",  # "hybrid", "local", "global"
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Retrieves context using LightRAG-inspired dual-level search:
        - "global": Queries High-Level Theme nodes (synthesized architecture/overview).
        - "local": Queries Low-Level Entity/Chunk nodes (exact formulas, tables, figures).
        - "hybrid": Jointly queries High-Level Themes + 1-hop Low-Level neighbors.
        """
        p_lower = prompt.lower()
        scored_nodes: List[Tuple[float, GraphNode]] = []

        for node in self.nodes.values():
            # Filter by mode level
            if mode == "global" and node.level != "high":
                continue
            if mode == "local" and node.level != "low":
                continue

            # Compute term overlap score
            score = 0.0
            label_lower = node.label.lower()
            content_lower = node.content.lower()

            words = [w for w in p_lower.split() if len(w) > 2]
            for w in words:
                if w in label_lower:
                    score += 2.0
                if w in content_lower:
                    score += 1.0

            # Boost high-importance modalities if explicitly mentioned
            if ("image" in p_lower or "diagram" in p_lower or "рисунок" in p_lower) and node.modality == "image":
                score += 3.0
            if ("table" in p_lower or "таблиця" in p_lower) and node.modality == "table":
                score += 3.0
            if ("formula" in p_lower or "equation" in p_lower or "формула" in p_lower) and node.modality == "equation":
                score += 3.0

            if score > 0.0:
                scored_nodes.append((score, node))

        # Sort descending by relevance
        scored_nodes.sort(key=lambda x: x[0], reverse=True)
        top_nodes = [node for _, node in scored_nodes[:top_k]]

        # Expand neighbors for hybrid mode (1-hop expansion)
        expanded_neighbors: List[GraphNode] = []
        if mode == "hybrid":
            for n in top_nodes:
                neighbor_ids = self._adjacency.get(n.id, set())
                for nid in neighbor_ids:
                    if nid in self.nodes and self.nodes[nid] not in top_nodes and self.nodes[nid] not in expanded_neighbors:
                        expanded_neighbors.append(self.nodes[nid])

        return {
            "mode": mode,
            "query": prompt,
            "themes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "level": n.level,
                    "modality": n.modality,
                    "content": n.content,
                }
                for n in top_nodes if n.level == "high"
            ],
            "entities": [
                {
                    "id": n.id,
                    "label": n.label,
                    "level": n.level,
                    "modality": n.modality,
                    "content": n.content,
                }
                for n in top_nodes if n.level == "low"
            ],
            "primary_matches": [
                {
                    "id": n.id,
                    "label": n.label,
                    "level": n.level,
                    "modality": n.modality,
                    "content": n.content[:200],
                }
                for n in top_nodes
            ],
            "expanded_context": [
                {
                    "id": n.id,
                    "label": n.label,
                    "level": n.level,
                    "modality": n.modality,
                    "content": n.content[:200],
                }
                for n in expanded_neighbors[:top_k]
            ],
            "combined_context": "\n\n".join([n.content for n in (top_nodes + expanded_neighbors[:top_k])]),
            "total_retrieved": len(top_nodes) + len(expanded_neighbors[:top_k]),
        }

    def to_canvas_graph(self) -> Dict[str, Any]:
        """
        Exports graph state in DNK Canvas / Visual Shell compatible JSON format.
        """
        canvas_nodes = []
        col_high = 100
        col_low = 100

        for node in self.nodes.values():
            if node.level == "high":
                canvas_nodes.append({
                    "id": node.id,
                    "type": "DocNode",
                    "name": node.label,
                    "x": col_high,
                    "y": 100,
                    "position": {"x": col_high, "y": 100},
                    "data": {
                        "name": node.label,
                        "text": node.content,
                        "title": node.label,
                        "level": "high",
                        "modality": str(node.modality),
                    },
                    "metadata": {
                        "level": "high",
                        "modality": node.modality,
                        "content": node.content,
                    },
                })
                col_high += 250
            else:
                canvas_node_type = "DocNode"
                if node.modality == "image":
                    canvas_node_type = "ImageNode"
                elif node.modality == "table":
                    canvas_node_type = "TableNode"
                elif node.modality == "equation":
                    canvas_node_type = "EquationNode"

                canvas_nodes.append({
                    "id": node.id,
                    "type": canvas_node_type,
                    "name": node.label,
                    "x": col_low,
                    "y": 400,
                    "position": {"x": col_low, "y": 400},
                    "data": {
                        "name": node.label,
                        "text": node.content,
                        "title": node.label,
                        "level": "low",
                        "modality": str(node.modality),
                        **node.attributes,
                    },
                    "metadata": {
                        "level": "low",
                        "modality": node.modality,
                        "content": node.content,
                        **node.attributes,
                    },
                })
                col_low += 250

        canvas_edges = [
            {
                "id": f"edge_{e.source}_{e.target}",
                "source": e.source,
                "target": e.target,
                "relation": e.relation,
                "label": e.relation,
                "weight": e.weight,
                "data": {
                    "relation": e.relation,
                    "weight": e.weight,
                    **e.attributes,
                },
                "metadata": e.attributes,
            }
            for e in self.edges
        ]

        return {
            "workspace_id": self.workspace_id,
            "nodes": canvas_nodes,
            "edges": canvas_edges,
            "node_count": len(canvas_nodes),
            "edge_count": len(canvas_edges),
            "metadata": {
                "total_nodes": len(canvas_nodes),
                "total_edges": len(canvas_edges),
                "workspace_id": self.workspace_id,
            },
        }
