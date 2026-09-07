# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/remotion_v5_patterns.md"
# purpose: "SOTA Clean-Room Composition Patterns & Architecture Spec for Remotion v5 (DNK-MEDIA-002)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎬 SOTA Assimilation Card: Remotion v5 Composition Architecture (DNK-MEDIA-002)

## 1. 🛡️ Two-Track Evolution & Legal Compliance Audit
- **Repository**: `remotion-dev/remotion`
- **Assimilated Version**: v5.0.x
- **License Classification**: `PROPRIETARY / SOURCE-AVAILABLE` (Remotion Commercial License)
- **Evolution Protocol Track**: **Track 2: Restrictive / Reverse Engineering Synthesis**
- **Legal Directives**:
  - Direct copying of source code from `@remotion/*` into DNK OS production packages is **STRICTLY PROHIBITED**.
  - All architecture, APIs, and timeline composition mechanics must be synthesized through **Clean-Room Engineering** under the permissive **MIT License**.
  - Sovereign execution runtime: Python (`core/video/`, `Pillow`, `cairocffi`, `FFmpeg`) and TypeScript (`apps/web/`, standard React/Canvas, WebCodecs) with zero external commercial runtime lock-in.

---

## 2. 🏛️ Core Architectural Primitives & Mental Model

### A. Pure Function of Frame ($f$)
In Remotion, a video composition is modeled as a deterministic, pure function of time:
$$\text{FrameState} = f(\text{frame}, \text{fps}, \text{config})$$
- There is no mutable timeline state during rendering.
- Any animated attribute (opacity, scale, translate, color, rotation) is calculated from the current frame index $f \in [0, \text{durationInFrames} - 1]$.
- Rendering can be sharded and parallelized across arbitrary workers because frame $k$ has zero temporal dependency on frame $k-1$.

### B. Hierarchical Composition Tree
Remotion organizes videos as nested temporal trees:
1. `<Composition />`: Root container defining spatial canvas (`width`, `height`), temporal bounds (`fps`, `durationInFrames`), and input `defaultProps`.
2. `<Sequence from={f_start} durationInFrames={d} />`: Shifts the local timeline context so child components experience `useCurrentFrame() = 0` at absolute frame $f_start$.
3. `<Series />` & `<Series.Sequence />`: Sequential concatenation without manual start-frame offset calculation.
4. `<AbsoluteFill />`: Layout wrapper pinning visual layers (`top: 0, left: 0, right: 0, bottom: 0`).
5. `<Loop durationInFrames={d} />`: Repeats an inner sequence indefinitely within the parent duration.

### C. Motion Physics & Math Primitives
1. **Linear & Eased Interpolation**:
   ```typescript
   interpolate(frame, [0, 30], [0, 1], {
     extrapolateLeft: 'clamp',
     extrapolateRight: 'clamp',
     easing: Easing.bezier(0.25, 0.1, 0.25, 1.0)
   });
   ```
2. **Spring Physics (Damped Harmonic Oscillator)**:
   ```typescript
   spring({
     frame,
     fps,
     config: {
       damping: 10,     // Damping coefficient
       mass: 1,         // Mass of the animated object
       stiffness: 100,  // Spring constant
       overshootClamping: false
     }
   });
   ```

### D. Asynchronous Resource Preloading & Headless Pipe
- **`delayRender()` & `continueRender()`**: Token-based barrier preventing headless frame capture until fonts, images, 3D meshes, and network assets are fully decoded.
- **Headless Renderer**:
  1. Headless browser instance (Chromium via CDP) renders each frame to a shared memory buffer or raw screenshot stream.
  2. Stdout stream piped directly into `ffmpeg` via standard stdin (`-f image2pipe -vcodec png -i -`).
  3. Video audio multiplexed with sample-rate synchronization (`aac`, `libx264`/`h264_videotoolbox` hardware acceleration).

---

## 3. 🧬 Clean-Room Implementation in DNK OS Swarm

Our clean-room implementation is mapped into:
1. `core/video/video_composition_schema.py`: Clean AST schema (Pydantic v2).
2. `core/video/easing_functions.py`: Pure Python implementation of Newton-Raphson Bezier curves and damped spring equations.
3. `core/video/remotion_renderer.py`: Dual-mode renderer (Headless React bridge + standalone kinetic FFmpeg engine).
4. `core/video/timeline_engine.py`: Multi-track timeline sequencing, layer compositing, and transition mixing.

---

## 4. 🤖 Agent Directive: `dnk_video_ai_creator`
- When generating product reels, kinetic typography, or story videos:
  1. Output strict JSON AST complying with `VideoCompositionSchema`.
  2. Prefer spring dynamics (`damping: 12, stiffness: 180`) for enter/exit animations.
  3. Use relative offsets inside sequences rather than hardcoding global frame indices.
  4. Ensure all remote media URLs are wrapped with preloading barriers.
