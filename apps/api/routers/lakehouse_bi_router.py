# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/lakehouse_bi_router.py"
# purpose: "FastAPI Router for Embedded DuckDB Lakehouse Analytics, AI Analyst NL2SQL & Swarm DAG Execution."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-SWARM-BI-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Antigravity (Mentor) & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from core.adapters.dnk_agentswarms_adapter import (
    DNKAgentSwarmsAdapter,
    SwarmNodeType,
    SwarmWorkflowNode,
    SwarmWorkflowEdge,
    SwarmWorkflowDAG,
    SemanticMetricSpec,
    LakehouseQueryResponse
)
from core.lakehouse.duckdb_engine import get_lakehouse_engine, DuckDBLakehouseEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v3/lakehouse", tags=["Lakehouse BI & AI Analyst"])

# Shared singleton adapter instance & DuckDB Lakehouse Engine
_agentswarms_adapter = DNKAgentSwarmsAdapter()
_lakehouse_engine: DuckDBLakehouseEngine = get_lakehouse_engine()


# --- Request / Response Models ---

class SQLQueryRequest(BaseModel):
    sql_query: str = Field(..., description="Raw SQL query to execute against DuckDB/SQLite Lakehouse")
    use_cache: bool = Field(True, description="Enable Parquet query caching for SELECT queries")
    cache_ttl_seconds: int = Field(300, description="Cache TTL in seconds")


class NL2SQLAnalysisRequest(BaseModel):
    question: str = Field(..., description="Natural language analytical question")


class CreateWorkflowRequest(BaseModel):
    title: str = Field(..., description="Workflow title")
    nodes: List[SwarmWorkflowNode] = Field(default_factory=list)
    edges: List[SwarmWorkflowEdge] = Field(default_factory=list)


class ExecuteWorkflowRequest(BaseModel):
    workflow_id: str
    inputs: Dict[str, Any] = Field(default_factory=dict)


# --- Endpoints ---

@router.post("/query", response_model=LakehouseQueryResponse, status_code=status.HTTP_200_OK)
async def execute_lakehouse_query(request: SQLQueryRequest):
    """
    Executes a direct analytical SQL query against the embedded Lakehouse via async ThreadPool and Parquet cache.
    """
    try:
        result = await _lakehouse_engine.query_async(
            request.sql_query,
            use_cache=request.use_cache,
            cache_ttl_seconds=request.cache_ttl_seconds
        )
        return LakehouseQueryResponse(
            columns=result.columns,
            rows=result.rows,
            execution_time_ms=result.execution_time_ms,
            row_count=result.row_count,
            engine=result.engine,
            cached=result.cached,
            cache_path=result.cache_path
        )
    except Exception as e:
        logger.error(f"Lakehouse query failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"SQL Query failed: {str(e)}"
        )


@router.post("/nl2sql", status_code=status.HTTP_200_OK)
async def analyze_natural_language_query(request: NL2SQLAnalysisRequest):
    """
    Translates a natural language question into SQL, executes it asynchronously, and formats the reasoning trace.
    """
    try:
        result = await _lakehouse_engine.analyze_nl2sql_async(request.question, use_cache=True)
        return result
    except Exception as e:
        logger.error(f"NL2SQL analysis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Analyst reasoning failed: {str(e)}"
        )


@router.post("/cache/clear", status_code=status.HTTP_200_OK)
async def clear_lakehouse_cache():
    """
    Purges all cached Parquet files in the lakehouse cache directory.
    """
    try:
        deleted_count = _lakehouse_engine.clear_cache()
        return {
            "status": "success",
            "message": f"Lakehouse Parquet cache cleared: {deleted_count} files removed",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error(f"Cache clear failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cache clear failed: {str(e)}"
        )


@router.get("/metrics", status_code=status.HTTP_200_OK)
async def list_semantic_metrics():
    """
    Returns the catalog of registered semantic metrics and dimension formulas.
    """
    metrics = [
        spec.model_dump()
        for spec in _agentswarms_adapter._semantic_catalog.values()
    ]
    return {
        "status": "success",
        "metrics_count": len(metrics),
        "metrics": metrics
    }


@router.post("/workflows", status_code=status.HTTP_201_CREATED)
async def create_swarm_workflow(request: CreateWorkflowRequest):
    """
    Creates and registers a new 6-node Swarm Workflow DAG.
    """
    try:
        dag = _agentswarms_adapter.create_workflow(
            title=request.title,
            nodes=request.nodes,
            edges=request.edges
        )
        return dag.model_dump()
    except Exception as e:
        logger.error(f"Workflow creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create workflow: {str(e)}"
        )


@router.post("/workflows/execute", status_code=status.HTTP_200_OK)
async def execute_swarm_workflow(request: ExecuteWorkflowRequest):
    """
    Executes a registered Swarm Workflow DAG through asynchronous topological traversal.
    """
    try:
        result = await _agentswarms_adapter.execute_workflow(
            workflow_id=request.workflow_id,
            inputs=request.inputs
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(e)}"
        )
