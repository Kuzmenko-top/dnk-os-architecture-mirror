# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/diffusion_studio/RN-008_diffusion_studio_editor_audit_and_assimilation.md"
# purpose: "Technical Audit, Architecture Deconstruction and 5-Phase Assimilation Roadmap for Diffusion Studio Editor (diffusionstudio/editor)."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-DIFFUSION-STUDIO-ASSIMILATION"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "Gerych (Hermes Prime) & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# 🎬 RN-008: Diffusion Studio Editor Audit & DNK OS Assimilation Plan

## 📋 1. Executive Summary & Overview
**Target Repository**: `https://github.com/diffusionstudio/editor`  
**License**: MPL-2.0 (Mozilla Public License 2.0 - Weak Copyleft)  
**Skills Repository**: `https://github.com/diffusionstudio/skills` (MIT License)  
**Primary Language**: TypeScript / Universal SolidJS JSX / WebCodecs / WebGL / Rust / Koota ECS  
**Core Value Proposition**: 
Diffusion Studio is an **Agent-Native Video Editing Engine and Desktop Studio** engineered specifically for AI coding agents (Claude Code, Codex, OpenCode, Hermes). Unlike traditional NLEs (Premiere, Final Cut) or passive renderers (Remotion), Diffusion Studio establishes a **two-way live bridge between video and code**:
- **Code AST ⇄ Koota ECS ⇄ Canvas Viewport**: Changing JSX updates the canvas and timeline in real-time; dragging or editing in the visual UI writes back attributes into the JSX source code via stamped AST ID identifiers.
- **Headless Runtime (`@diffusionstudio/runtime`)**: Entity-Component-System (ECS via Koota), deterministic timing, Anime.js physics, MediaBunny WebCodecs audio/video decoding with zero DOM dependency.
- **Zero-Token Visual Verification (`dapi capture`)**: AI agents inspect frame contact sheets and specific timestamps without doing costly 100% video exports.
- **Agentic Multimodal Inspection Tools (`dapi media`)**: Native audio waveform, visual filmstrip scene transitions, Whisper-level word timestamps (`transcribe`), and conversational audio Q&A with timestamps (`listen`).
- **Composition Linter (`dapi check`)**: Static and runtime validation for black frames, hidden nodes, zero-duration clips, and missing assets.

---

## 🔬 2. Architecture & Subsystem Deconstruction

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DIFFUSION STUDIO ECOSYSTEM TOPOLOGY                   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. CLI LAYER (`apps/cli` - `dapi`):                                         │
│    - Commands: `open`, `context`, `check`, `capture`, `media`, `export`     │
│    - Transport: Local Unix Domain Socket (`diffusion-studio.sock`)          │
│    - Protocol: WebSocket / tRPC IPC bridge with bidirectional event stream  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. AUTHORING & AST SURFACE (`packages/jsx` + `@diffusionstudio/reconciler`):│
│    - SolidJS Universal JSX: `<stage>`, `<scene>`, `<sequence>`, `<video>`  │
│    - Automatic AST ID stamping (`_id="clip_123"`) for bidirectional edits    │
│    - Generative placeholders: `generate.image()`, `generate.video()`        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. HEADLESS ECS RUNTIME (`packages/runtime`):                               │
│    - Koota ECS World: Entities, Traits, Actions, Systems                   │
│    - Anime.js v4 for high-precision spring/cubic-bezier interpolation       │
│    - Mediabunny: Hardware-accelerated WebCodecs audio/video demux & decode  │
│    - Zero-DOM: Runs in Node.js, Electron background workers, or headless    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. VISUAL STUDIO & ENCODER (`apps/desktop` + `packages/encoder`):           │
│    - Electron Host + Chromium Canvas / WebGL Composition Engine             │
│    - Real-time Timeline scrubber, multi-track Sequencer                     │
│    - MP4 / WebM / GIF WebCodecs export pipeline                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚖️ 3. License & Compliance Audit (DNK OS Two-Track Protocol)
- **Codebase License**: **MPL-2.0 (Mozilla Public License 2.0)**.
- **DNK OS Compliance Assessment**:
  - MPL-2.0 is **file-level weak copyleft**. It does NOT viral-infect surrounding proprietary or differently licensed code.
  - As long as Diffusion Studio packages are consumed as external npm dependencies or interfaced via IPC (tRPC / Unix Socket / CLI `dapi` / WebSocket), DNK OS proprietary core and licensing remain completely protected.
  - **Track Classification**: **Track 2 (Isolated Adapter & Clean-Room Architecture Synthesis)**.
  - **Skills Repository (`diffusionstudio/skills`)**: **MIT License** — direct assimilation into DNK OS skills catalog without restrictions.

