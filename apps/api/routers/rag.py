# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/rag.py"
# purpose: "FastAPI Router for Multimodal RAG & Knowledge Graph Engine (HKUDS/RAG-Anything)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (dnk_dev_fullstack & Gerych Prime)"
# --- END DNK-MRH-HEADER ---

import logging
import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends

from apps.api.schemas.rag import (
    IngestDocumentRequest,
    IngestTextRequest,
    IngestResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    MultimodalQueryRequest,
    DocumentGraphResponse,
    IngestCanvasRequest,
    DualLevelQueryRequest,
    DualLevelQueryResponse,
    SCONESSyncRequest,
    SCONESSyncResponse,
    CanvasGraphResponse,
    MarketingBannerRequest,
    MarketingBannerResponse,
)
from core.adapters.dnk_rag_anything_adapter import (
    DNKRAGAnythingAdapter,
    RAGConfig,
)
from core.rag.marketing_banner import GroundedMarketingBannerSynthesizer
from core.rag.processors import MultimodalElement, ModalityType

logger = logging.getLogger("apps.api.routers.rag")

router = APIRouter(prefix="/api/v1/rag", tags=["Multimodal RAG"])

# Shared singleton adapter instance
_rag_adapter = DNKRAGAnythingAdapter(config=RAGConfig())


