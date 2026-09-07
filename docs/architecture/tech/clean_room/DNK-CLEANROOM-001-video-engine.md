# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/clean_room/DNK-CLEANROOM-001-video-engine.md"
# purpose: "Clean-Room Architecture Specification for Programmatic Video Engine (Remotion/FrameCN Reverse Engineering)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎬 DNK-CLEANROOM-001: Programmatic Video Engine Specification

## 1. Context & Clean-Room Firewall
- **Target Capability**: Declarative AST Timeline, Keyframe Interpolation & Headless Frame Rendering for `dnk_video_ai_creator`.
- **Donor Sources Analyzed**: `remotionlabs/remotion` (GPL/Proprietary dual license) and `FrameCN/framecn`.
- **Isolation Protocol**: 100% Clean-Room reverse engineering via AST interfaces without copying donor source code.

## 2. Synthesized Architecture & Pydantic Models
```python
class TimelineTrack(BaseModel):
    id: str
    media_type: str  # "video", "audio", "text", "image"
    keyframes: list[dict]
    start_frame: int
    duration_frames: int

class VideoCompositionAST(BaseModel):
    composition_id: str
    width: int = 1920
    height: int = 1080
    fps: int = 30
    duration_in_frames: int
    tracks: list[TimelineTrack]
```

## 3. License Compliance Certification
- **Verdict**: Track 2 Clean-Room Synthesized. Zero GPL contamination.