---

## ⚡ 4. Synergies with DNK OS Capabilities

| DNK OS Feature / Agent | Diffusion Studio Capability | Assimilated Superpower |
| :--- | :--- | :--- |
| **`dnk_video_ai_creator`** | JSX Code-as-Video AST & Headless Runtime | Bidirectional transpiler between DNK `video_composition_schema.py` and Diffusion Studio JSX. Zero-latency live preview. |
| **`apps/web` (Infinite Canvas)** | Canvas Bridge & Unix Socket / tRPC IPC | Embedding video composition viewport into Infinite Canvas notes (`VideoStoryboardNoteNode`). |
| **`gerych_auditor`** | `dapi check` & `dapi capture` | Automated pre-commit video gate: detect black frames, zero durations, and audio desyncs with 0 render cost. |
| **`gerych_researcher`** | `dapi media probe/filmstrip/waveform/transcribe` | Deep automated video understanding, B-roll sourcing, and scene boundary detection for raw user footage. |
| **`dnk_shopify`** | Generative JSX templates | One-click programmatic creation of TikTok / Instagram Reels from Shopify catalog assets. |
| **Gemini 3.8 Video Agent** | Word-level audio transcripts & frame grabs | Dynamic multimodal agentic loops without paying multi-gigabyte context token bills. |

---

## 🚀 5. Phased Assimilation Roadmap

### Phase 1: Skills & Agent Intelligence Ingestion (Immediate)
1. Ingest `diffusionstudio/skills` (`editor` and `watch` skills) into DNK OS:
   - Create `skills/diffusionstudio-editor/` and register with Hermes Prime.
   - Empower `dnk_video_ai_creator` and `gerych_researcher` with `dapi` CLI workflows.

### Phase 2: Transpiler & Schema Mapping (`services/dnk_video_ai_creator`)
1. Implement `services/dnk_video_ai_creator/src/transpilers/diffusion_studio_transpiler.py`:
   - Map DNK Pydantic composition (`VideoCompositionSpec`, `VideoTrack`, `VideoClip`, `VideoSubtitle`) into Diffusion Studio JSX format.
   - Support bidirectional reconciliation: JSX AST modifications back into Pydantic models.

### Phase 3: Headless Verification Gate (`gerych_auditor`)
1. Integrate `dapi check` and `dapi capture` into `scripts/verify_all.sh` and adversarial review pipelines:
   - Validate every generated composition for blank frames, out-of-bound clips, and asset 404s.
   - Diff contact-sheet captures against visual storyboard specs.

### Phase 4: Infinite Canvas Live Bridge (`apps/web` & `apps/api`)
1. Connect DNK OS `CanvasRuntimeBridge` (`003 / 005 ADR`) to Diffusion Studio's tRPC / WebSocket socket:
   - Real-time scrub and playback inside the Canvas video node.
   - Live synchronization of visual notes on the canvas with video timeline tracks.

### Phase 5: Autonomous E-Commerce Reel Generator (`dnk_shopify`)
1. Deploy end-to-end Shopify product-to-video pipeline:
   - Pull high-res product photos + descriptions from Shopify store (`ReBurn`, etc.).
   - Generate voiceover with Edge/ElevenLabs, background music, dynamic kinetic typography, and export viral short-form ads via WebCodecs.