def get_rag_adapter() -> DNKRAGAnythingAdapter:
    return _rag_adapter


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_document(req: IngestDocumentRequest) -> IngestResponse:
    """
    Ingests and parses a document (Markdown, text, notes) into the multimodal knowledge graph.
    """
    adapter = get_rag_adapter()
    try:
        doc_id = adapter.ingest_document(
            file_path=req.file_path,
            metadata=req.metadata,
            workspace_id=req.workspace_id,
        )
        return IngestResponse(
            doc_id=doc_id,
            status="success",
            message=f"Document '{req.file_path}' successfully decomposed and indexed."
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to ingest document {req.file_path}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/ingest-text", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_text(req: IngestTextRequest) -> IngestResponse:
    """
    Directly ingests a raw snippet or multiline markdown content into knowledge graph.
    """
    adapter = get_rag_adapter()
    try:
        doc_id = adapter.ingest_text(
            text=req.text,
            title=req.title,
            metadata=req.metadata,
            workspace_id=req.workspace_id,
        )
        return IngestResponse(
            doc_id=doc_id,
            status="success",
            message=f"Snippet '{req.title}' successfully decomposed and indexed."
        )
    except Exception as e:
        logger.error(f"Failed to ingest text snippet {req.title}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/query", response_model=RAGQueryResponse)
def query_rag(req: RAGQueryRequest) -> RAGQueryResponse:
    """
    Executes hybrid text + graph retrieval over indexed multimodal documents.
    """
    adapter = get_rag_adapter()
    try:
        res = adapter.query(prompt=req.query, mode=req.mode)
        return RAGQueryResponse(
            query=res.query,
            answer=res.answer,
            referenced_nodes=res.referenced_nodes,
            visual_evidence_urls=res.visual_evidence_urls,
            confidence_score=res.confidence_score,
            execution_time_ms=res.execution_time_ms,
            mode=res.mode
        )
    except Exception as e:
        logger.error(f"Query retrieval error for '{req.query}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/query-multimodal", response_model=RAGQueryResponse)
def query_multimodal_rag(req: MultimodalQueryRequest) -> RAGQueryResponse:
    """
    Executes multimodal query with direct visual/table element injection.
    """
    adapter = get_rag_adapter()
    try:
        domain_elements: List[MultimodalElement] = []
        for el in req.elements:
            try:
                modality = ModalityType(el.type.lower())
            except ValueError:
                modality = ModalityType.TEXT

            domain_elements.append(
                MultimodalElement(
                    type=modality,
                    content=el.content,
                    caption=el.caption,
                    bounding_box=el.bounding_box,
                    metadata=el.metadata or {}
                )
            )

        res = adapter.query_multimodal(
            prompt=req.query,
            elements=domain_elements,
            mode=req.mode
        )
        return RAGQueryResponse(
            query=res.query,
            answer=res.answer,
            referenced_nodes=res.referenced_nodes,
            visual_evidence_urls=res.visual_evidence_urls,
            confidence_score=res.confidence_score,
            execution_time_ms=res.execution_time_ms,
            mode=res.mode
        )
    except RuntimeError as e:
        # SpendGuard or budget threshold
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except Exception as e:
        logger.error(f"Multimodal query retrieval error for '{req.query}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/graph/{doc_id}", response_model=DocumentGraphResponse)
def get_graph(doc_id: str) -> DocumentGraphResponse:
    """
    Retrieves topology of nodes and edges for Visual Shell Canvas visualization.
    """
    adapter = get_rag_adapter()
    try:
        graph = adapter.get_document_graph(doc_id)
        return DocumentGraphResponse(
            doc_id=graph["doc_id"],
            file_path=graph["file_path"],
            nodes=graph["nodes"],
            edges=graph["edges"],
            total_nodes=graph["total_nodes"],
            total_edges=graph["total_edges"]
        )
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to fetch graph for {doc_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/ingest-canvas", response_model=IngestResponse, status_code=status.HTTP_201_CREATED)
def ingest_canvas_context(
    req: IngestCanvasRequest,
    adapter: DNKRAGAnythingAdapter = Depends(get_rag_adapter)
) -> IngestResponse:
    """
    Ingests visual nodes and relations directly from DNK Visual Shell Canvas.
    """
    try:
        canvas_payload = {
            "nodes": req.nodes,
            "edges": req.edges or []
        }
        doc_id = adapter.ingest_canvas(
            canvas_data=canvas_payload,
            canvas_id=req.title or "canvas",
            metadata=req.metadata or {},
            workspace_id=req.workspace_id,
        )
        return IngestResponse(
            doc_id=doc_id,
            status="success",
            message=f"Canvas context ingested successfully with {len(req.nodes)} nodes"
        )
    except Exception as e:
        logger.error(f"Failed to ingest canvas context: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/query-dual-level", response_model=DualLevelQueryResponse)
def query_dual_level(
    req: DualLevelQueryRequest,
    adapter: DNKRAGAnythingAdapter = Depends(get_rag_adapter)
) -> DualLevelQueryResponse:
    """
    Executes LightRAG dual-level query (hybrid, local, or global) across thematic and entity graphs.
    Supports cross-workspace retrieval across multiple knowledge bases.
    """
    try:
        mode = req.mode.lower()
        if mode not in ("hybrid", "local", "global"):
            mode = "hybrid"

        result = adapter.query_dual_level(
            prompt=req.query,
            mode=mode,
            top_k=req.top_k,
            workspace_id=req.workspace_id,
            workspace_ids=req.workspace_ids,
        )
        return DualLevelQueryResponse(
            query=result.get("query", req.query),
            mode=result.get("mode", mode),
            themes=result.get("thematic_context", []) or result.get("themes", []),
            primary_matches=result.get("primary_matches", []),
            expanded_context=result.get("expanded_neighbors", []),
            combined_context=result.get("combined_context", "") or result.get("synthesized_context", ""),
            execution_time_ms=result.get("execution_time_ms", 1.0),
            workspace_ids=result.get("workspace_ids", req.workspace_ids or ([req.workspace_id] if req.workspace_id else [])),
        )
    except Exception as e:
        logger.error(f"Dual-level query error for '{req.query}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/scones-sync", response_model=SCONESSyncResponse)
def sync_scones_memory(
    req: SCONESSyncRequest,
    adapter: DNKRAGAnythingAdapter = Depends(get_rag_adapter)
) -> SCONESSyncResponse:
    """
    Synchronizes high-level themes, formulas, and artifacts into SCONES cognitive memory.
    """
    try:
        ws_id = req.workspace_id or "ws-alpha-001"
        res = adapter.sync_scones(workspace_id=ws_id)
        return SCONESSyncResponse(
            status=res.get("status", "success"),
            synced_nodes=res.get("synced_nodes", 0),
            workspace_id=ws_id,
            message=f"Successfully synced {res.get('synced_nodes', 0)} nodes to SCONES memory"
        )
    except Exception as e:
        logger.error(f"SCONES sync error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/canvas-graph", response_model=CanvasGraphResponse)
def get_canvas_graph(
    workspace_id: Optional[str] = None,
    adapter: DNKRAGAnythingAdapter = Depends(get_rag_adapter)
) -> CanvasGraphResponse:
    """
    Exports the entire dual-level knowledge graph formatted for Visual Shell Canvas React Flow rendering.
    """
    try:
        target_ws = workspace_id or adapter.config.workspace_id
        canvas_data = adapter.export_canvas_graph(workspace_id=target_ws)
        nodes = canvas_data.get("nodes", [])
        edges = canvas_data.get("edges", [])
        return CanvasGraphResponse(
            workspace_id=target_ws,
            nodes=nodes,
            edges=edges,
            node_count=len(nodes),
            edge_count=len(edges),
            metadata=canvas_data.get("metadata", {})
        )
    except Exception as e:
        logger.error(f"Canvas graph export error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/marketing-banner", response_model=MarketingBannerResponse)
def generate_marketing_banner(
    req: MarketingBannerRequest,
    adapter: DNKRAGAnythingAdapter = Depends(get_rag_adapter),
) -> MarketingBannerResponse:
    """
    Synthesizes a 100% grounded, publication-ready marketing banner
    by retrieving patterns across marketing and project-specific knowledge bases.
    """
    start_time = time.time()
    try:
        synthesizer = GroundedMarketingBannerSynthesizer(rag_adapter=adapter)
        result = synthesizer.synthesize(
            product_name=req.product_name,
            marketing_goal=req.marketing_goal,
            target_audience=req.target_audience or "",
            framework=req.framework or "AIDA",
            workspace_ids=req.workspace_ids,
            format_type=req.format or "square_1_1",
        )
        exec_time = (time.time() - start_time) * 1000
        return MarketingBannerResponse(
            status="success",
            product_name=result.product_name,
            framework=result.framework,
            headline=result.headline,
            subheadline=result.subheadline,
            bullet_points=result.bullet_points,
            call_to_action=result.call_to_action,
            psychological_angle=result.psychological_angle,
            product_facts_grounded=result.product_facts_grounded,
            referenced_assets=result.referenced_assets,
            svg_markup=result.svg_markup,
            html_markup=result.html_markup,
            remotion_props=result.remotion_props,
            canvas_node=result.canvas_node,
            workspaces_consulted=result.workspaces_consulted,
            execution_time_ms=exec_time,
        )
    except Exception as e:
        logger.error(f"Failed to synthesize marketing banner: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

