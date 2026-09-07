# --- DNK-MRH-HEADER ---
# mrh_id: "core/bricks/brick_05_video_ai/contracts/schemas.py"
# purpose: "Pydantic contract schemas for Brick 05: Video AI UGC Pipeline."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class VideoScene(BaseModel):
    scene_id: str
    duration_frames: int
    text_overlay: Optional[str] = None
    media_url: Optional[str] = None
    effects: List[str] = Field(default_factory=list)


class VideoRenderJob(BaseModel):
    job_id: str
    title: str
    fps: int = 30
    width: int = 1080
    height: int = 1920
    scenes: List[VideoScene] = Field(default_factory=list)
