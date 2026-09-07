# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/tools/dnk_rag_tool.py"
# purpose: "Native Hermes tool bridging Swarm Agents with HKUDS RAG-Anything Multimodal & Dual-Level Knowledge Graph."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm (Gerych Prime)"
# --- END DNK-MRH-HEADER ---

import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("DNKRAGTool")

HUB_ROOT = Path(__file__).resolve().parent.parent.parent
if str(HUB_ROOT) not in sys.path:
    sys.path.insert(0, str(HUB_ROOT))

_GLOBAL_ADAPTER = None


def _get_adapter():
    global _GLOBAL_ADAPTER
    if _GLOBAL_ADAPTER is None:
        try:
            from core.adapters.dnk_rag_anything_adapter import DNKRAGAnythingAdapter, RAGConfig
            cfg = RAGConfig(
                spendguard_budget_usd=25.0,
                enable_vlm_direct_injection=True,
                workspace_id="ws-alpha-001"
            )
            _GLOBAL_ADAPTER = DNKRAGAnythingAdapter(config=cfg)
        except Exception as e:
            logger.error(f"Failed to instantiate DNKRAGAnythingAdapter: {e}")
            _GLOBAL_ADAPTER = None
    return _GLOBAL_ADAPTER


def dnk_rag_query(
    query: str = "",
    mode: str = "hybrid",
    top_k: int = 5,
    workspace_id: str = "ws-alpha-001",
    workspace_ids: Optional[List[str]] = None,
    **kwargs: Any
) -> str:
    """
    Executes a high-precision multimodal or dual-level LightRAG query across the DNK Knowledge Graph.
    Supports cross-workspace retrieval when multiple workspace_ids are specified.

    Args:
        query: Search question, architecture query, or technical prompt.
        mode: Search mode: 'hybrid' (combines macro themes and detailed entities), 'local' (micro-entities), or 'global' (macro-themes).
        top_k: Maximum number of primary and neighbor results to retrieve (default: 5).
        workspace_id: Single workspace isolation identifier.
        workspace_ids: Optional list of workspace identifiers for cross-workspace retrieval.

    Returns:
        JSON string containing the retrieved context, themes, entities, and citations.
    """
    effective_query = (
        query
        or kwargs.get("prompt")
        or kwargs.get("search")
        or kwargs.get("text")
        or ""
    ).strip()

    if not effective_query:
        return json.dumps({
            "status": "error",
            "message": "Empty query provided to dnk_rag_query."
        })

    adapter = _get_adapter()
    if adapter is None:
        return json.dumps({
            "status": "error",
            "message": "DNKRAGAnythingAdapter could not be initialized."
        })

    try:
        norm_mode = mode.lower() if mode else "hybrid"
        if norm_mode not in ("hybrid", "local", "global"):
            norm_mode = "hybrid"

        effective_ws_ids = workspace_ids or kwargs.get("workspaces")
        result = adapter.query_dual_level(
            prompt=effective_query,
            mode=norm_mode,
            top_k=top_k,
            workspace_id=workspace_id,
            workspace_ids=effective_ws_ids,
        )
        return json.dumps({
            "status": "success",
            "workspace_id": workspace_id,
            "workspace_ids": result.get("workspace_ids", [workspace_id]),
            "query": effective_query,
            "mode": norm_mode,
            "thematic_context": result.get("thematic_context", []) or result.get("themes", []),
            "primary_matches": result.get("primary_matches", []),
            "expanded_neighbors": result.get("expanded_neighbors", []),
            "combined_context": result.get("combined_context", "") or result.get("synthesized_context", ""),
            "execution_time_ms": result.get("execution_time_ms", 1.0)
        }, indent=2)
    except Exception as e:
        logger.error(f"Error executing dnk_rag_query: {e}")
        return json.dumps({
            "status": "error",
            "query": effective_query,
            "message": str(e)
        })


