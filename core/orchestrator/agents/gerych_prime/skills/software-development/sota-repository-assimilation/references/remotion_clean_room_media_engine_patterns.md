# 🎬 Remotion v5 Clean-Room Media Engine & Timeline Composition Patterns

## 🛡️ Track 2 License Compliance & Clean-Room Invariant
- **Source**: `remotion-dev/remotion` (v5.0.x).
- **License**: Remotion License (source-available commercial license; restricted for companies > 3 employees).
- **Two-Track Classification**: **Track 2 (Restrictive / Reverse Engineering Synthesis)**.
- **Rule**: Direct copy-pasting or bundling proprietary runtime packages in production distributions is strictly prohibited. All capabilities must be synthesized via clean-room MIT architectures (`core/video/`, `services/video/`).

---

## 📐 Core Architectural Primitives

### 1. Frame-as-a-Function-of-Time
```typescript
// Pure deterministic function: frame -> Scene AST
type FrameRenderer = (frame: number, config: VideoConfig) => SceneNode;
```
- Eliminates time accumulation drift and frame dropping.
- Guarantees 100% frame-accurate reproducible renders across distributed workers.

### 2. Relative Timeline Nesting (<Sequence />)
- Parent time flows continuously: $t_{\text{parent}} \in [0, D]$.
- Child component receives local frame:
  $$f_{\text{local}} = f_{\text{parent}} - f_{\text{from}}$$
- Clamping and overflow control:
  - Inside duration: rendered normally.
  - Outside duration: unmounted or frozen depending on layout policy.

### 3. Spring Dynamics & Kinetic Motion
- Damped harmonic oscillator formulation:
  $$m \frac{d^2 x}{dt^2} + c \frac{dx}{dt} + k x = 0$$
- Recommended presets for kinetic text & UI animations:
  - `stiffness: 180-220` (responsive snap)
  - `damping: 12-16` (smooth deceleration without jarring oscillation)
  - `mass: 1.0`

### 4. Headless Chromium CDP Render Pipeline
1. Launch headless Chromium via Playwright/Puppeteer with fixed viewport (`width x height`).
2. Expose deterministic frame advancer (`window.advanceToFrame(n)`).
3. Read raw frame buffer via CDP (`Page.captureScreenshot`).
4. Pipe raw RGBA/JPEG stream into FFmpeg process via stdin:
   `ffmpeg -f image2pipe -vcodec png -r 30 -i - -c:v libx264 -pix_fmt yuv420p output.mp4`

---

## 🤖 Swarm Role Integration: `dnk_video_ai_creator`
- Consumes composition AST from `core/video/video_composition_schema.py`.
- Generates JSON timeline manifests rather than raw monolithic video files.
- Uses SCONES memory `Remotion SOTA Composition Patterns (Track 2 Clean-Room)` for fast retrieval.
