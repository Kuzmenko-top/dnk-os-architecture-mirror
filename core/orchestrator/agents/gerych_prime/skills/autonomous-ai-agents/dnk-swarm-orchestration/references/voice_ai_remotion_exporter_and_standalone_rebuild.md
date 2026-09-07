# Voice AI Audio Synthesis, Remotion MP4 Exporter & Standalone Rebuild Protocol

---
mrh_id: "core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/voice_ai_remotion_exporter_and_standalone_rebuild.md"
purpose: "Reference protocol for Voice AI TTS synthesis, Remotion video timeline audio sync, headless MP4 export, and Next.js standalone container rebuilds."
status: "Active"
version: "1.0.0"
---

## 1. Overview & Context

This protocol codifies the integration patterns established in `TASK-DNK-REMOTION-20260906-010` for:
1. Voice AI text-to-speech voiceover generation and streaming endpoints.
2. Micro-stutter-free audio-timeline synchronization inside the Remotion Web Player.
3. Headless MP4 video rendering via Remotion CLI and async status polling.
4. Safe Docker Compose Next.js standalone container rebuilds in agent terminal environments.

---

## 2. Audio-Timeline Synchronization Pattern (Web Player)

When synchronizing an HTML5 `<audio>` element with Remotion's frame-based timeline (`@remotion/player` or custom frame loop):
- **Micro-Stutter Pitfall**: Seeking the HTML5 audio element on every single rendered frame introduces severe audio distortion, buffering clicks, and micro-stutters.
- **Drift Threshold Formula**:
  Only synchronize/seek the audio element when the drift between the audio playhead and the video frame exceeds a safety threshold (typically 150ms / 0.15s):
  ```typescript
  const targetTime = currentFrame / fps;
  if (Math.abs(audioRef.current.currentTime - targetTime) > 0.15) {
    audioRef.current.currentTime = targetTime;
  }
  ```
- **Playback Synchronization**:
  Bind `onPlay` and `onPause` callbacks of the video player directly to `audio.play()` and `audio.pause()` to guarantee lockstep transport state.

---

## 3. Headless Remotion MP4 Exporter Architecture

- **Synthesis Endpoint**:
  `/api/v1/node-tasks/synthesize_voiceover` accepts `{ node_id, script_text, voice_id, speed }` and returns an audio URL (`/api/v1/node-tasks/voiceover_audio/{file_id}`).
- **Asynchronous Exporter Endpoint**:
  `/api/v1/node-tasks/export_video_mp4` triggers headless video compilation via `remotion render` or Python RemotionRenderer in background tasks.
- **Export Polling**:
  The client polls `/api/v1/node-tasks/video_export_status/{task_id}` until status reaches `"completed"` or `"failed"`.
  When `"completed"`, `download_url` is exposed to allow direct binary streaming.

---

## 4. Docker Compose Standalone Rebuild Invariant

In containerized monorepos where Next.js runs in `output: "standalone"` mode:
1. **Source Mutation Sync**:
   Unlike backend containers with mounted reload volumes (`volumes: - .:/app`), the Next.js standalone container does not automatically pick up changes to `apps/web/` without a rebuild.
2. **Foreground Build & Background Re-creation Pattern**:
   - `docker compose build frontend`: Execute as a standard foreground terminal command (exits with code 0 upon compiling static/dynamic chunks).
   - `docker compose up -d --no-deps frontend`: Must be executed with `background=True` (or via separate daemon management) to prevent heuristic command-line locks on long-lived daemon triggers.
   - Verify health immediately using `curl -sI http://localhost:3000/`.
