# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/schemas/personalive.py"
# purpose: "Pydantic validation schemas for PersonaLive streaming portrait animation API"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class PersonaLiveAnimateRequest(BaseModel):
    reference_image: str = Field(..., description="Relative path or URI to portrait image")
    audio_source: str = Field(..., description="Relative path or URI to driving audio speech")
    max_frames: int = Field(100, ge=1, le=1000, description="Max video frames to synthesize")
    fps: int = Field(25, ge=1, le=60, description="Frame rate per second")
    use_xformers: bool = Field(True, description="Enable xFormers memory-efficient attention")
    stream_gen: bool = Field(True, description="Enable progressive frame streaming")


class PersonaLiveAnimateResponse(BaseModel):
    session_id: str
    status: str
    total_frames: int
    fps: int
    duration_sec: float
    output_stream_url: str
    cost_usd: float
    metrics: Dict[str, Any]


class PersonaLiveStatusResponse(BaseModel):
    session_id: str
    status: str
    frames_rendered: int
    total_frames: int
    fps: int
    elapsed_time_sec: float
    is_complete: bool
