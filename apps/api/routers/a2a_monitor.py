# --- DNK-MRH-HEADER ---
# mrh_id: "ROUTER-DNK-A2A-001"
# purpose: "FastAPI REST API Router for A2A Multi-Agent Protocol & Swarm Runtime Monitoring"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym & Gerych Builder"
# --- END DNK-MRH-HEADER ---

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..services.a2a_protocol_engine import (
    CommunicationPattern,
    ConsensusMechanism,
)
from ..services.swarm_runtime import SwarmRuntime

router = APIRouter(prefix="/a2a", tags=["A2A Multi-Agent Protocol"])

# Global Singleton SwarmRuntime Instance for API Server
_swarm_runtime_instance: Optional[SwarmRuntime] = None


def get_swarm_runtime() -> SwarmRuntime:
    global _swarm_runtime_instance
    if _swarm_runtime_instance is None:
        _swarm_runtime_instance = SwarmRuntime()
    return _swarm_runtime_instance


class SendMessageRequest(BaseModel):
    sender: str
    recipients: list[str] = Field(default_factory=list)
    method: str
    params: dict[str, Any] = Field(default_factory=dict)
    pattern: CommunicationPattern = CommunicationPattern.P2P
    topic: Optional[str] = None
    timeout_ms: int = 5000


class BroadcastAlertRequest(BaseModel):
    sender: str
    alert: dict[str, Any]
    severity: str = "HIGH"


class ProposeConsensusRequest(BaseModel):
    proposer: str
    topic: str
    description: str
    mechanism: ConsensusMechanism = ConsensusMechanism.MAJORITY_VOTE
    threshold: float = 0.5
    participants: Optional[list[str]] = None


class VoteConsensusRequest(BaseModel):
    proposal_id: str
    voter: str
    vote: str
    rationale: str = ""


class LockRequest(BaseModel):
    resource: str
    agent: str
    ttl_seconds: float = 30.0


@router.get("/agents")
async def list_agents() -> dict[str, Any]:
    """Returns all 14 registered Swarm agents with roles and consensus weights."""
    runtime = get_swarm_runtime()
    agents = runtime.list_agents()
    return {"count": len(agents), "agents": agents}


@router.get("/topics")
async def list_topics() -> dict[str, Any]:
    """Returns active PubSub topics in the Swarm."""
    runtime = get_swarm_runtime()
    topics = runtime.message_router.list_active_topics()
    return {"count": len(topics), "topics": topics}


@router.post("/messages/send")
async def send_a2a_message(req: SendMessageRequest) -> dict[str, Any]:
    """Routes an A2AMessage across the Swarm."""
    runtime = get_swarm_runtime()
    msg = await runtime.send_message(
        sender=req.sender,
        recipients=req.recipients,
        method=req.method,
        params=req.params,
        pattern=req.pattern,
        topic=req.topic,
        timeout_ms=req.timeout_ms,
    )
    return {"status": "sent", "message": msg.model_dump()}


@router.post("/broadcast")
async def broadcast_alert(req: BroadcastAlertRequest) -> dict[str, Any]:
    """Broadcasts a high-priority alert to all Swarm agents."""
    runtime = get_swarm_runtime()
    msg = await runtime.broadcast_alert(
        sender=req.sender,
        alert=req.alert,
        severity=req.severity,
    )
    return {"status": "broadcasted", "message_id": msg.id, "recipients_count": len(runtime.agents) - 1}


@router.post("/consensus/propose")
async def propose_consensus(req: ProposeConsensusRequest) -> dict[str, Any]:
    """Initiates a swarm consensus proposal."""
    runtime = get_swarm_runtime()
    prop = runtime.request_consensus(
        proposer=req.proposer,
        topic=req.topic,
        description=req.description,
        mechanism=req.mechanism,
        threshold=req.threshold,
        participants=req.participants,
    )
    return {"status": "created", "proposal": prop.model_dump()}


@router.post("/consensus/vote")
async def vote_consensus(req: VoteConsensusRequest) -> dict[str, Any]:
    """Casts a vote on a consensus proposal."""
    runtime = get_swarm_runtime()
    try:
        updated_prop = runtime.vote_consensus(
            proposal_id=req.proposal_id,
            voter=req.voter,
            vote=req.vote,
            rationale=req.rationale,
        )
        return {"status": "voted", "proposal": updated_prop.model_dump()}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/consensus/{proposal_id}")
async def get_consensus_status(proposal_id: str) -> dict[str, Any]:
    """Retrieves current voting status and outcome of a consensus proposal."""
    runtime = get_swarm_runtime()
    if proposal_id not in runtime.consensus_engine._proposals:
        raise HTTPException(status_code=404, detail=f"Proposal '{proposal_id}' not found.")
    prop = runtime.consensus_engine._proposals[proposal_id]
    return {"proposal": prop.model_dump()}


@router.get("/locks")
async def list_active_locks() -> dict[str, Any]:
    """Lists all currently active distributed locks."""
    runtime = get_swarm_runtime()
    locks = runtime.get_active_locks()
    return {"count": len(locks), "locks": locks}


@router.post("/locks/acquire")
async def acquire_lock(req: LockRequest) -> dict[str, Any]:
    """Acquires a distributed lock on a resource."""
    runtime = get_swarm_runtime()
    success = runtime.acquire_resource_lock(
        resource=req.resource,
        agent=req.agent,
        ttl_seconds=req.ttl_seconds,
    )
    if not success:
        raise HTTPException(status_code=409, detail=f"Resource '{req.resource}' is currently locked.")
    return {"status": "acquired", "resource": req.resource, "owner": req.agent, "ttl_seconds": req.ttl_seconds}


@router.post("/locks/release")
async def release_lock(req: LockRequest) -> dict[str, Any]:
    """Releases a distributed lock."""
    runtime = get_swarm_runtime()
    success = runtime.release_resource_lock(resource=req.resource, agent=req.agent)
    if not success:
        raise HTTPException(status_code=403, detail=f"Cannot release lock for '{req.resource}' by '{req.agent}'.")
    return {"status": "released", "resource": req.resource}


@router.get("/telemetry")
async def get_a2a_telemetry(trace_id: Optional[str] = Query(None)) -> dict[str, Any]:
    """Retrieves delivery and latency telemetry records."""
    runtime = get_swarm_runtime()
    records = runtime.get_telemetry(trace_id=trace_id)
    return {"count": len(records), "telemetry": [r.model_dump() for r in records]}


@router.get("/dlq")
async def get_dead_letter_queue() -> dict[str, Any]:
    """Retrieves all poisoned / unroutable messages from DLQ."""
    runtime = get_swarm_runtime()
    dlq = runtime.get_dlq()
    return {"count": len(dlq), "dead_letters": [d.model_dump() for d in dlq]}
