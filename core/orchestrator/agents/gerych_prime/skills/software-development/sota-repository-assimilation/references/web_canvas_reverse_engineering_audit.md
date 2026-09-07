# 🌐 Web Canvas & AI Design Engine Reverse-Engineering Audit

## 🎯 Purpose
Guidelines and structured methodology for auditing and reverse-engineering complex web-based visual canvas engines, generative AI design tools (e.g. CapCut, Figma, Canva), and interactive 2D/3D editors via Browser CDP, DOM inspection, and Scene Graph extraction.

---

## 🔍 Core Audit Methodology

### 1. Canvas Layering & Multi-Tier Composition
- **Detect Stacked HTML5 Canvases**: Look for parent `.render-root` containers housing multiple `<canvas>` elements.
- **Identify Layer Roles**:
  - **Top Canvas (High z-index, pointer-events: none/auto)**: Gizmo / Transformer / Selection Handles / Rulers / Guidelines. Isolates fast manipulations (60 FPS) from heavy graphic re-renders.
  - **Middle Canvas (Active Stage)**: The primary 2D scene graph (e.g. Konva Stage, Fabric.js canvas, Pixi.js viewport).
  - **Bottom Canvas (Low z-index, pointer-events: none)**: Artboard background buffer, grid, offscreen cache.
- **Offscreen Buffers**: Inspect `#offscreenCanvas` elements used for typography metrics, text bounding-box pre-calculation, and color picker wheels.

### 2. Scene Graph & Framework Detection
- **Konva / Fabric / Pixi Detection**:
  ```javascript
  // Inspect global stage instances
  const konvaStages = window.Konva?.stages?.map(s => ({
    width: s.width(),
    height: s.height(),
    layers: s.children.map(l => ({ id: l.id(), name: l.name(), children: l.children?.length }))
  }));
  ```
- **Specialized AI Node Groups**: Look for dedicated functional node groups in the scene graph:
  - `imageCutOut`: Alpha mask / background removal layers.
  - `inpaintEditor`: Inpainting brush masks and bounding boxes.
  - `imageFrameEditor`: Aspect-ratio constrained vector slots.

### 3. State Management & Service Locator Architecture
- Check for Dependency Injection (DI) containers in React Fiber trees (`instantiationService`, Service Locator pattern).
- Telemetry & APM SDKs (`TEAVisualEditor`, Slardar APM, Sentry) providing central event pipelines.
- ContentEditable Bridges (e.g. Tiptap / ProseMirror overlays for typography and prompt bars).

### 4. Network Telemetry & API Schema Extraction
- Filter Performance Resource entries for active REST/WebSocket/SSE endpoints:
  - Workspace sync (`/workspace/mget_workspace_info`).
  - Cloud assets (`/workspace/get_all_everphoto_user`).
  - Credit consumption & quotas (`/subscription/user_info`).
