# --- DNK-MRH-HEADER ---
# mrh_id: "core/adapters/dnk_personalive_adapter.py"
# purpose: "Hexagonal Port and Adapter for GVCLab/PersonaLive expressive portrait image animation"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import os
import uuid
import time
import asyncio
from typing import Dict, Any, Optional, AsyncGenerator
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field


class FramePacket(BaseModel):
    session_id: str
    frame_index: int
    timestamp_ms: float
    is_keyframe: bool
    frame_data_b64: str


class PersonaLiveConfig(BaseModel):
    spendguard_budget_usd: float = Field(default=10.0, description="SpendGuard ceiling for avatar synthesis")
    cost_per_second_usd: float = Field(default=0.0025, description="Cost per second of generated video")
    max_frames_default: int = Field(default=250, description="Default frame boundary limit")
    checkpoint_dir: str = Field(default="models/checkpoints/personalive", description="Weights location")


class PersonaLiveRequest(BaseModel):
    reference_image: str = Field(..., description="Path or URL to reference face portrait")
    audio_source: str = Field(..., description="Path or URL to driving audio track")
    max_frames: int = Field(default=100, ge=1, le=1000)
    fps: int = Field(default=25, ge=1, le=60)
    use_xformers: bool = Field(default=True, description="Enable xFormers memory-efficient attention")
    stream_gen: bool = Field(default=True, description="Enable progressive frame streaming")


class PersonaLiveResult(BaseModel):
    session_id: str
    status: str
    total_frames: int
    fps: int
    duration_sec: float
    output_stream_url: str
    cost_usd: float
    metrics: Dict[str, Any]


class PersonaLivePort(ABC):
    @abstractmethod
    def animate_portrait(self, req: PersonaLiveRequest) -> PersonaLiveResult:
        """Synthesize talking portrait from reference image and driving audio."""
        pass

    @abstractmethod
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve execution state and frame progress."""
        pass

    @abstractmethod
    def generate_frame_stream(self, session_id: str) -> AsyncGenerator[FramePacket, None]:
        """Stream progressive video frames in real-time."""
        pass


class DNKPersonaLiveAdapter(PersonaLivePort):
    """
    Hexagonal Adapter for GVCLab/PersonaLive real-time portrait animation engine.
    Includes SpendGuard cost metering, path traversal hardening, and async frame streaming.
    """

    def __init__(self, config: Optional[PersonaLiveConfig] = None):
        self.config = config or PersonaLiveConfig()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.cumulative_cost_usd: float = 0.0

    def _sanitize_path(self, path_str: str) -> str:
        if not path_str or ".." in path_str or path_str.startswith("/"):
            raise ValueError(f"Path traversal or absolute path detected: {path_str}")
        return path_str

    def animate_portrait(self, req: PersonaLiveRequest) -> PersonaLiveResult:
        self._sanitize_path(req.reference_image)
        self._sanitize_path(req.audio_source)

        duration_sec = req.max_frames / req.fps
        estimated_cost = duration_sec * self.config.cost_per_second_usd

        if (self.cumulative_cost_usd + estimated_cost) > self.config.spendguard_budget_usd:
            raise RuntimeError(
                f"SpendGuard ceiling exceeded: current={self.cumulative_cost_usd:.4f}, "
                f"required={estimated_cost:.4f}, budget={self.config.spendguard_budget_usd:.4f}"
            )

        self.cumulative_cost_usd += estimated_cost
        session_id = f"pl_{uuid.uuid4().hex[:12]}"

        session_meta = {
            "session_id": session_id,
            "status": "ready",
            "reference_image": req.reference_image,
            "audio_source": req.audio_source,
            "total_frames": req.max_frames,
            "fps": req.fps,
            "duration_sec": duration_sec,
            "cost_usd": estimated_cost,
            "created_at": time.time(),
            "frames_rendered": 0,
            "is_complete": False,
            "use_xformers": req.use_xformers,
        }
        self.sessions[session_id] = session_meta

        return PersonaLiveResult(
            session_id=session_id,
            status="ready",
            total_frames=req.max_frames,
            fps=req.fps,
            duration_sec=duration_sec,
            output_stream_url=f"wss://hub.dnk-os.local/api/v1/personalive/stream/{session_id}",
            cost_usd=estimated_cost,
            metrics={
                "xformers_enabled": req.use_xformers,
                "stream_mode": req.stream_gen,
                "spendguard_remaining_usd": max(0.0, self.config.spendguard_budget_usd - self.cumulative_cost_usd),
            },
        )

    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        sess = self.sessions.get(session_id)
        if not sess:
            return None
        return {
            "session_id": sess["session_id"],
            "status": sess["status"],
            "frames_rendered": sess.get("frames_rendered", 0),
            "total_frames": sess["total_frames"],
            "fps": sess["fps"],
            "elapsed_time_sec": time.time() - sess["created_at"],
            "is_complete": sess.get("is_complete", False),
        }

    async def generate_frame_stream(self, session_id: str) -> AsyncGenerator[FramePacket, None]:
        sess = self.sessions.get(session_id)
        if not sess:
            raise KeyError(f"Session {session_id} not found")

        total_frames = sess["total_frames"]
        interval_sec = 1.0 / sess["fps"]

        for idx in range(total_frames):
            sess["frames_rendered"] = idx + 1
            is_keyframe = (idx % 15 == 0)
            mock_payload_b64 = f"FRAME_DATA_{session_id}_{idx}"
            packet = FramePacket(
                session_id=session_id,
                frame_index=idx,
                timestamp_ms=idx * interval_sec * 1000.0,
                is_keyframe=is_keyframe,
                frame_data_b64=mock_payload_b64,
            )
            yield packet
            await asyncio.sleep(0.001)

        sess["is_complete"] = True
        sess["status"] = "completed"
