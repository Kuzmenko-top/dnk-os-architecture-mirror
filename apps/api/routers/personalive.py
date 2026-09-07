# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/routers/personalive.py"
# purpose: "FastAPI router for GVCLab/PersonaLive expressive portrait animation engine"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import logging
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from apps.api.schemas.personalive import (
    PersonaLiveAnimateRequest,
    PersonaLiveAnimateResponse,
    PersonaLiveStatusResponse,
)
from core.adapters.dnk_personalive_adapter import (
    DNKPersonaLiveAdapter,
    PersonaLiveConfig,
    PersonaLiveRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/personalive", tags=["PersonaLive Streaming Avatar"])

# Singleton adapter instance
_adapter = DNKPersonaLiveAdapter(PersonaLiveConfig())


@router.post("/animate", response_model=PersonaLiveAnimateResponse)
def animate_portrait(req: PersonaLiveAnimateRequest):
    """
    Synthesize animated talking portrait from a static image and speech audio.
    """
    try:
        core_req = PersonaLiveRequest(
            reference_image=req.reference_image,
            audio_source=req.audio_source,
            max_frames=req.max_frames,
            fps=req.fps,
            use_xformers=req.use_xformers,
            stream_gen=req.stream_gen,
        )
        res = _adapter.animate_portrait(core_req)
        return PersonaLiveAnimateResponse(
            session_id=res.session_id,
            status=res.status,
            total_frames=res.total_frames,
            fps=res.fps,
            duration_sec=res.duration_sec,
            output_stream_url=res.output_stream_url,
            cost_usd=res.cost_usd,
            metrics=res.metrics,
        )
    except ValueError as e:
        logger.warning(f"PersonaLive validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"PersonaLive runtime / SpendGuard error: {e}")
        raise HTTPException(status_code=429, detail=str(e))
    except Exception as e:
        logger.exception(f"PersonaLive unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal animation error: {e}")


@router.get("/status/{session_id}", response_model=PersonaLiveStatusResponse)
def get_session_status(session_id: str):
    """
    Retrieve live rendering status and frame counters for an active session.
    """
    status_data = _adapter.get_session_status(session_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Session not found")
    return PersonaLiveStatusResponse(**status_data)


@router.websocket("/stream/{session_id}")
async def websocket_stream_frames(websocket: WebSocket, session_id: str):
    """
    WebSocket streaming endpoint delivering progressive animation frames in real-time.
    """
    await websocket.accept()
    try:
        async for packet in _adapter.generate_frame_stream(session_id):
            await websocket.send_json(
                {
                    "session_id": packet.session_id,
                    "frame_index": packet.frame_index,
                    "timestamp_ms": packet.timestamp_ms,
                    "is_keyframe": packet.is_keyframe,
                    "frame_data_b64": packet.frame_data_b64,
                }
            )
        await websocket.send_json({"event": "stream_complete", "session_id": session_id})
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from stream {session_id}")
    except Exception as e:
        logger.error(f"Error streaming session {session_id}: {e}")
        try:
            await websocket.send_json({"event": "error", "detail": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
