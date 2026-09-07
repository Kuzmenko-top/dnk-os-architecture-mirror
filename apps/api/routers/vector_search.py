# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/vector_search.py"
# purpose: "FastAPI REST Router for PostgreSQL Hybrid Vector Search, Ingestion, Reranking and Collection Analytics"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-VECTOR-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field

from apps.api.db.vector_store import VectorStore
from apps.api.services.postgres_hybrid_search_engine import PostgresHybridSearchEngine
from apps.api.services.cross_encoder_reranker import CrossEncoderReranker

logger = logging.getLogger("VectorSearchRouter")

router = APIRouter(prefix="/api/v1/vector", tags=["Vector Search"])

# Shared singleton instances
vector_store = VectorStore()
hybrid_engine = PostgresHybridSearchEngine(vector_store=vector_store)
reranker_service = CrossEncoderReranker()


# --- Pydantic Request/Response Models ---

class VectorPointIngestRequest(BaseModel):
    id: Optional[str] = None
    tenant_id: str = Field(default="default_tenant")
    workspace_id: str = Field(default="default_workspace")
    memory_type: str = Field(default="document")
    content: str
    content_tokens: Optional[int] = None
    embedding_dense: Optional[List[float]] = None
    metadata: Optional[Dict[str, Any]] = None
    embedding_model: Optional[str] = "text-embedding-3-large"


class BatchVectorIngestRequest(BaseModel):
    points: List[VectorPointIngestRequest]


class HybridSearchRequest(BaseModel):
    query: str
    dense_vector: Optional[List[float]] = None
    tenant_id: str = Field(default="default_tenant")
    workspace_id: str = Field(default="default_workspace")
    top_k: int = Field(default=10, ge=1, le=100)
    rrf_k: int = Field(default=60, ge=1)
    dense_weight: float = Field(default=1.0, ge=0.0)
    sparse_weight: float = Field(default=1.0, ge=0.0)
    rerank: bool = False
    rerank_top_k: int = Field(default=5, ge=1, le=50)
    memory_type: Optional[str] = None
    filter_metadata: Optional[Dict[str, Any]] = None


class RerankRequest(BaseModel):
    query: str
    documents: List[Dict[str, Any]]
    top_k: int = Field(default=5, ge=1, le=50)
    model_name: Optional[str] = "ms-marco-MiniLM-L-6-v2"


# --- REST Endpoints ---

@router.post("/ingest")
async def ingest_vector(request: VectorPointIngestRequest) -> Dict[str, Any]:
    """Ingest a single document vector into the PostgreSQL hybrid store."""
    try:
        point_id = vector_store.ingest_vector(request.model_dump())
        return {
            "status": "success",
            "id": point_id,
            "message": "Vector successfully ingested into pgvector/tsvector store",
        }
    except Exception as exc:
        logger.error(f"Vector ingestion error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/ingest/batch")
async def ingest_batch_vectors(request: BatchVectorIngestRequest) -> Dict[str, Any]:
    """Batch ingestion of multiple vectors with atomic commit."""
    try:
        points_data = [pt.model_dump() for pt in request.points]
        inserted_ids = vector_store.ingest_batch(points_data)
        return {
            "status": "success",
            "count": len(inserted_ids),
            "ids": inserted_ids,
        }
    except Exception as exc:
        logger.error(f"Batch ingestion error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{id}")
async def delete_vector(
    id: str = Path(..., description="Vector UUID to delete"),
    tenant_id: str = Query(default="default_tenant"),
    workspace_id: str = Query(default="default_workspace"),
) -> Dict[str, Any]:
    """Delete a vector record ensuring tenant and workspace isolation."""
    success = vector_store.delete_vector(vector_id=id, tenant_id=tenant_id, workspace_id=workspace_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vector not found or unauthorized")
    return {"status": "success", "id": id, "deleted": True}


@router.post("/hybrid-search")
async def hybrid_search(request: HybridSearchRequest) -> Dict[str, Any]:
    """Execute hybrid search combining Dense pgvector and Sparse tsvector via RRF and optional reranking."""
    try:
        results = hybrid_engine.search(
            query_text=request.query,
            query_dense_vector=request.dense_vector,
            tenant_id=request.tenant_id,
            workspace_id=request.workspace_id,
            top_k=request.top_k,
            rrf_k=request.rrf_k,
            dense_weight=request.dense_weight,
            sparse_weight=request.sparse_weight,
            rerank=request.rerank,
            rerank_top_k=request.rerank_top_k,
            memory_type=request.memory_type,
            filter_metadata=request.filter_metadata,
        )
        return results
    except Exception as exc:
        logger.error(f"Hybrid search error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/search/dense")
async def search_dense(
    tenant_id: str = Query(default="default_tenant"),
    workspace_id: str = Query(default="default_workspace"),
    top_k: int = Query(default=10, ge=1, le=100),
    memory_type: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """Perform pure dense search (vector similarity)."""
    # Dummy mock vector if not passed via body for pure GET testing
    dummy_vec = [0.1] * 1536
    results = hybrid_engine.dense_search.search(
        query_vector=dummy_vec,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        top_k=top_k,
        memory_type=memory_type,
    )
    return {"results": results, "count": len(results)}


@router.get("/search/sparse")
async def search_sparse(
    q: str = Query(..., description="Query text"),
    tenant_id: str = Query(default="default_tenant"),
    workspace_id: str = Query(default="default_workspace"),
    top_k: int = Query(default=10, ge=1, le=100),
    memory_type: Optional[str] = Query(default=None),
) -> Dict[str, Any]:
    """Perform pure sparse lexical search (tsvector/BM25)."""
    results = hybrid_engine.sparse_search.search(
        query_text=q,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        top_k=top_k,
        memory_type=memory_type,
    )
    return {"results": results, "count": len(results)}


@router.post("/rerank")
async def rerank_documents(request: RerankRequest) -> Dict[str, Any]:
    """Rerank given documents using Cross-Encoder model."""
    try:
        reranked = reranker_service.rerank(
            query=request.query,
            documents=request.documents,
            top_k=request.top_k,
            model_name=request.model_name,
        )
        return {"query": request.query, "results": reranked, "count": len(reranked)}
    except Exception as exc:
        logger.error(f"Reranking error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/collections")
async def list_collections(
    workspace_id: str = Query(default="default_workspace"),
) -> Dict[str, Any]:
    """List collection categories within a workspace."""
    collections = vector_store.list_collections(workspace_id=workspace_id)
    return {"workspace_id": workspace_id, "collections": collections}


@router.get("/collections/{id}/stats")
async def get_collection_stats(
    id: str = Path(..., description="Workspace ID"),
) -> Dict[str, Any]:
    """Get statistics for a specific collection / workspace."""
    stats = vector_store.get_stats(workspace_id=id)
    return stats


@router.get("/health")
async def vector_health() -> Dict[str, Any]:
    """Vector search service health status."""
    return {
        "status": "healthy",
        "engine": "PostgreSQL (pgvector + tsvector)",
        "dense_dimension": 1536,
        "fusion": "Reciprocal Rank Fusion (RRF)",
        "reranker": "Cross-Encoder",
    }


@router.get("/stats")
async def global_vector_stats() -> Dict[str, Any]:
    """Global system stats across all workspaces."""
    return {
        "status": "online",
        "supported_models": ["text-embedding-3-large", "text-embedding-3-small", "bge-large-en-v1.5"],
        "pgvector_enabled": True,
        "tsvector_enabled": True,
    }