def dnk_rag_ingest(
    content_or_path: str,
    title: Optional[str] = None,
    modality: str = "auto",
    workspace_id: str = "ws-alpha-001",
    **kwargs: Any
) -> str:
    """
    Ingests documents, markdown text, or Canvas graphs into the DNK Multimodal RAG system.

    Args:
        content_or_path: File path (relative or absolute) or raw text snippet / JSON Canvas payload.
        title: Descriptive title or label for the ingested document.
        modality: Modality hint ('auto', 'text', 'canvas', 'document').
        workspace_id: Workspace isolation identifier.

    Returns:
        JSON string containing doc_id, element counts, and ingestion status.
    """
    adapter = _get_adapter()
    if adapter is None:
        return json.dumps({
            "status": "error",
            "message": "DNKRAGAnythingAdapter could not be initialized."
        })

    try:
        # Check if content_or_path is an existing local file
        possible_path = Path(content_or_path)
        if not possible_path.is_absolute():
            possible_path = HUB_ROOT / possible_path

        if possible_path.exists() and possible_path.is_file():
            doc_id = adapter.ingest_document(
                file_path=str(content_or_path),
                metadata={"title": title or possible_path.name, "workspace_id": workspace_id},
                workspace_id=workspace_id,
            )
            doc_info = adapter.get_document_graph(doc_id)
            return json.dumps({
                "status": "success",
                "doc_id": doc_id,
                "type": "document",
                "file_path": str(content_or_path),
                "total_nodes": doc_info.get("total_nodes", 0),
                "total_edges": doc_info.get("total_edges", 0),
                "workspace_id": workspace_id
            }, indent=2)

        # Check if JSON canvas representation
        if content_or_path.strip().startswith("{") and '"nodes"' in content_or_path:
            try:
                canvas_data = json.loads(content_or_path)
                doc_id = adapter.ingest_canvas(
                    canvas_data=canvas_data,
                    canvas_id=title or "swarm_canvas",
                    metadata={"workspace_id": workspace_id},
                    workspace_id=workspace_id,
                )
                return json.dumps({
                    "status": "success",
                    "doc_id": doc_id,
                    "type": "canvas",
                    "title": title or "swarm_canvas",
                    "workspace_id": workspace_id
                }, indent=2)
            except json.JSONDecodeError:
                pass

        # Ingest as raw text / markdown
        doc_id = adapter.ingest_text(
            text=content_or_path,
            title=title or "snippet",
            metadata={"workspace_id": workspace_id},
            workspace_id=workspace_id,
        )
        doc_info = adapter.get_document_graph(doc_id)
        return json.dumps({
            "status": "success",
            "doc_id": doc_id,
            "type": "text",
            "title": title or "snippet",
            "total_nodes": doc_info.get("total_nodes", 0),
            "total_edges": doc_info.get("total_edges", 0),
            "workspace_id": workspace_id
        }, indent=2)
    except Exception as e:
        logger.error(f"Error executing dnk_rag_ingest: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


def dnk_rag_sync_scones(
    workspace_id: str = "ws-alpha-001",
    **kwargs: Any
) -> str:
    """
    Synchronizes current dual-level knowledge graph into SCONES long-term cognitive memory.

    Args:
        workspace_id: Target workspace identifier.

    Returns:
        JSON string with count of synced nodes and status.
    """
    adapter = _get_adapter()
    if adapter is None:
        return json.dumps({
            "status": "error",
            "message": "DNKRAGAnythingAdapter could not be initialized."
        })

    try:
        res = adapter.sync_scones(workspace_id=workspace_id)
        return json.dumps({
            "status": res.get("status", "success"),
            "synced_nodes": res.get("synced_nodes", 0),
            "workspace_id": workspace_id,
            "message": f"Successfully synced {res.get('synced_nodes', 0)} nodes to SCONES"
        }, indent=2)
    except Exception as e:
        logger.error(f"Error syncing to SCONES: {e}")
        return json.dumps({
            "status": "error",
            "workspace_id": workspace_id,
            "message": str(e)
        })


def dnk_generate_marketing_banner(
    product_name: str,
    marketing_goal: str,
    target_audience: Optional[str] = None,
    framework: str = "AIDA",
    workspace_ids: Optional[List[str]] = None,
    format_type: str = "square_1_1",
    **kwargs: Any
) -> str:
    """
    Autonomous Swarm Marketing Pipeline Tool:
    Synthesizes a 100% grounded, publication-ready marketing banner (HTML5, SVG, Remotion, Canvas)
    by querying global marketing psychology frameworks + project-specific technical specs and extracted photos.

    Args:
        product_name: Name of the product or brand (e.g. 'ReBurn Pro Smoker').
        marketing_goal: Objective of the banner (e.g. 'Facebook campaign highlighting water seal and clean smoke').
        target_audience: Optional target persona.
        framework: Marketing framework ('AIDA', 'PAS', 'BAB').
        workspace_ids: List of knowledge base workspaces (e.g. ['global-marketing', 'ws-reburn-001']).
        format_type: Layout aspect ratio ('square_1_1', 'story_9_16', 'landscape_16_9').

    Returns:
        JSON string with complete grounded banner specification, verified assets, SVG, HTML5, and Canvas node.
    """
    adapter = _get_adapter()
    if adapter is None:
        return json.dumps({
            "status": "error",
            "message": "DNKRAGAnythingAdapter could not be initialized."
        })

    try:
        from core.rag.marketing_banner import GroundedMarketingBannerSynthesizer
        effective_ws_ids = workspace_ids or kwargs.get("workspaces") or ["global-marketing", "ws-alpha-001"]
        synthesizer = GroundedMarketingBannerSynthesizer(rag_adapter=adapter)
        result = synthesizer.synthesize(
            product_name=product_name,
            marketing_goal=marketing_goal,
            target_audience=target_audience,
            framework=framework,
            format_type=format_type,
            workspace_ids=effective_ws_ids,
        )
        return json.dumps({
            "status": "success",
            "product_name": result.product_name,
            "framework": result.framework,
            "headline": result.headline,
            "subheadline": result.subheadline,
            "bullet_points": result.bullet_points,
            "call_to_action": result.call_to_action,
            "psychological_angle": result.psychological_angle,
            "product_facts_grounded": result.product_facts_grounded,
            "referenced_assets": result.referenced_assets,
            "svg_markup": result.svg_markup,
            "html_markup": result.html_markup,
            "remotion_props": result.remotion_props,
            "canvas_node": result.canvas_node,
            "workspaces_consulted": result.workspaces_consulted,
        }, indent=2)
    except Exception as e:
        logger.error(f"Error generating marketing banner: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })
