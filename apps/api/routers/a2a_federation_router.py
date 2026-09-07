# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_a2a_federation_router"
# purpose: "FastAPI REST Router for Cross-Platform Agent Mesh Federation, Routes & Health Probes (DNK-A2A-004 Phase 4)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from apps.api.services.a2a_federation_registry_service import A2AFederationRegistryService
from apps.api.services.a2a_health_probe_service import A2AHealthProbeService
from apps.api.services.a2a_mesh_router_service import A2AMeshRouterService
from apps.api.services.a2a_message_codec_service import A2AMessageCodecService
from apps.api.services.a2a_streaming_engine import A2AStreamingEngine

logger = logging.getLogger("dnk.a2a.federation.router")

router = APIRouter(prefix="/api/v1/a2a/mesh", tags=["A2A Cross-Platform Mesh"])

# Singleton instances for router layer
registry_service = A2AFederationRegistryService()
mesh_router_service = A2AMeshRouterService()
health_probe_service = A2AHealthProbeService()
codec_service = A2AMessageCodecService()
streaming_engine = A2AStreamingEngine()


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class RegisterAgentRequest(BaseModel):
    workspace_id: str
    agent_name: str
    platform: str
    api_endpoint: str
    capabilities: List[str]
    trust_tier: str = "tier-2"
    auth_token: Optional[str] = None
    public_key: Optional[str] = None
    streaming_endpoint: Optional[str] = None
    max_concurrency: float = 5.0
    metadata: Optional[Dict[str, Any]] = None


class RegisterCapabilityRequest(BaseModel):
    workspace_id: str
    capability_key: str
    display_name: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    target_sla_latency_ms: float = 1500.0
    required_trust_tier: str = "tier-2"
    cost_per_invocation: float = 0.01
    rate_limit_rpm: int = 120
    description: Optional[str] = None


class RegisterRouteRequest(BaseModel):
    workspace_id: str
    capability_key: str
    primary_agent_id: str
    fallback_agent_ids: List[str] = Field(default_factory=list)
    routing_strategy: str = "least_loaded"
    priority_weight: float = 1.0


class DispatchTaskRequest(BaseModel):
    workspace_id: str
    capability_key: str
    sender_agent_id: str
    method: str
    payload: Dict[str, Any]
    secret_key: Optional[str] = None
    trace_id: Optional[str] = None


class RecordProbeRequest(BaseModel):
    workspace_id: str
    agent_id: str
    probe_type: str = "http_ping"
    is_healthy: bool = True
    latency_ms: float = 120.0
    cpu_usage_pct: Optional[float] = None
    memory_usage_pct: Optional[float] = None
    error_message: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/agents", status_code=status.HTTP_201_CREATED)
def register_agent(req: RegisterAgentRequest):
    """Registers a federated agent in the mesh registry."""
    agent = registry_service.register_agent(
        workspace_id=req.workspace_id,
        agent_name=req.agent_name,
        platform=req.platform,
        api_endpoint=req.api_endpoint,
        capabilities=req.capabilities,
        trust_tier=req.trust_tier,
        auth_token=req.auth_token,
        public_key=req.public_key,
        streaming_endpoint=req.streaming_endpoint,
        max_concurrency=req.max_concurrency,
        metadata=req.metadata,
    )
    return {"status": "success", "agent": agent}


@router.get("/agents")
def list_agents(
    workspace_id: Optional[str] = Query(None),
    capability: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
):
    """Lists or discovers agents matching filter criteria."""
    if capability:
        agents = registry_service.discover_agents_by_capability(capability)
    else:
        agents = registry_service.list_agents(workspace_id=workspace_id, status=status_filter)
    return {"status": "success", "count": len(agents), "agents": agents}


@router.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    """Retrieves metadata of a specific agent."""
    agent = registry_service.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return {"status": "success", "agent": agent}


@router.post("/capabilities", status_code=status.HTTP_201_CREATED)
def register_capability(req: RegisterCapabilityRequest):
    """Registers a capability schema contract."""
    schema = registry_service.register_capability_schema(
        workspace_id=req.workspace_id,
        capability_key=req.capability_key,
        display_name=req.display_name,
        input_schema=req.input_schema,
        output_schema=req.output_schema,
        target_sla_latency_ms=req.target_sla_latency_ms,
        required_trust_tier=req.required_trust_tier,
        cost_per_invocation=req.cost_per_invocation,
        rate_limit_rpm=req.rate_limit_rpm,
        description=req.description,
    )
    return {"status": "success", "capability": schema}


@router.post("/routes", status_code=status.HTTP_201_CREATED)
def register_route(req: RegisterRouteRequest):
    """Registers a mesh routing rule across primary/fallback agents."""
    route = mesh_router_service.register_route(
        workspace_id=req.workspace_id,
        capability_key=req.capability_key,
        primary_agent_id=req.primary_agent_id,
        fallback_agent_ids=req.fallback_agent_ids,
        routing_strategy=req.routing_strategy,
        priority_weight=req.priority_weight,
    )
    return {"status": "success", "route": route}


@router.get("/routes/{capability_key}")
def get_route(capability_key: str):
    """Retrieves routing configuration for a capability."""
    route = mesh_router_service.get_route(capability_key)
    if not route:
        raise HTTPException(status_code=404, detail=f"Route for capability '{capability_key}' not found")
    return {"status": "success", "route": route}


@router.post("/dispatch")
def dispatch_task(req: DispatchTaskRequest):
    """Selects best healthy node with circuit breaker & failover, creates wire envelope and signs it."""
    # 1. Validate capability contract if registered
    val = registry_service.validate_capability_invocation(req.capability_key, req.payload)
    if not val["valid"] and "Unknown capability" not in str(val.get("error")):
        raise HTTPException(status_code=400, detail=val["error"])

    # 2. Select node
    available_agents = {a["id"]: a for a in registry_service.list_agents(workspace_id=req.workspace_id)}
    selection = mesh_router_service.select_target_agent(req.capability_key, available_agents)
    if not selection["success"]:
        raise HTTPException(status_code=503, detail=selection.get("error"))

    target_agent_id = selection["agent_id"]

    # 3. Create envelope
    envelope = codec_service.create_envelope(
        workspace_id=req.workspace_id,
        sender_agent_id=req.sender_agent_id,
        recipient_agent_id=target_agent_id,
        method=req.method,
        payload=req.payload,
        trace_id=req.trace_id,
        secret_key=req.secret_key,
    )

    return {
        "status": "success",
        "dispatched_to": target_agent_id,
        "is_fallback": selection.get("is_fallback", False),
        "envelope": envelope,
    }


@router.post("/probes")
def record_probe(req: RecordProbeRequest):
    """Records a synthetic health probe result."""
    res = health_probe_service.record_probe_result(
        workspace_id=req.workspace_id,
        agent_id=req.agent_id,
        probe_type=req.probe_type,
        is_healthy=req.is_healthy,
        latency_ms=req.latency_ms,
        cpu_usage_pct=req.cpu_usage_pct,
        memory_usage_pct=req.memory_usage_pct,
        error_message=req.error_message,
    )
    return {"status": "success", "result": res}


@router.get("/health/{agent_id}")
def get_agent_health(agent_id: str):
    """Retrieves comprehensive health metrics for an agent."""
    summary = health_probe_service.get_agent_health_summary(agent_id)
    return {"status": "success", "health": summary}


class CreateStreamSessionRequest(BaseModel):
    workspace_id: str
    sender_agent_id: str
    receiver_agent_id: str
    stream_type: str = "cot_stream"
    backpressure_window_size: int = 50
    metadata: Optional[Dict[str, Any]] = None


class PushStreamEventRequest(BaseModel):
    event_type: str
    data: Dict[str, Any]
    timeout_s: float = 2.0


class CloseStreamSessionRequest(BaseModel):
    reason: Optional[str] = "completed"


@router.post("/stream/sessions", status_code=status.HTTP_201_CREATED)
def create_stream_session(req: CreateStreamSessionRequest):
    """Initializes a new streaming session with bounded queue backpressure."""
    session = streaming_engine.create_session(
        workspace_id=req.workspace_id,
        sender_agent_id=req.sender_agent_id,
        receiver_agent_id=req.receiver_agent_id,
        stream_type=req.stream_type,
        backpressure_window_size=req.backpressure_window_size,
        metadata=req.metadata,
    )
    return {"status": "success", "session": session}


@router.post("/stream/{session_token}/events")
async def push_stream_event(session_token: str, req: PushStreamEventRequest):
    """Pushes a streaming frame into the bounded session queue."""
    res = await streaming_engine.push_event(
        session_token=session_token,
        event_type=req.event_type,
        data=req.data,
        timeout_s=req.timeout_s,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Push event failed"))
    return {"status": "success", "seq": res["seq"], "queue_size": res.get("queue_size", 0)}


@router.post("/stream/{session_token}/close")
def close_stream_session(session_token: str, req: CloseStreamSessionRequest):
    """Closes an active streaming session."""
    res = streaming_engine.close_session(session_token=session_token, reason=req.reason)
    if not res.get("success"):
        raise HTTPException(status_code=404, detail=res.get("error", "Stream session not found"))
    return {"status": "success", "session": res["session"]}
