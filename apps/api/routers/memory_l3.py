# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/memory_l3.py"
# purpose: "FastAPI REST Router for SCONES L3 Long-Term Memory (Retrieval, Manual Ingestion, Consolidation trigger & Metrics)"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-SCONES-L3-001", "DNK-SCONES-L3-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import math
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.scones_l3_memory import SCONESL3Memory

try:
    from core.memory.pgvector_store import PgVectorStore as PGVectorStore
except ImportError:
    try:
        from core.memory.pgvector_store import PgVectorStore as PGVectorStore
    except ImportError:
        PGVectorStore = None

router = APIRouter(prefix="/api/v1/memory/l3", tags=["SCONES L3 Memory"])

_pgvector = PGVectorStore() if PGVectorStore else None
scones_l3 = SCONESL3Memory(_pgvector)


class MemoryStoreRequest(BaseModel):
    user_id: str
    workspace_id: str
    agent_id: str = "system"
    memory_type: str = "semantic"
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    retention_policy: str = "forever"


class MemoryConsolidateRequest(BaseModel):
    user_id: str
    workspace_id: str
    older_than_days: int = 7


@router.post("/store")
async def store_memory(req: MemoryStoreRequest):
    """
    Store an explicit long-term memory into SCONES L3.
    """
    mem_id = await scones_l3.store_memory(
        user_id=req.user_id,
        workspace_id=req.workspace_id,
        agent_id=req.agent_id,
        memory_type=req.memory_type,
        content=req.content,
        metadata=req.metadata,
        retention_policy=req.retention_policy,
    )
    return {"status": "success", "memory_id": mem_id}


@router.get("/memories")
async def list_memories(
    user_id: str = Query(..., description="Target user ID"),
    workspace_id: str = Query(..., description="Target workspace ID"),
    query: str = Query("", description="Optional search query for hybrid retrieval"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    List or search long-term memories for a user/workspace using hybrid search + temporal decay.
    """
    memories = await scones_l3.retrieve_memories(
        user_id=user_id,
        workspace_id=workspace_id,
        query=query,
        top_k=limit,
    )
    return {"memories": memories, "count": len(memories)}


@router.post("/consolidate")
async def trigger_consolidation(req: MemoryConsolidateRequest):
    """
    Trigger Agentic Sleep Consolidation (L2 -> L3 distillation).
    """
    distilled = await scones_l3.consolidate_memories(
        user_id=req.user_id,
        workspace_id=req.workspace_id,
        older_than_days=req.older_than_days,
    )
    await scones_l3.apply_temporal_decay()
    return {
        "status": "success",
        "distilled_facts_count": len(distilled),
        "distilled_records": distilled,
    }


@router.get("/stats")
async def get_memory_stats(
    user_id: str = Query(..., description="Target user ID"),
    workspace_id: str = Query(..., description="Target workspace ID"),
):
    """
    Aggregate statistics for SCONES L3 memory tier.
    """
    if _pgvector and hasattr(_pgvector, "pool") and _pgvector.pool:
        try:
            async with _pgvector.pool.acquire() as conn:
                stats = await conn.fetchrow(
                    """
                    SELECT
                      COUNT(*)::int as total,
                      COUNT(DISTINCT memory_type)::int as types,
                      COALESCE(AVG(recency_score), 1.0)::float as avg_recency
                    FROM scones_longterm_memories
                    WHERE user_id = $1 AND workspace_id = $2
                    """,
                    user_id,
                    workspace_id,
                )
                if stats:
                    return dict(stats)
        except Exception:
            pass

    # In-memory stats fallback
    matching = [
        m for m in scones_l3._in_memory_l3_store.values()
        if str(m.get("user_id")) == str(user_id) and str(m.get("workspace_id")) == str(workspace_id)
    ]
    total = len(matching)
    types_count = len(set(m.get("memory_type", "semantic") for m in matching))
    avg_rec = sum(m.get("recency_score", 1.0) for m in matching) / max(total, 1)

    return {
        "total": total,
        "types": types_count,
        "avg_recency": avg_rec,
    }
