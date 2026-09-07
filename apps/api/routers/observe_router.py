# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/observe_router.py"
# purpose: "FastAPI REST Router for Distributed Tracing, OTLP Ingestion & Topology Analytics (DNK-OBSERVE-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from apps.api.services.telemetry_collector_service import (
    TelemetryCollectorService,
    get_default_collector,
)
from apps.api.db.models.trace_span import TraceSpan
from apps.api.db.models.trace_service import TraceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/observe", tags=["Distributed Tracing & Observability"])


# ---------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------

class SpanIngestItem(BaseModel):
    name: str = Field(..., description="Span operation name")
    service_name: str = Field(..., description="Service name")
    trace_id: Optional[str] = Field(None, description="Trace ID (32-hex)")
    span_id: Optional[str] = Field(None, description="Span ID (16-hex)")
    parent_span_id: Optional[str] = Field(None, description="Parent Span ID")
    kind: str = Field("INTERNAL", description="Span kind: INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER")
    status_code: str = Field("OK", description="Status code: UNSET, OK, ERROR")
    status_message: Optional[str] = Field(None, description="Status error message")
    duration_ms: float = Field(0.0, description="Duration in milliseconds")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Span attributes")
    events: List[Dict[str, Any]] = Field(default_factory=list, description="Span events")
    links: List[Dict[str, Any]] = Field(default_factory=list, description="Span links")
    workspace_id: str = Field("ws-alpha-001", description="Workspace ID")


class BatchSpanIngestRequest(BaseModel):
    spans: Optional[List[SpanIngestItem]] = Field(None, description="List of spans to ingest")
    resourceSpans: Optional[List[Dict[str, Any]]] = Field(None, description="Standard OTLP resourceSpans format")


class ServiceRegisterRequest(BaseModel):
    service_name: str = Field(..., description="Unique service name")
    service_version: str = Field("1.0.0", description="Semantic version")
    environment: str = Field("production", description="Runtime environment")
    runtime: str = Field("python-fastapi", description="Service runtime / framework")
    status: str = Field("HEALTHY", description="Service health status: HEALTHY, DEGRADED, UNHEALTHY")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Service metadata")
    workspace_id: str = Field("ws-alpha-001", description="Workspace ID")


# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@router.post("/spans/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_spans(payload: Dict[str, Any]):
    """
    Ingests OpenTelemetry spans. Supports:
    1. Direct list of spans: {"spans": [...]}
    2. Native OTLP payload: {"resourceSpans": [...]}
    3. Single span dict.
    """
    collector = get_default_collector()
    try:
        # Check if standard OTLP JSON
        if "resourceSpans" in payload:
            count = collector.ingest_otlp_json(payload)
            ingested_count = count.get("ingested_count", 0) if isinstance(count, dict) else count
            return {
                "status": "success",
                "format": "otlp_json",
                "ingested_spans_count": ingested_count,
            }

        # Check if batch format
        if "spans" in payload and isinstance(payload["spans"], list):
            spans_list = payload["spans"]
            span_models = []
            for item in spans_list:
                span_obj = TraceSpan(
                    name=item.get("name", "unnamed_span"),
                    service_name=item.get("service_name", "unknown_service"),
                    trace_id=item.get("trace_id"),
                    span_id=item.get("span_id"),
                    parent_span_id=item.get("parent_span_id"),
                    kind=item.get("kind", "INTERNAL"),
                    status_code=item.get("status_code", "OK"),
                    status_message=item.get("status_message"),
                    duration_ms=float(item.get("duration_ms", 0.0)),
                    attributes=item.get("attributes", {}),
                    events=item.get("events", []),
                    links=item.get("links", []),
                    workspace_id=item.get("workspace_id", "ws-alpha-001"),
                )
                span_models.append(span_obj)

            count = collector.ingest_spans(span_models)
            ingested_count = count.get("ingested_count", 0) if isinstance(count, dict) else count
            return {
                "status": "success",
                "format": "batch_spans",
                "ingested_spans_count": ingested_count,
            }

        # Single span format
        span_obj = TraceSpan(
            name=payload.get("name", "unnamed_span"),
            service_name=payload.get("service_name", "unknown_service"),
            trace_id=payload.get("trace_id"),
            span_id=payload.get("span_id"),
            parent_span_id=payload.get("parent_span_id"),
            kind=payload.get("kind", "INTERNAL"),
            status_code=payload.get("status_code", "OK"),
            status_message=payload.get("status_message"),
            duration_ms=float(payload.get("duration_ms", 0.0)),
            attributes=payload.get("attributes", {}),
            events=payload.get("events", []),
            links=payload.get("links", []),
            workspace_id=payload.get("workspace_id", "ws-alpha-001"),
        )
        collector.ingest_span(span_obj)
        return {
            "status": "success",
            "format": "single_span",
            "ingested_spans_count": 1,
        }

    except Exception as e:
        logger.exception("Failed to ingest spans into telemetry collector: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to ingest spans: {str(e)}",
        )


