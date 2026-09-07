# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/distiller.py"
# purpose: "FastAPI Router for Error Distillation & Closed-Loop Self-Healing System (Query, Record, Heal, Stats)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym & Antigravity"
# --- END DNK-MRH-HEADER ---

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from apps.api.services.self_healing_distiller import (
    SelfHealingDistiller,
    DistillationResult,
    ErrorSnapshot
)
from core.hermes_agent.tools.dnk_distiller_tool import (
    dnk_query_error_solutions,
    dnk_record_error_solution,
    _load_knowledge_base
)

logger = logging.getLogger("DistillerRouter")

router = APIRouter(prefix="/api/v1/distiller", tags=["Error Distillation & Self-Healing"])

_distiller = SelfHealingDistiller(max_retry=3)


class DistillationQueryRequest(BaseModel):
    error_text: str = Field(..., description="Error message, stack trace, or log")
    workspace_id: str = Field(default="ws-alpha-001", description="Target workspace ID")


class DistillationRecordRequest(BaseModel):
    error_text: str = Field(..., description="Error text or pattern")
    solution_text: str = Field(..., description="Resolution or workaround")
    root_cause: str = Field(..., description="Identified root cause")
    category: Optional[str] = Field(default="DYNAMIC_AGENT_DISTILLED", description="Error category taxonomy")
    workspace_id: str = Field(default="ws-alpha-001", description="Target workspace ID")


class SelfHealingRequest(BaseModel):
    error_message: str = Field(..., description="Error message or exception description")
    stack_trace: Optional[str] = Field(default="", description="Stack trace or logs")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Contextual execution metadata")
    auto_package_skill: bool = Field(default=True, description="Whether to package validated fix as SKILL.md")


@router.post("/query")
async def query_distilled_solution(req: DistillationQueryRequest):
    """
    Query the Error Distillation database to find known remedies, root causes, and recommended fixes.
    """
    try:
        raw_res = dnk_query_error_solutions(error_text=req.error_text, workspace_id=req.workspace_id)
        return json.loads(raw_res)
    except Exception as e:
        logger.error(f"Error querying distillation: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/record")
async def record_distilled_solution(req: DistillationRecordRequest):
    """
    Store an analyzed error fix into long-term SCONES memory and the distillation store.
    """
    try:
        raw_res = dnk_record_error_solution(
            error_text=req.error_text,
            solution_text=req.solution_text,
            root_cause=req.root_cause,
            workspace_id=req.workspace_id
        )
        return json.loads(raw_res)
    except Exception as e:
        logger.error(f"Error recording distillation: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/heal")
async def execute_self_healing(req: SelfHealingRequest):
    """
    Execute closed-loop self-healing: knowledge lookup, synthesis proposal, validation, and optional auto-skill packaging.
    """
    try:
        combined_error = f"{req.error_message}\n{req.stack_trace}".strip()
        result = await _distiller.handle_error(
            error=combined_error,
            context=req.context,
            auto_package_skill=req.auto_package_skill
        )
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error executing self-healing: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats")
async def get_distillation_stats():
    """
    Retrieve statistics on known distillation patterns, categories, and self-healing metrics.
    """
    try:
        kb = _load_knowledge_base()
        categories = {}
        for item in kb:
            cat = item.get("category", "UNKNOWN")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "status": "active",
            "total_distillations": len(kb),
            "categories": categories,
            "cache_size": len(_distiller._in_memory_cache),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Error getting distillation stats: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
