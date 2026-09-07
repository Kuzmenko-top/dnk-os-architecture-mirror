# Remotion Storyboard Node Compilation & CanvasRuntimeBridge WebSocket Streaming

## Overview

This guide details the integration pattern between Canvas Visual Storyboard Nodes (`VideoStoryboardNoteNode`), the `RemotionCompiler` (`services/dnk_video_ai_creator/remotion_compiler.py`), and the real-time event pipeline `CanvasRuntimeBridge` (`core/canvas_runtime_bridge.py`).

## 1. Storyboard Node Schema Normalization

Visual storyboard cards on the Canvas (`VideoStoryboardNoteNode.tsx`) store scene sequences in either `data.shots` or `data.storyboard`. Each scene item typically provides:
- `text` or `script`: Text caption / spoken copy.
- `visual_prompt`: Visual prompt used for image/video generation.
- `duration_frames` or `duration`: Duration in frames (defaults to 90 frames / 3 seconds at 30 fps).
- `image_url` or `audio_url`: Optional media asset URLs.

`RemotionCompiler.compile_canvas_storyboard()` extracts scenes transparently:
```python
scenes = (
    node_data.get("shots")
    or node_data.get("storyboard")
    or node_data.get("scenes")
    or []
)
```

## 2. Real-Time CanvasRuntimeBridge Event Protocol

During compilation of canvas storyboard nodes, progress events are published to the event bus and relayed over the WebSocket channel (`/api/v1/ws/canvas/{id}`):

1. **`node.started` (`step: "compile_start"`)**:
   - Status: `started`
   - Payload: `{"step": "compile_start", "total_frames": N, "scenes_count": M, "aspect_ratio": "9:16"}`
2. **`node.progress` (`step: "frame_render"`)**:
   - Status: `rendering`
   - Emitted iteratively per scene sequence with calculated progress percentage:
     `{"step": "frame_render", "scene_id": idx, "scene_title": "...", "progress": int((idx + 1) / total * 100)}`
3. **`node.completed` (`step: "completed"`)**:
   - Status: `completed`
   - Payload: `{"step": "completed", "composition_id": "...", "progress": 100, "duration_in_frames": N}`
4. **`node.failed`**:
   - Emitted inside exception blocks before re-raising errors to notify connected UI clients.

## 3. Remotion v5 Clean-Room Composition AST

Generated compositions adhere to Remotion v5 idioms:
- **`Frame-as-a-Function-of-Time`**:
  All transitions compute strictly via `interpolate(frame, [0, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })`.
- **`<Sequence />` Slicing**:
  Each scene and visual asset is scoped into `<Sequence from={start_frame} durationInFrames={duration_frames}>` to isolate component lifecycles.
- **Spring Physics**:
  Dynamic zooming and scaling use `spring({ frame, fps, config: { damping, stiffness, mass } })`.
- **Number Normalization Invariant**:
  When formatting numbers into TSX strings, clean whole floats to integers (e.g. `12` instead of `12.0`) to avoid syntax discrepancies and keep generated code human-readable.

## 4. Testing & Verification Patterns

- **Spying on `CanvasRuntimeBridge` in headless tests**:
  `RuntimeEventBus.subscribe()` requires `(execution_id, tenant_id, workspace_id)` and returns an `asyncio.Queue`. For synchronous unit tests, spy directly on `bridge.publish_node_executed`:
  ```python
  captured_events = []
  original_publish = bridge.publish_node_executed

  def spy_publish(*args, **kwargs):
      ev = original_publish(*args, **kwargs)
      captured_events.append(ev)
      return ev

  bridge.publish_node_executed = spy_publish
  ```
- **Testing Event Assertions**:
  Assert `event.event_type` (`"node.started"`, `"node.progress"`, `"node.completed"`) and `event.payload["status"]`.