@router.get("/traces")
async def list_traces(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    status_code: Optional[str] = Query(None, description="Filter by status code (OK, ERROR)"),
    min_duration_ms: Optional[float] = Query(None, description="Filter by minimum duration in ms"),
    limit: int = Query(50, ge=1, le=500, description="Max traces to return"),
):
    """Retrieves high-level overview of distributed traces matching query filters."""
    collector = get_default_collector()
    traces = collector.list_traces(
        service_name=service_name,
        status_code=status_code,
        min_duration_ms=min_duration_ms,
        limit=limit,
    )
    return {
        "count": len(traces),
        "traces": traces,
    }


@router.get("/traces/{trace_id}")
async def get_trace_details(trace_id: str):
    """Retrieves full trace tree with spans, causality links and error events for a specific trace_id."""
    collector = get_default_collector()
    spans = collector.get_trace(trace_id)
    if not spans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trace with ID '{trace_id}' not found.",
        )
    
    root_span = next((s for s in spans if s.get("is_root") or not s.get("parent_span_id")), spans[0])
    services = list({s["service_name"] for s in spans if "service_name" in s})
    total_duration = max((s.get("duration_ms", 0.0) for s in spans), default=0.0)
    has_error = any(s.get("status_code") == "ERROR" for s in spans)
    return {
        "trace_id": trace_id,
        "root_service": root_span.get("service_name"),
        "root_operation": root_span.get("name"),
        "span_count": len(spans),
        "services": services,
        "duration_ms": total_duration,
        "has_error": has_error,
        "spans": spans,
    }


@router.get("/topology")
async def get_service_topology():
    """Retrieves service dependency topology graph with edge call counts and latency metrics."""
    collector = get_default_collector()
    topology = collector.get_service_topology()
    edges = []
    for edge in topology.get("edges", []):
        e_dict = dict(edge)
        e_dict["caller"] = edge.get("source")
        e_dict["callee"] = edge.get("target")
        edges.append(e_dict)
    
    nodes = topology.get("nodes", [])
    node_names = [n.get("name") or n.get("service_name") if isinstance(n, dict) else n for n in nodes]
    return {
        "total_services": topology.get("total_services", len(node_names)),
        "total_dependencies": topology.get("total_dependencies", len(edges)),
        "nodes": node_names,
        "service_details": nodes,
        "edges": edges,
    }


@router.get("/services")
async def list_services():
    """Retrieves registry of active services, runtime information and health status."""
    collector = get_default_collector()
    services = collector.list_services()
    return {
        "count": len(services),
        "services": services,
    }


@router.post("/services/register", status_code=status.HTTP_200_OK)
async def register_service(payload: ServiceRegisterRequest):
    """Registers or updates service metadata in the telemetry registry."""
    collector = get_default_collector()
    svc_dict = collector.register_service(
        name=payload.service_name,
        environment=payload.environment,
        version=payload.service_version,
        runtime=payload.runtime,
        health_status=payload.status,
        metadata_info=payload.metadata,
        workspace_id=payload.workspace_id,
    )
    return {
        "status": "success",
        "service": svc_dict if isinstance(svc_dict, dict) else (svc_dict.to_dict() if hasattr(svc_dict, "to_dict") else {}),
    }


@router.get("/metrics/aggregations")
async def get_metric_aggregations(
    service_name: Optional[str] = Query(None, description="Filter by service name"),
    operation: Optional[str] = Query(None, description="Filter by operation name"),
):
    """Computes and returns SLA percentiles (p50, p95, p99), error rates, and call volumes."""
    collector = get_default_collector()
    aggregations = collector.compute_aggregations(
        service_name=service_name,
        operation=operation,
    )
    return {
        "count": len(aggregations),
        "aggregations": aggregations,
    }


@router.post("/flush", status_code=status.HTTP_200_OK)
async def flush_collector_buffer():
    """Forces an immediate flush of the telemetry collector buffer."""
    collector = get_default_collector()
    flushed_count = collector.flush()
    return {
        "status": "flushed",
        "flushed_spans_count": flushed_count,
    }
