# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_a2a_mesh_sse"
# purpose: "FastAPI SSE Streaming Router for CoT, Tokens, Tool Calls & Artifacts (DNK-A2A-004 Phase 4)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from apps.api.services.a2a_streaming_engine import A2AStreamingEngine

logger = logging.getLogger("dnk.a2a.sse.router")

sse_router = APIRouter(prefix="/api/v1/a2a/mesh/stream", tags=["A2A Mesh Streaming"])

# Global streaming engine singleton for the router
streaming_engine = A2AStreamingEngine()


class CreateStreamSessionRequest(BaseModel):
    workspace_id: str
    sender_agent_id: str
    receiver_agent_id: str
    stream_type: str = "cot_stream"
    backpressure_window_size: int = 50
    metadata: Optional[Dict[str, Any]] = None


class PushStreamEventRequest(BaseModel):
    event_type: str = Field(..., description="cot_thought, token_chunk, tool_call, artifact_chunk, heartbeat, complete")
    data: Dict[str, Any]
    timeout_s: float = 2.0


class CloseStreamSessionRequest(BaseModel):
    reason: str = "completed"


@sse_router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_stream_session(req: CreateStreamSessionRequest):
    """Initializes a new A2A streaming session."""
    session = streaming_engine.create_session(
        workspace_id=req.workspace_id,
        sender_agent_id=req.sender_agent_id,
        receiver_agent_id=req.receiver_agent_id,
        stream_type=req.stream_type,
        backpressure_window_size=req.backpressure_window_size,
        metadata=req.metadata,
    )
    return {"status": "success", "session": session}


@sse_router.post("/{session_token}/events")
async def push_stream_event(session_token: str, req: PushStreamEventRequest):
    """Pushes an event frame into the streaming channel with backpressure control."""
    res = await streaming_engine.push_event(
        session_token=session_token,
        event_type=req.event_type,
        data=req.data,
        timeout_s=req.timeout_s,
    )
    if not res["success"]:
        raise HTTPException(status_code=429 if "Backpressure" in res.get("error", "") else 400, detail=res["error"])
    return {"status": "success", "seq": res["seq"], "queue_size": res["queue_size"]}


@sse_router.get("/{session_token}")
async def subscribe_stream_sse(session_token: str):
    """Subscribes to real-time Server-Sent Events (SSE) for the given streaming session."""
    session = streaming_engine.get_session(session_token)
    if not session:
        raise HTTPException(status_code=404, detail="Stream session not found")

    async def event_generator():
        async for frame in streaming_engine.consume_events(session_token):
            yield A2AStreamingEngine.format_sse_frame(
                event_type=frame["event_type"],
                data=frame["data"],
                event_id=str(frame.get("seq")),
            )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@sse_router.post("/{session_token}/close")
def close_stream_session(session_token: str, req: Optional[CloseStreamSessionRequest] = None):
    """Closes the streaming session."""
    reason = req.reason if req else "completed"
    res = streaming_engine.close_session(session_token, reason=reason)
    if not res["success"]:
        raise HTTPException(status_code=404, detail=res["error"])
    return {"status": "success", "session": res["session"]}
