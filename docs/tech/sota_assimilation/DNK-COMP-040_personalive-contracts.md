# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-COMP-040_personalive-contracts.md"
# purpose: "Component & API Contracts: Pydantic schemas and WebSocket streaming specifications"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK Swarm & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 📋 Component Contracts DNK-COMP-040: PersonaLive

## 1. Pydantic Request & Response Models
- `PersonaLiveAnimateRequest`:
  - `reference_image: str`
  - `audio_source: str`
  - `max_frames: int` (1..1000)
  - `fps: int` (1..60)
  - `use_xformers: bool`
  - `stream_gen: bool`
- `PersonaLiveAnimateResponse`:
  - `session_id: str`
  - `status: str`
  - `total_frames: int`
  - `fps: int`
  - `duration_sec: float`
  - `output_stream_url: str`
  - `cost_usd: float`
  - `metrics: Dict[str, Any]`

## 2. WebSocket Streaming Contract
- **Endpoint**: `/personalive/stream/{session_id}`
- **Frame Packet Schema**:
  ```json
  {
    "session_id": "pl_abc123",
    "frame_index": 0,
    "timestamp_ms": 0.0,
    "is_keyframe": true,
    "frame_data_b64": "..."
  }
  ```
- **Completion Event**:
  ```json
  {
    "event": "stream_complete",
    "session_id": "pl_abc123"
  }
  ```
