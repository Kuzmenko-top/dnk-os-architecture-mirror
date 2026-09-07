---
name: canvas-engine-architecture
description: "Canvas architectural patterns & headless test environments."
version: 1.0.0
author: Hermes Agent (gerych_prime)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [canvas, konva, architecture, testing, performance, indexeddb, opfs]
    related_skills: [test-driven-development, systematic-debugging]
---

# Canvas Engine Architecture & Headless Testing

## When to Use

Use when designing, optimizing, or writing headless unit/integration tests for rich visual elements, design canvas stages (e.g., Konva.js, react-konva), complex multi-tier coordinates mapping, zoom/pan systems, transactional undo/redo engines, or IndexedDB/OPFS persistence layers.
Also use when supervising or troubleshooting the local Visual Shell (`visual_shell/open_design/` Next.js web client on `:5173` & Node.js daemon on `:7456`), including native Node.js ABI versions (`better-sqlite3`) and Turbopack import boundaries. See `references/visual_shell_open_design_runtime_supervision.md`.

## 👑 1. Multi-Tier Canvas Layer Architecture

To achieve peak performance (60 FPS rendering under heavy loads) and isolate concerns, structure the canvas engine into exactly 3 independent coordinate-aligned layers:

1. **Tier 1: Background Layer**
   - Renders the grid lines, safety canvas borders, ruler markers, and coordinate space indicators.
   - Designed to redraw *only* during active panning/zooming.
   - **Performance Invariant:** Grid drawing must feature safety boundaries and Level-of-Detail (LOD) thresholds to prevent rendering millions of lines when zoomed far out.

2. **Tier 2: Content Layer**
   - Renders domain nodes, cards, shapes, connections, text blocks, and images.
   - Optimized for individual updates or targeted dirty region repaints.
   - Event listeners for node drag-and-drop, focus, or clicks live here.

3. **Tier 3: Interaction/Transient Layer**
   - Renders selection marquees, alignment guidelines, transformer handles (e.g., `Konva.Transformer`), and transient cursor overlays.
   - This layer changes highly dynamically during dragging, selecting, or resizing, so keeping it isolated prevents costly Tier 2/Tier 1 redraws during micro-interactions.

---

## ⚡ 2. 60 FPS Render Scheduling & Pacing

- **Avoid direct immediate repaints:** Direct synchronous `layer.draw()` on mousemove events causes extreme layout thrashing.
- **Debounced requestAnimationFrame Draw Loop:**
  Implement a frame scheduler that batches draw requests and fires exactly once per display frame:
  ```typescript
  private isDrawScheduled = false;

  public requestDraw(): void {
    if (this.isDrawScheduled) return;
    this.isDrawScheduled = true;
    requestAnimationFrame(() => {
      this.backgroundLayer.safeDraw();
      this.contentLayer.safeDraw();
      this.interactionLayer.safeDraw();
      this.isDrawScheduled = false;
    });
  }
  ```

---

## 🧪 3. Headless Konva.js & Canvas Testing in Node.js

Running canvas rendering code in a Node.js testing runner (like native `node --test` or Jest) requires bypassing native browser window, WebGL, and canvas features safely.

### A. Environment Configuration & Mocks
1. **Node Canvas Dependency:** Ensure `canvas` is installed in `devDependencies` (supplies Node bindings to Cairo).
2. **Global Mocks:**
   - In your test-runner entry setup, safely mock `window`, `document`, and animation loop functions:
     ```typescript
     import { JSDOM } from 'jsdom';
     
     const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>');
     global.window = dom.window as unknown as Window & typeof globalThis;
     global.document = dom.window.document;
     global.navigator = dom.window.navigator;
     
     // Mock requestAnimationFrame
     global.requestAnimationFrame = (callback: FrameRequestCallback) => {
       return setTimeout(() => callback(Date.now()), 16) as unknown as number;
     };
     global.cancelAnimationFrame = (id: number) => {
       clearTimeout(id);
     };
     ```

### B. Suppressing the Konva.js Endless Animation Loop
Konva starts a background loop when animations are initialized, which keeps the Node process alive and causes tests to hang indefinitely.
**Crucial Fix:** Explicitly suppress Konva's private loop in tests:
```typescript
import Konva from 'konva';

before(() => {
  // Disable native animation loop to prevent tests from hanging
  if ((Konva as any).Animation && (Konva as any).Animation._animationLoop) {
    (Konva as any).Animation._animationLoop = () => {};
  }
});
```

### C. The Grid Drawing Endless Loop/OOM Protection
When rendering coordinate grids, calculating step lines based on current zoom scale can result in division-by-zero or excessively small steps when zoomed out, creating millions of line objects.
**Mandatory Safety Invariants:**
```typescript
const step = Math.pow(2, Math.floor(Math.log2(gridSize / zoom)));

// SAFETY GATE: Clamp step size from falling below a threshold
const finalStep = Math.max(step, 10); 

// SAFETY GATE: Never draw more than a strict amount of steps per axis
const maxStepsPerAxis = 50; 
const startX = Math.max(bounds.minX, -width * 5);
const endX = Math.min(bounds.maxX, width * 5);

let count = 0;
for (let x = startX; x <= endX; x += finalStep) {
  if (++count > maxStepsPerAxis) break; // Circuit-breaker
  // Draw line...
}
```

---

## 💾 4. Mocking Storage (IndexedDB & OPFS) in Tests

### A. IndexedDB Mocking via `fake-indexeddb`
Do not attempt to write complex stubs for IndexedDB. Use `fake-indexeddb` as a drop-in replacement.
In test environments:
```typescript
import 'fake-indexeddb/auto';
```
This automatically populates `indexedDB` and `IDBKeyRange` globally, allowing full transactional integration testing.

### B. OPFS Mocking (Origin Private File System)
OPFS accesses native device storage via asynchronous promises on `navigator.storage.getDirectory()`.
In headless tests, create a fast local directory structure stub or a fallback Memory Storage Adapter:
```typescript
class MemoryOPFSAdapter {
  private files = new Map<string, string>();

  async write(fileName: string, content: string): Promise<void> {
    this.files.set(fileName, content);
  }

  async read(fileName: string): Promise<string> {
    if (!this.files.has(fileName)) throw new Error('File not found');
    return this.files.get(fileName)!;
  }
}
```

---

## 🔄 5. Transactional Integrity via Inverse Patching (fast-json-patch)

To implement scalable Undo/Redo commands (e.g. Ring Buffer of max 100 entries) linked directly with a local database:
1. When performing operations, utilize `fast-json-patch` to extract RFC 6902 compliant diffs between the old node state and new node state.
2. Store the operation as:
   ```typescript
   interface CommandOperation {
     path: string;
     op: 'replace' | 'add' | 'remove';
     value?: any;
     oldValue?: any; // Crucial for instant inverse patching
   }
   ```
3. Use the inverse patches to undo transactions seamlessly without storing the complete document state on each micro-interaction.

---

## 🌐 6. Live WebSocket Canvas Synchronization & Multi-Modal Streaming

To synchronize visual design canvas mutations in real-time across multiple clients and backend agents:

1. **Structured Mutation Events**:
   - Standardize on a unified real-time event model:
     ```typescript
     type CanvasSyncEvent = 
       | { type: 'screen_added'; payload: ScreenNode }
       | { type: 'edge_linked'; payload: ScreenEdge }
       | { type: 'token_updated'; payload: { key: string; value: string } }
       | { type: 'timeline_keyframe_added'; payload: KeyframeData }
       | { type: 'interactive_element_clicked'; payload: { target_screen_id: string; source_screen_id: string } };
     ```
2. **Robust Connection Lifecycle & Exponential Backoff**:
   - Implement automatic reconnection with a randomized exponential backoff delay to prevent overwhelming the server.
   - Queue outgoing mutations when the socket is in a `CONNECTING` or `CLOSED` state, and drain the queue sequentially upon a successful `OPEN` event.
3. **Multi-Modal Generation Streaming**:
   - During AI generation runs (e.g. via Gemini/Vertex AI), stream chunked updates (`generation_progress` events) to display real-time skeletons or low-fidelity wireframes before transmitting the final high-fidelity HTML/CSS layout.

---

## 🎮 7. Interactive Play Mode & Kinematic Camera Navigation

When testing interactive application prototypes directly within the design canvas:

1. **Sandboxed Event Interception**:
   - Render interactive screens using sandboxed `iframe` instances or Shadow DOM to prevent third-party scripts from hijacking canvas-level events.
   - Inject light interceptor scripts inside the iframe context to capture mouse clicks on anchor tags or interactive components annotated with `data-stitch-target="..."` or unique selectors, then dispatch them upward via standard `postMessage` interfaces.
2. **Smooth Pan-and-Zoom Transition Math**:
   - To achieve realistic fluid camera movement when navigating from screen to screen, compute the target translation vectors (`x, y, scale`) based on the target element bounds relative to the viewport.
   - Execute a smooth transition using cubic-bezier pacing over a period of 400-600ms, updating the Stage's transformation matrices dynamically on each frame.
   - Prevent panning jitter during navigation by decoupling canvas redraw loops from layout measurements.

---

## 🎨 8. React UI Integration & Zustand State Store Orchestration

To bridge the gap between declarative React UI components (Toolbar, Layers Panel, Property Inspector) and imperative Canvas CanvasStageService & Undo/Redo pattern engines, design a reactive centralized Zustand state store.

### A. The Zustand Reactive Store Pattern
1. **Store Responsibility:** Use the Zustand store to manage active visual selection states, scale/zoom levels, active UI tools, drag states, and AI processing statuses (`isProcessingAI`).
2. **Imperative Sync Bridge:** Let the store act as the controller that coordinates the under-the-hood engine state. Direct actions on the store (e.g. `updateSelectedNodeProperty`, `undo`, `redo`) should translate directly to commands executed against the state engine and storage service:
   ```typescript
   export const useCanvasStudioStore = create<CanvasStudioState>((set, get) => ({
     selectedNodeIds: [],
     activeTool: 'select',
     isProcessingAI: false,
     
     selectNode: (nodeId) => {
       set({ selectedNodeIds: [nodeId] });
       // Synchronize selected highlights on the Tier 3 interaction layer
       canvasStageService.getInteractionLayer().selectNodes([nodeId]);
     },
     
     updateSelectedNodeProperty: (property, value) => {
       const { selectedNodeIds } = get();
       if (!selectedNodeIds.length) return;
       
       // Execute update node command via Undo/Redo Stack
       const command = new UpdateNodeCommand(selectedNodeIds[0], { [property]: value });
       undoRedoStack.execute(command);
       
       // Trigger reactive UI re-renders
       set({ lastModified: Date.now() });
     }
   }));
   ```

### B. Property Inspector Panel (Reactive Geometry & Appearance)
- Divide properties into **Geometry** (X, Y, Width, Height, rotation), **Appearance** (fill, stroke, strokeWidth, cornerRadius, opacity), and **Typography** (text, fontSize, fontFamily, align).
- Support reactive binding by reading values from the Zustand store's selected node state, and dispatching updates directly to the store on input changes (`onChange`/`onBlur`).

### C. Hierarchy/Layers Panel (Visibility, Lock, & Order)
- Visual trees must sync with Node properties.
- **Node-level Locking/Visibility:** Implement a `locked` boolean property on individual nodes. Locked nodes must bypass drag listeners on the Tier 2 Content Layer and highlight with a lock symbol on Tier 3.
- **Reordering:** Implement a `ReorderLayerCommand` that manipulates node indexes in the hierarchy tree, pushes the operation to the Undo/Redo stack, and triggers a canvas stage refresh.

### D. Mocking UI & Zustand State for Testing
When writing integration unit tests for the React UI controller layer, mock the underlying engine instances and test the reactivity of state transitions:
```typescript
import { test, describe } from 'node:test';
import assert from 'node:assert';
import { useCanvasStudioStore } from './store';

describe('React UI Zustand Store & Commands Integration', () => {
  test('should handle tool selection, node lock, and undo operations', () => {
    const store = useCanvasStudioStore.getState();
    
    // Select Rect tool
    store.setActiveTool('rect');
    assert.strictEqual(useCanvasStudioStore.getState().activeTool, 'rect');
    
    // Toggle node lock state
    store.toggleNodeLock('node-1');
    assert.strictEqual(useCanvasStudioStore.getState().nodes['node-1'].locked, true);
    
    // Perform undo
    store.undo();
    assert.strictEqual(useCanvasStudioStore.getState().nodes['node-1'].locked, false);
  });
});
```

---

## 🤖 9. AI Action Adapters & Command History Integration

When integrating AI-powered capabilities (background cutout via BiRefNet, relighting via IC-Light, transparent layer generation via FLUX.1 + LayerDiffuse) into the canvas studio:

### A. Dual-Mode Mutation Pattern (In-Place vs. Non-Destructive Copy)
- **In-Place Mutation (`replaceOriginal: true`):** Modifies the existing node's `src` or metadata and wraps the change into an `UpdateNodeCommand`. Preserves node ID, position, hierarchy order, and child relationships.
- **Non-Destructive Copy (`replaceOriginal: false`):** Clones the node, offsets position (e.g. `x + 40, y + 40`), updates image source/metadata, and dispatches an `AddNodeCommand`. Leaves the original intact.

### B. Transactional Undo/Redo Dispatch
Always execute AI actions through the canvas command stack rather than raw state mutation:
```typescript
// Undo/Redo integration for AI actions
if (replaceOriginal) {
  const oldSrc = node.src;
  const updateCmd = new UpdateNodeCommand(nodeId, {
    src: processedImage,
    metadata: { ...node.metadata, aiAction: 'cutout', lastModified: Date.now() }
  });
  undoRedoStack.execute(updateCmd);
} else {
  const newNode = { ...node, id: generateId(), src: processedImage, x: node.x + 30, y: node.y + 30 };
  const addCmd = new AddNodeCommand(newNode);
  undoRedoStack.execute(addCmd);
}
```

### C. Base64 & Data URL Normalization Invariant
AI backend services require consistent image payload representations. Always implement robust normalization:
1. Accept raw bytes, base64 strings, or `data:image/png;base64,...` data URLs.
2. Strip data URL prefixes before transmitting to raw model inference backends.
3. Automatically format responses back to standard data URLs (`data:image/png;base64,...`) for instant browser rendering and `Konva.Image` consumption.

### D. Headless Testing of AI Adapters
Mock network client calls using custom `fetch` or injected mock clients with deterministic responses (mock base64 SVGs or 1x1 PNGs), asserting both node state transitions and undo/redo stack consistency.

### E. Unified Photo Studio Production Workers & Adapters
When implementing the production-grade worker pipelines for Phase 4 Photo Studio:
- **BiRefNet Adapter (`birefnet.py`):** Encapsulate the `BiRefNetAdapter` to process high-resolution background removal and mask generation with fallback modes and threshold gating.
- **IC-Light Adapter (`iclight.py`):** Support lighting-direction mapping (`natural`, `left`, `right`, `top`, `bottom`) to harmonize foreground elements with ambient or structured light prompts.
- **FLUX.1 + LayerDiffuse Adapter (`flux1.py`):** Leverage layer-by-layer alpha channel diffusion to generate pre-cutout, isolated assets on demand using specific aspect ratios and style presets.
- **Async Execution Invariant:** Always invoke worker operations within an `asyncio` async context to prevent blocking high-throughput canvas api event loops.

### F. Dual-Tab UI Integration on Living Canvas Nodes
Ensure frontend nodes (e.g. `PhotoStudioNode.tsx`) leverage a segmented dual-tab layout separating traditional **Prompt Generation** from advanced **AI Studio Actions**:
1. **Interactive Base64 Uploads:** Support file dragging/dropping and file dialogs that instantly convert files to local data URLs via a `FileReader` interface.
2. **On-Node Stage Overlays:** Maintain isolated loading states (`studioLoading`) and action types (`activeAction`) directly inside the node to keep generation feedback non-blocking and visually locked to the target asset.
3. **One-Click Replace & Extraction Actions:** Provide clear, high-contrast action buttons (`Scissors`, `Lightbulb`, `Layers`) that process the targeted canvas asset and support direct in-place mutation or standalone canvas node spawning.

---

## 🚀 10. Full-Lifecycle E2E Workflow & Modal Integration

To integrate end-to-end multi-step AI design pipelines (Upload ➡️ Cutout ➡️ Generate ➡️ Relight ➡️ Undo/Redo):

### A. Reactive AI State & Progress Toast Feedback
Expose a dedicated, isolated reactive sub-state inside the Zustand store for AI actions to avoid re-rendering heavy canvas stages on progress ticks:
```typescript
export interface AIProcessingState {
  isProcessing: boolean;
  actionType: 'cutout' | 'relight' | 'generate' | null;
  progressMessage: string | null;
  progress: number | null; // 0 to 100
  error: string | null;
}
```
Bind this sub-state to an auto-hiding `AIProgressToast` component positioned over the canvas stage with a dynamic visual progress bar and spinner.

### B. Prompt Modal with Style & Dimension Presets
Implement modular modal dialogs (`AIPromptModal`) featuring:
1. **Style Presets:** Map human-friendly chips (e.g. `📷 Photorealistic`, `🌆 Cyberpunk`, `🛍️ E-Commerce`, `🎨 Artistic`, `✨ Minimal`) directly to system prompt enhancements and negative prompts.
2. **Dimension Ratios:** Provide standard aspect-ratio presets (Square 1024x1024, Landscape 1920x1080, Portrait 1080x1920, E-Com 1200x1200) that translate into exact target node dimensions on insertion.

### C. Async Undo/Redo Invariant in Zustand Store & Headless Tests
`UndoRedoStack.undo()` and `UndoRedoStack.redo()` are asynchronous (`Promise<boolean>`) because command undo/redo actions execute async side effects (such as updating local storage DBs or async canvas node hydration).
1. **Zustand Action Signature Invariant:** Always declare `undo` and `redo` as `async (): Promise<void>` inside the Zustand store and `await stack.undo()` / `await stack.redo()`.
2. **Test Await Invariant:** In unit and E2E headless tests, always `await` store `undo`/`redo` calls (e.g. `await useCanvasStudioStore.getState().undo()`) before inspecting state or asserting `canRedo()`. Failure to `await` causes microtask race conditions where `canRedo()` returns `false` before the undone command moves to `redoStack`.

### D. AIClient Request Payload Serialization & Mock Fallback Control
When unit testing frontend `AIClient` request serialization (e.g. verifying `foreground_image_base64`, `background_image_base64`, `light_direction`, `transparent_background` fields in `fetch` bodies):
- Explicitly set `enableMockFallback: false` when constructing `AIClient({ baseUrl, enableMockFallback: false })`. This forces the client to execute the mock `globalThis.fetch` handler and capture request bodies rather than returning default mock responses on empty payloads.

### E. Headless Multi-Step E2E Test Suite Template
Test the entire chained workflow deterministically without requiring a live GPU server or browser display:
```typescript
// E2E Headless Test Sequence
// 1. Upload base image node -> AddNodeCommand
// 2. Run AI Cutout (BiRefNet) -> UpdateNodeCommand (aiCutout: true)
// 3. Run AI Generate Layer (FLUX.1) -> AddNodeCommand (aiGenerated: true)
// 4. Run AI Relight (IC-Light) -> UpdateNodeCommand
// 5. Verify complete Undo/Redo roundtrip preserves all layer coordinates
```

---

## 🚢 11. Production Deployment & Containerization Architecture

When deploying Canvas Studio to production environments with containerized microservices:

### A. Four-Tier Microservice Topology
1. **`canvas-api` (FastAPI, Port 8000):** High-throughput REST API and WebSocket session hub. Handles validation, routing, spatial graph operations, and client collaboration.
2. **`canvas-worker` (Inference Worker / Celery):** GPU worker container with dedicated CUDA device allocation and PyTorch/TensorRT model pipelines (`BiRefNet-v1`, `IC-Light`, `FLUX.1-LayerDiffuse`). Models are mounted via a persistent volume (`canvas_model_cache`) to prevent cold-start download latency.
3. **`canvas-web` (Next.js 14, Port 3000):** Standalone Next.js/React frontend container configured with SSR and client-side canvas routing.
4. **`canvas-redis` (Redis 7 Stack, Port 6379):** Event broker and distributed cache for task queues, collaborative session locks, and ring-buffer Undo/Redo persistence sync.

### B. Healthchecks & Resource Safeguards
- Always declare explicit resource limits (`deploy.resources.limits`) and reservations for CPU and RAM across all services.
- Define HTTP or CLI healthchecks on all services with `start_period`, `interval`, and `retries` to ensure downstream dependencies (e.g. `canvas-api` waiting on `canvas-redis`) boot in the correct order.

### C. CI/CD Multi-Stage Quality Gate (.github/workflows/canvas-ci.yml)
- **Backend Gate:** Runs Python 3.12+ `pytest tests/canvas/` with coverage reporting.
- **Frontend Gate:** Runs Node.js 20 `npx tsx --test` across all unit and E2E suites.
- **Docker Validation Gate:** Runs `docker compose -f docker-compose.canvas.yml config` and headless container builds with `docker/build-push-action`.

### D. Staged Launch & Minimal MVP Docker Topology
When preparing an early MVP / Beta release (5-10 users) for rapid user feedback:
1. **Scope Boundary Invariant:** Defer heavy asynchronous worker pipelines (GPU inference, Celery, Shopify live synchronization, headless Remotion video rendering) to post-MVP phases (Phase 4+).
2. **Lean MVP Services (`docker-compose.mvp.yml`):**
   - `canvas-web` (Next.js 14 frontend, port 3000)
   - `canvas-api` (FastAPI Canvas Engine, port 8000)
   - `postgres` (PostgreSQL 16-alpine, port 5432)
   - `redis` (Redis 7-alpine, port 6379)
3. **One-Click Deploy Scripting (`scripts/deploy-mvp.sh`):**
   - Perform pre-flight port availability scans (3000, 8000, 5432, 6379) before launching containers.
   - Run `docker compose -f docker-compose.mvp.yml config` to catch syntax/env errors fail-closed.
   - Poll `/health` endpoints with a bounded loop (max retries + sleep) before declaring deployment success.
4. **PostgreSQL Schema Auto-Creation & Schema Isolation Invariant:**
   - In containerized environments starting with a clean/new PostgreSQL instance, any custom schemas (such as `hub_memory` or others defined in ORM model tables' `__table_args__ = {"schema": "hub_memory"}`) do not exist by default.
   - Running SQLAlchemy's `Base.metadata.create_all(bind=engine)` directly will fail with `InvalidSchemaName: schema "hub_memory" does not exist`.
   - **Fix/Rule:** Always execute an explicit `CREATE SCHEMA IF NOT EXISTS <schema_name>` inside a database transaction block *before* invoking metadata table generation. This guarantees clean startup and prevents silent fallbacks to SQLite in production/staging environments.

### E. Next.js App Router Dedicated Health Route Invariant
To support automated container healthchecks without triggering SSR page render overhead or authentication redirects:
- Implement a lightweight, dedicated route handler at `apps/web/app/health/route.ts` (or `apps/web/src/app/api/health/route.ts` if using `src/`):
  ```typescript
  import { NextResponse } from 'next/server';

  export async function GET() {
    return NextResponse.json(
      { status: 'healthy', timestamp: new Date().toISOString(), service: 'canvas-web' },
      { status: 200 }
    );
  }
  ```
- This ensures load balancers and `docker compose` health probes receive instant 200 OK responses with zero database or render side effects.

### F. Alpine Native Build & Runtime Dependencies (npm canvas/node-canvas)
When building canvas-based Node applications on Alpine Linux:
1. **Build Stage (`builder`):** Install full Native SDK libraries needed for Cairo canvas compilation:
   ```dockerfile
   RUN apk add --no-cache python3 make g++ cairo-dev pango-dev jpeg-dev giflib-dev librsvg-dev pixman-dev
   ```
2. **Run Stage (`runner`):** Copy over the compiled node-modules but ensure runtime-shared library binaries are present in Alpine without build tooling overhead:
   ```dockerfile
   RUN apk add --no-cache cairo pango jpeg giflib librsvg pixman
   ```
   This keeps container size minimal while satisfying node-gyp bindings.

### G. Monorepo Docker Context & Dependency Ingestion
If a Dockerized service (e.g. `apps/web`) depends on sibling local packages (e.g. `packages/teleprompter-core` or `packages/video-audit-core`):
1. **Root Context SSOT:** Set the Docker build `context` to the monorepo root (`.`) instead of the app subfolder.
2. **Relative Copy Invariant:** Explicitly copy the packages into the container before compiling:
   ```dockerfile
   COPY packages/ /packages/
   COPY apps/web/package*.json ./
   RUN npm ci
   COPY apps/web/ ./
   ```
3. **Dual ESM/TS Next.js Webpack Normalization:** Ensure client-side Webpack bundle compilation does not crash when encountering server-only imports (`node:child_process`, `fs`, `crypto`) or TypeScript source files inside packages:
   ```javascript
   // next.config.mjs configuration
   const nextConfig = {
     output: 'standalone',
     transpilePackages: ['@dnk/teleprompter-core', '@dnk/video-audit-core'],
     webpack: (config, { isServer }) => {
       if (!isServer) {
         // Prevent client bundles from compiling Node.js native server-only imports
         config.plugins.push(
           new webpack.NormalModuleReplacementPlugin(
             /^node:(child_process|fs|fs\/promises|crypto|path)$/,
             (resource) => {
               resource.request = 'empty';
             }
           )
         );
         config.resolve.fallback = {
           ...config.resolve.fallback,
           child_process: false,
           fs: false,
           crypto: false,
           path: false,
         };
       }
       // Resolve .js extension imports mapping directly to actual .ts package files
       config.resolve.extensionAlias = {
         '.js': ['.ts', '.tsx', '.js', '.jsx'],
       };
       return config;
     }
   };
   ```

### H. PostgreSQL Major Version Named Volume Hygiene
To prevent database connection drops and startup crashes:
- Always align the `image:` version (e.g. `postgres:16-alpine`) in `docker-compose.mvp.yml` with the major version of pre-existing Docker named volume directory contents. PostgreSQL will refuse to boot with `FATAL: database files are incompatible with server version` if a mismatch is introduced. Always query logs immediately on startup: `docker compose logs postgres`.

---

## 🌐 12. Spatial Agentic Canvas Architecture (SOTA Synthesis & Excalidraw Integration)

When synthesizing Infinite Node-Based Canvases with AI Agent Swarms and visual boards (Excalidraw, tldraw, CapCut LUI, Flowgram.ai):

### A. Reverse-Engineering & Ingesting Encrypted Excalidraw Boards
Shared Excalidraw links (`https://excalidraw.com/#json=<id>,<key>`) are client-side encrypted with AES-GCM.
- **Zero-Dependency Headless Ingestion Pattern:**
  Instead of compiling Python AES-GCM decryption routines with external dependencies, use a headless browser (`browser_exec`):
  1. Navigate to the link via `new_tab(url)` and await scene hydration.
  2. Extract the decrypted scene elements directly from `localStorage.getItem('excalidraw')` or `window.collab?.excalidrawAPI?.getSceneElements?.()`.
  3. Parse the resulting JSON array (grouping texts, arrows with `startBinding`/`endBinding`, and bounding boxes) to reconstruct the node dependency graph.

### B. Lightweight Proxy Rendering for 60 FPS at Scale
When node cards host heavy engines (e.g. Remotion video players, full Shopify Liquid editors, rich iframes):
1. **Zoom-Level LOD (Level of Detail):**
   - At scale `< 0.6x`: Render a lightweight SVG/WebP proxy preview card and title badge without mounting complex DOM subtrees.
   - At scale `>= 0.6x`: Lazily hydrate the interactive runtime editor/player.
2. **Standardized Spatial SSOT (.canvas):**
   - Use the **JSON Canvas standard** (`jsoncanvas.org`) as the portable file representation on disk for Git versioning and agent mutation.
   - Use **Data-Flow reactive variables** (inspired by `bytedance/flowgram.ai`) to pass dynamic execution context across connected handles without re-rendering the root stage.

---

## 🗂️ 13. JSON Canvas v1.0 & Flowgram.ai Data-Flow Specification

When implementing bidirectional synchronization between `@xyflow/react` and portable canvas files:

### A. JSON Canvas 1.0 Specification (`.canvas`)
The JSON Canvas open specification (jsoncanvas.org) organizes visual canvases into portable JSON documents:
- **Nodes Array**:
  - `id`: Unique identifier string.
  - `type`: `'text' | 'file' | 'link' | 'group'`.
  - `x`, `y`, `width`, `height`: Spatial bounding box integers.
  - `text` (for `text` nodes): Raw markdown content.
  - `file` / `subpath` (for `file` nodes): Relative file paths.
  - `color`: Hex color or palette enum (`"1"` to `"6"`).
- **Edges Array**:
  - `id`: Unique edge identifier.
  - `fromNode`: Source node ID.
  - `fromSide`: `'top' | 'right' | 'bottom' | 'left'`.
  - `fromEnd`: `'none' | 'arrow'`.
  - `toNode`: Target node ID.
  - `toSide`: `'top' | 'right' | 'bottom' | 'left'`.
  - `toEnd`: `'none' | 'arrow'`.
- **DNK OS Spatial Extension (`DNKNodeData`)**:
  Encode custom node metadata (such as CapCut-style types `StrategyMarkdownNode`, `DesignGalleryNode`, `SprintKanbanNode`) inside the `text` field frontmatter or extended node attributes (`dnkType`, `category`, `upstreamData`).

### B. Flowgram.ai Reactive Data-Flow Pattern
To prevent full-stage re-renders when data changes in an upstream card:
1. Maintain an `upstreamData` map on each node's `data` payload: `{ [sourceNodeId: string]: any }`.
2. On upstream mutation, traverse downstream edges (`edge.source === sourceId`) and dispatch targeted `propagateDataFlow(sourceId, payload)` actions.
3. Downstream cards subscribe only to their specific `upstreamData` keys, allowing reactive parameter passing (e.g., brand colors propagating into Shopify code templates) at sub-millisecond speeds.

### C. Headless Testing via `tsx` and Native `node:test`
To test Zustand canvas stores and JSON Canvas converters without DOM dependencies:
- Use `node:test` and `node:assert`.
- Execute tests directly via `npx tsx <test_path>` to bypass bundler/compilation overhead. Ensure store actions update history snapshots after mutation to preserve exact undo/redo states.

---

## 🌐 14. SCONES Brand DNA, Business Templates & Onboarding Synthesis (Phase 2)

When integrating long-term brand memory (SCONES), interactive wizards, and multi-stage business pipelines into Spatial Canvas:

### A. SCONES Brand DNA Engine (`sconesStore`)
To ensure deep brand identity and style persistence across the spatial agent swarm, maintain a dedicated, workspace-isolated `sconesStore`:
- **Workspace Isolation:** Bind memory structures to a tenant-level `workspaceId` (e.g., `ws-alpha-001`) to protect multi-brand setups.
- **Unified Parameter Synthesizer:** Supply standardized prompt modifiers and environment variables directly to downstream media engines (CapCut AI, FLUX.1 style seeds, IC-Light relighting models, and BiRefNet segmentation masks).

### B. Business Templates to standard JSON Canvas (.canvas)
Design repeatable multi-node business topologies that translate instantly into standardized JSON Canvas v1.0 documents:
1. **E-Com DTC Template:** Deploys Strategy, Design, Shopify Code (Liquid AST), and Kanban nodes.
2. **UGC Video Funnel Template:** Deploys Research (hook formulas), Mindmap (script structure), Design Gallery (9:16 aspect ratio), and Kanban nodes.
3. **SaaS Growth Engine Template:** Deploys Strategy (ICP matrix), Market Research (competitors), and Code (FastAPI/Stripe) nodes.
4. **Brand Identity Launch Template:** Deploys Mindmap (archetypes), Design (palette tokens), Strategy (ToV manifest), and Kanban nodes.

### C. 4-Step Interactive Onboarding Wizard
To bridge non-technical user briefs with structured multi-node engineering specifications, implement a 4-step wizard:
1. **Identity & Audience Extraction:** Collects brand attributes, tagline, industry, and target ICP.
2. **Visual & Voice Mapping:** Presets Tone of Voice configurations (Bold, Premium, Clean, Tech) and assigns matching color tokens and font families.
3. **USP & Competitor Benchmarking:** Defines specific goals and unique selling propositions.
4. **Swarm Generation Gate & Co-Pilot Synthesis:** Runs Prompt Co-Pilot logic to construct standard model parameters, triggers `sconesStore` persistence, and programmatically spawns the initial TaskDNA node graph on the canvas using the computed Brand DNA.

### D. In-App Interactive Tutorial & Gamification (5-Step Guided Demo)
For in-app canvas onboarding walkthroughs, guided tours, and achievement systems, see [references/in_app_canvas_tutorial_and_badges.md](references/in_app_canvas_tutorial_and_badges.md):
- 5-step guided walkthrough (New Canvas → Name → Template → Generate → Explore) with UI glow targeting.
- Zero-dependency Web Audio API synthesized chimes and buzz feedback (muted by default).
- Pure CSS/SVG confetti particle system honoring `prefers-reduced-motion`.
- Gamification with 4 achievement badges (First Canvas, Quick Learner, Onboarding Complete, Creative Mind) and Web Share API.
- WCAG 2.1 AA accessible progress indicators (`role="progressbar"` with ARIA attributes).

---

## 🌲 15. Task Forest & Multi-Tree Spatial Agentic Orchestration

When scaling agentic workspaces beyond single-pipeline DAGs or flat task lists:
- **Task Forest Paradigm:** Model workspace goals as a forest of interconnected domain trees (Knowledge/Memory Tree, Product Delivery Tree, R&D Hypothesis Tree, Quality Gate Tree).
- **Reactive Cross-Tree Edges:** Enable dynamic cross-tree dataflow where changes in contracts or gate failures propagate visual notifications across tree boundaries.
- **Event-Sourced Time-Travel Nodes:** Encapsulate task nodes as event-sourced capsules tracking author, prompt hypotheses, diffs, tool executions, and gate verification states.
- **Reference Specification:** See `references/task-forest-spatial-integration.md` for full 5-level plant taxonomy schemas (Field ➔ Sector ➔ Tree ➔ Bush ➔ Flower), recursive Bottom-Up Rollup calculations, and interactive double-panel React canvas integration.

---

## 🎨 16. CapCut AI Design + Google Stitch Spatial Paradigm Synthesis

When architecting high-velocity agentic systems that unify generative UI design, multimedia production, and social intelligence:

### A. Dual UX Synthesis (CapCut LUI + Google Stitch Minimalist Variants)
1. **Google Stitch Workflow (`stitch.withgoogle.com`)**:
   - **Variant Exploration**: Parallel generation of alternative layouts, copy styles, and design themes side-by-side on the infinite canvas.
   - **Adaptive Design Tokens**: Centralized Obsidian Dark & Crisp Light token synchronization across Web components, Shopify Liquid templates, and Canvas preview slices.
2. **CapCut AI Design Workflow (`capcut.com/ai-design`)**:
   - **Contextual In-Place Prompting (LUI)**: `CopilotToolbar` accessible directly on any node, canvas coordinate, or media asset.
   - **1-Click Media Actions**: In-canvas background removal (`BiRefNet`), directional relighting (`IC-Light`), and generative layer synthesis (`FLUX.1 + LayerDiffuse`).
   - **Asset & Project Vault**: Centralized asset drawer tracking brand assets, generated images, reference videos, and export bundles.

### B. In-Canvas Social Video Intelligence (`@dnk/video-audit-core`)
- Mount the multimodal pipeline directly into spatial nodes (`VideoAuditReportNode`).
- Ingestion of TikTok, Instagram Reels, and YouTube Shorts into synchronized analysis streams:
  1. WhisperX speech transcription with Ukrainian domain vocabulary.
  2. Scene boundary detection and OCR frame extraction.
  3. Audio prosody, pitch, and energy profiling.
  4. 3-second hook evaluation, retention scoring, and claim verification.
- Direct derivation of high-retention video scripts into `@dnk/teleprompter-core` for immediate teleprompter recording.

### C. Master Architecture Reference
- Consult `docs/architecture/DNK_OS_AGENTIC_SYSTEM_CANVAS_BLUEPRINT.md` for the unified system topology, phase roadmap (Phases 3 to 6), and quality invariants.

---

## 17. Unified Working Canvas Convergence Pattern

When consolidating disparate tools (structured node graphs, freehand whiteboards, AI prompt docks, e-commerce sync, teleprompter):
1. **Central Store SSOT**: Bind the master workspace shell directly to the centralized Zustand reactive store (`useCanvasStore`), replacing isolated component-level states.
2. **Dual-Layer Overlay**: Mount freehand drawing as a toggleable overlay layer over the structured node canvas rather than routing to a separate page.
3. **In-Place Swarm Docking**: Embed a floating prompt dock (`StitchPromptDock`) on the canvas to spawn and link new domain nodes on demand, complete with model selectors, keyword-based swarm routing, and voice-simulation feedback.
4. **Media Templates & HTML5 Drag-and-Drop Spawning**: Integrate visual media templates (Video 9:16 Remotion storyboards, Shopify OS 2.0 specs, Photo Studio concepts) into sidebars supporting direct HTML5 drag-and-drop onto React Flow coordinates via `screenToFlowPosition`.
5. **Live Rendering Feedback on Living Nodes**: Equip media-centric notes (`VideoStoryboardNoteNode`) with real-time Remotion compilation progress bars, preview players, and timeline controls.
6. **PostgreSQL 16 Spatial Persistence**: Synchronize canvas revisions transactionally with the backend API (`services/dnk_canvas_api`).
- See `references/unified_working_canvas_convergence.md` for the detailed convergence architecture and checklist.
- See `references/unified_workspace_ssot_integration.md` for the step-by-step Zustand store SSOT integration, 13+ living node registrations, and JSON Canvas export/import.
- See `references/sketch_whiteboard_overlay_integration.md` for transparent SVG drawing overlay integration, coordinate projection projection math, and unified Undo/Redo history.
- See `references/postgres_delta_sync_and_offline_hydration.md` for PostgreSQL 16 (hub_memory) atomic delta sync, conflict resolution, WebSocket collaboration broadcast, and IndexedDB offline-first hydration.
- See `references/video_intelligence_canvas_integration.md` for the detailed Phase 5 Video Intelligence multi-worker backend pipeline, SVG Retention Curve rendering, and TypeScript compilation/isolatedModules invariants.
- See `references/canvas_runtime_bridge_events.md` for Canvas Runtime Bridge node lifecycle event mapping (`node.created` / `node.executed`), Pydantic v2 `mode="json"` Redis serialization, and selection execution scenario orchestration.

---

## 🤖 18. Swarm Co-Pilot, Budget Guard & Intent Resolver (Phase 3 Integration)

To support real-time intelligent co-piloting directly within the design canvas without rendering bottlenecks or unvalidated cost overruns:

### A. Budget Guard Pattern (`budgetGuard.ts`)
- **Predictive Tokens & Cost Matrix:** Define a strict cost table matching model tokens (`input`/`output` cost per 1M tokens).
- **Multi-Agent Evaluation:** Iterate through targeted agents (e.g. `dnk_shopify`, `dnk_video_ai_creator`) and calculate cost predictions based on input prompt context before calling APIs.
- **Risk Triage:** Dynamically assign risk levels (`low` < $0.05, `medium` < $0.20, `high` >= $0.20) for visual feedback in UI toolbars.

### B. Swarm Intent Resolver Pattern (`intentResolver.ts`)
- **Semantic Classification:** Map natural-language user requests (e.g., "reskin this node", "audit check") to core execution intents and specific target swarm agents.
- **Brand DNA Integration:** Enrich queries automatically with brand attributes (e.g., target market, tone of voice, visual palette) extracted from the centralized brand memory storage (`sconesStore`).
- **Graph Topology Mutations:** Formulate structured node adjustments (inserting new nodes, linking downstream edges) dynamically based on agent resolution.

### C. Floating Context-Aware Copilot Toolbar (`CopilotToolbar.tsx` & `DNKStudioWorkspace.tsx`)
- **Direct Canvas Coordinates Positioning:** Compute floating position `style={{ top, left }}` over active/selected nodes using canvas zoom/pan projection coordinate transformations.
- **Keyboard Shortcut Toggle (`Cmd+K` / `Ctrl+K`):** Global event listeners to summon/hide the toolbar at the cursor position or selected node anchors.
- **Non-blocking Stream Progress:** Render asynchronous progress states (e.g., loading spinners, progress bars, mock streaming tokens) using lightweight component triggers, preventing global canvas stage repaints during generation.

---

## 🛠️ 19. Next.js App Router Client-Side Hydration & SWC Build Pitfalls

When developing or integrating the visual workspace within a Next.js App Router environment, adhere to these strict client-side validation rules to prevent build or runtime exceptions. See `references/nextjs-xyflow-integration.md` for complete technical details, code blocks, port conflict routines, Docker network proxy rewrites, safe JSON error intake, Next.js hydration mount guards, `@xyflow/react` v12 custom node typing, and monorepo tsconfig exclusions.

### A. Machine-Readable Header (MRH) Comment Syntax (SWC Loader Safety)
- **Problem:** Next.js SWC loader and Webpack parsers fail with `Module build failed ... Expected ident` when encountering Python-style `#` comments inside `.ts`, `.tsx`, `.js`, `.jsx`, or `.css` files.
- **Mandatory Invariant:** Always use double-slash `//` or block `/* ... */` comment blocks for MRH headers in web and client-side modules:
  ```typescript
  // --- DNK-MRH-HEADER ---
  // mrh_id: "apps/web/components/canvas/MyNode.tsx"
  // purpose: "Render custom media node on the canvas."
  // --- END DNK-MRH-HEADER ---
  ```

### B. Client-Side Route Parameters using `useParams()`
- **Problem:** In Next.js 14+ client components (`'use client'`), passing dynamic parameters as synchronous `params` props in components or layouts can trigger unhandled runtime desynchronization or serialization crashes.
- **Mandatory Invariant:** Always access dynamic canvas route parameters using the `useParams()` hook from `'next/navigation'`:
  ```typescript
  'use client';

  import { useParams } from 'next/navigation';

  export default function CanvasPage() {
    const params = useParams();
    const canvasId = params?.canvasId as string;
    
    // Use canvasId safely...
  }
  ```

### C. React Flow Hook and Zustand Selector Desynchronization (`TypeError: setNodes is not a function`)
- **Problem:** When integrating React Flow components with a centralized Zustand store (`useCanvasStore`), components or toolbars may try to destructure `setNodes` or `setEdges` from the store (or other custom helper methods), assuming they are native setters, causing instant client-side crashes with `TypeError: setNodes is not a function`.
- **Mandatory Invariant:** Always implement and expose explicit setters inside your Zustand state definition (`CanvasState` and `useCanvasStore`) to mirror standard React Flow state mutators, supporting both direct array assignment and functional updaters:
  ```typescript
  // 1. Definition in CanvasState:
  setNodes: (nodes: Node[] | ((prev: Node[]) => Node[])) => void;
  setEdges: (edges: Edge[] | ((prev: Edge[]) => Edge[])) => void;

  // 2. Implementation in useCanvasStore:
  setNodes: (nodesOrUpdater) => {
    set((state) => {
      const nextNodes = typeof nodesOrUpdater === 'function'
        ? (nodesOrUpdater as Function)(state.nodes)
        : nodesOrUpdater;
      return { nodes: nextNodes };
    });
  },
  ```

---

## 🎨 20. Google Stitch UI High-Fidelity Spatial Integration

When implementing or transitioning a React Flow workspace (`@xyflow/react`) to the minimalist, high-fidelity Google Stitch spatial design paradigm:

### A. Core Canvas Theme & Dot Grid Configuration
- **Canvas Base Background:** Set a uniform dark graphite base color `#0d0f12` or `#0e1014` on the parent container.
- **React Flow Grid:** Replace default lines with white dot-pattern indicators (`BackgroundVariant.Dots`) set to a contrasting dark gray color `#262830` with custom spacing (e.g. `12` or `16`).
- **Handle Appearance Invariant:** Hide heavy default connection lines. Set handles (`target` / `source`) to be small, translucent, and style them to highlight on hover or select to preserve the clean, infinite-board aesthetic.

### B. Segmented Floating Multi-Widget Architecture
To keep the infinite stage unobstructed, mount interface widgets as absolute, high-z-index, floating overlays directly over the full-bleed canvas container:
1. **Top Navigation (`StitchTopNav`):** Minimal horizontal bar with transparent background or glassmorphism (`backdrop-blur-xl bg-[#0e1014]/60`). Houses hamburger menu, Play/Preview trigger, outlined "Export" and "Share" action buttons, and a circular accent profile avatar (e.g. Purple `#7C3AED` with white initials).
2. **Top-Left Status Card (`StitchGenerationStatusCard`):** A floating dark card (`#13161b` with border `#262830`) containing the AI status emblem, the raw user query bubble (Ukrainian ToV alignment: `"прибери останній к..."`), copy action icons, and real-time generation error/warning texts with a retry handler.
3. **Bottom-Left Agent Log (`StitchAgentLog`):** Oval rocket pill widget (`🚀 Agent log ▾`) that expands into a step-by-step progress drawer, showing active task status in real-time.
4. **Bottom-Center Prompt Dock (`StitchPromptDock`):** Floating stadium-shaped input dock. Contains prompt input, model selector (`Balanced` preset dropdown with color accents), microphone button, and a circle send trigger.
5. **Bottom-Right Navigation Controls (`StitchCanvasControls`):** Compact inline block providing Undo/Redo commands, zoom multiplier display (`100%`), and a help request trigger (`?`).
6. **Right-Center Spatial Toolbar (`StitchSpatialToolbar`):** Floating vertical dock holding canvas mode tools (Select, Frame, Draw, Hand, Image, Emoji, Star). Active states highlight with solid circular background markers.

### C. Demonstration Artboard Topologies & Color Tokens
Provide rich high-fidelity node templates (`StitchArtboardNode`) immediately on workspace mount:
- **E-Com Thumbnails & Typo Scales:** Miniature analytics cards and typography hierarchies.
- **Obsidian Flow Design System:** Visual chip row displaying primary Neon Mint (`#33EE75`), deep purple, charcoal gradients, together with button grids and form fields.
- **Mobile & Desktop Executive Dashboards:** Interactive frames housing fake CLI shell logs, Latency monitors, code compiler progress tickers, and diagnostic dashboards.

### D. Extended Spatial Drawers Suite & Canonical Consolidation (ADR 016 Variant B)
To prevent architectural drift and duplicate interfaces, all spatial UI elements and control drawers reside under `apps/web/components/stitch/` with barrel export at `index.ts`. Legacy `visual_shell` is permanently frozen as `DEPRECATED`.
- **6 Canonical Drawers:** `StitchSmartInspector` (WCAG 2.1 AA audit & DESIGN.md tokens), `StitchShopifyPreviewDrawer` (OS 2.0 AST Liquid & schema validation), `StitchBiAnalystDrawer` (DuckDB NL2SQL), `StitchTaskForestDrawer` (5-level hierarchy & time-travel scrubber), `StitchSwarmCommandCenter` (token & latency HUD), and `StitchKineticTimeline` (event playback).
- **Automated Contracts:** OpenAPI 3.1 types generated via `scripts/system/generate_frontend_types.py` into `apps/web/types/apiGenerated.ts`.
- **Reference Guide:** See [`references/google_stitch_extended_drawers_and_canonical_consolidation.md`](references/google_stitch_extended_drawers_and_canonical_consolidation.md).

---

## ⚡ 21. Canvas Runtime Bridge, Lifecycle Events & Redis Pub/Sub Transport

When connecting visual Infinite Canvas nodes and bounding-box selections with runtime execution (EventBus, Redis, LangGraph):

### A. Node Lifecycle Events
- **`node.created`**: Emitted when a canvas node or selection component enters the execution graph. Carries node metadata, bounding box coordinates, and execution thread ID.
- **`node.executed`**: Emitted upon node execution completion or failure. Carries execution duration, status (`completed` or `error`), output artifacts, and updated node states.

### B. Serialization Pitfall (Pydantic v2 + Redis / JSON)
- **Problem**: Serializing models with `datetime` fields (e.g. `timestamp`, `updated_at`) using `event.model_dump()` followed by `json.dumps()` raises `TypeError: Object of type datetime is not JSON serializable`.
- **Mandatory Invariant**: Always dump via `event.model_dump(mode="json")` prior to `json.dumps(...)` to ensure standard ISO 8601 string formatting across Redis pub/sub channels.

### C. Graceful Fallback & Headless Resilience
- Always wrap external Redis publishing with non-blocking error handling to ensure seamless offline / headless testing via the in-memory `RuntimeEventBus`.
- Reference: `references/canvas_runtime_bridge_events.md`.

---

## ⚡ 22. Swarm Bridge & Live Agent Log Streaming (Phase 1 Synthesis)

When wiring up spatial canvas nodes (e.g. `ShopifySpecNoteNode`, `VideoStoryboardNoteNode`) to trigger backend multi-agent swarms with live log streaming and Langfuse tracing:

### A. Sub-50ms Dispatch & Optimistic Status Transition
- On node trigger action, immediately update node status optimistically to `thinking` (<10ms) to provide immediate tactile UI feedback.
- Transmit `TASK_EXECUTE` payload over active collaboration WebSocket (`/api/v1/ws/canvas/{id}`) carrying `nodeId`, `taskType`, and execution context enriched with `userSoul` (founder/brand identity context) and `activeProjectId`.

### B. Dual Status & Message Normalization Invariants
- **Dual Status Invariant:** When receiving `TASK_STATUS` events (`idle` → `thinking` → `running` → `completed` / `error`), update both `node.status` and `node.data.status` (and `node.data.agentStatus`) so both React Flow container selectors and custom internal card components react consistently.
- **Message Key Normalization:** Support heterogeneous swarm backend log structures by normalizing `log.message || log.text` and setting defaults for level (`info`) and step (`execution`).
- **Log Buffer Cap:** Maintain `activeLogs` ring-buffer capped at 200 items in Zustand to prevent canvas memory leaks during long-running agent streaming.

### C. Live Log Inspector UI & Langfuse Dashboard Binding
- In `StitchAgentLog.tsx`, provide reactive filtering by `selectedNodeId` with an "All Logs" fallback.
- Render Langfuse `trace_id` (e.g. `trace-wf-XXXXXXXX`) directly in the inspector drawer for one-click telemetry inspection.
- Auto-scroll smoothly to latest incoming logs via `ref.scrollIntoView({ behavior: 'smooth' })`.
- Reference: `references/swarm_bridge_canvas_integration.md`.

---

## 🗺️ 23. Mind Map Spatial Nodes, Semantic Edges & Graph Persistence (Phase 11 Kickoff)

When extending the Infinite Canvas with hierarchical Mind Mapping capabilities:

### A. 5 Core Mind Map Node Types (`apps/web/components/canvas/nodes/`)
1. **Idea (`MindMapIdeaNode.tsx`):** Sticky note aesthetic (Yellow `#FEF08A`, border `#FACC15`) with tags and confidence scores.
2. **Goal (`MindMapGoalNode.tsx`):** High-contrast target card (Green `#DCFCE7`, border `#4ADE80`) tracking deadline, metrics arrays, and achievement status.
3. **Task (`MindMapTaskNode.tsx`):** Actionable item card (Blue `#DBEAFE`, border `#60A5FA`) with assignee, priority triage, and Kanban status (`todo`/`doing`/`done`).
4. **Agent (`MindMapAgentNode.tsx`):** Swarm worker representation (Orange `#FFEDD5`, border `#FB923C`) linking to live executor telemetry and result payloads.
5. **Evidence (`MindMapEvidenceNode.tsx`):** Research artifact container (Purple `#F3E8FF`, border `#C084FC`) holding file paths, URLs, and previews.

### B. 4 Semantic Edge Types (`apps/web/components/canvas/edges/`)
1. **Dependency (`DependencyEdge.tsx`):** Red directional arrow (`#EF4444`) enforcing execution prerequisites.
2. **Relation (`RelationEdge.tsx`):** Blue dashed wavy line (`#3B82F6`) denoting associative, non-blocking conceptual links.
3. **Cluster (`ClusterEdge.tsx`):** Gray translucent boundary/connector (`#9CA3AF`) denoting topic groupings.
4. **Milestone (`MilestoneEdge.tsx`):** Purple arrow (`#A855F7`) connecting high-level Goals to discrete deliverable milestones.

### C. PostgreSQL 16 Persistence & WebSocket Broadcast
- Persist structured graphs into `mind_map_nodes` and `mind_map_edges` with JSONB payloads.
- Broadcast real-time node/edge lifecycle mutations (`MINDMAP_NODE_CREATE`, `MINDMAP_EDGE_CREATE`) over the collaboration WebSocket bridge.
- See `references/mind_map_nodes_edges_specification.md` for full database schemas, payload structures, and verification gates.

---

## 🎬 24. Remotion Storyboard Node Compilation & Live Bridge Streaming

When transforming visual canvas nodes (`VideoStoryboardNoteNode`) into executable Remotion v5 TSX compositions with real-time execution feedback:

### A. Direct Storyboard Node Compilation (`compile_canvas_storyboard`)
- Extract scenes from node attributes (`shots`, `storyboard`, or `scenes`) with automatic schema fallback.
- Normalize scene durations, visual prompts, and voiceover text into Remotion clips within `<Sequence />` boundaries.

### B. CanvasRuntimeBridge WebSocket Streaming Invariant
- Automatically dispatch lifecycle execution events via `CanvasRuntimeBridge.publish_node_executed(node_id, status=..., payload=...)`:
  - `step: "compile_start"` (`status="started"`, `node.started`)
  - `step: "frame_render"` (`status="rendering"`, `node.progress`)
  - `step: "completed"` (`status="completed"`, `node.completed`)
  - `step: "failed"` (`status="failed"`, `node.failed`)

### C. Clean-Room Spring & Math Formatting Invariant
- Calculate dynamic motion using Remotion v5 spring physics (`damping: 12`, `stiffness: 180`, `mass: 0.8`).
- Format integer-equivalent floats cleanly in TSX templates (`12` instead of `12.0`) to avoid formatting churn and maintain clean syntax.
- See `references/remotion_canvas_compiler_bridge.md` for complete schema normalization, event bus subscription patterns, and test spy setups.

---

## 📓 25. Obsidian Canvas & Markdown Two-Way Synchronization (Phase 11 Stage 3)

When integrating visual Infinite Canvases with external Obsidian Vaults (Markdown notes + `.canvas` JSON Canvas files):

### A. Dual Bundle Export & File Sanitization
- **Bundle Generation:** Use `export_canvas_bundle(nodes, edges, output_dir=..., canvas_name="...")` to generate both the standard JSON Canvas file and corresponding markdown files with YAML frontmatter.
- **Contract Pitfall:** `export_canvas_bundle` takes `output_dir` (not `export_dir`) and returns `{"canvas_path": str, "markdown_files": List[str]}`.

### B. Graph Parsing & Last-Write-Wins Conflict Resolution
- **Canvas Parser Signature:** `parse_canvas_file(file_path)` returns a dictionary `{"nodes": list, "edges": list}` (not a tuple).
- **Conflict Strategy:** When reconciling local canvas changes with external vault edits, `resolve_conflicts(..., strategy="last_write_wins")` evaluates node `updated_at` / file `mtime` stamps and unifies tag sets across versions.
- **Frontend & WS Protocol:** Mount floating `ObsidianSyncBar.tsx` wired to `canvasStore.ts` and handle real-time `OBSIDIAN_SYNC_STATUS` WebSocket updates.

### C. Vault Archival & Virtualenv Testing Invariants
- **Vault Archival:** Write architectural specs to `~/Documents/DNK_HUB My Notes/DNK_HUB My Notes/` using 3-digit prefixes (e.g. `007 ...md`), MRH headers, and update `000 DNK HUB Index.md`.
- **Test Runner Invariant:** Always execute tests via `.venv/bin/pytest` from `$HUB_ROOT` (`tests/core/test_obsidian_export_import.py`, `tests/canvas/test_obsidian_sync.py`), never system `pytest` or from subdirectories.
- Reference: `references/obsidian_canvas_bidirectional_sync.md`.

## 🗺️ 26. Archify Spatial Node & A2A Live Mesh Telemetry
- **Component**: `apps/web/components/canvas/nodes/ArchifySpatialNode.tsx` registered in `NodeRegistry.ts` (category: `'architecture'`, icon: `Layers`) and `DNKCanvas.tsx` (`nodeTypes`).
- **Telemetry Bridge**: `packages/archify/assets/archify_telemetry_bridge.js` connects diagram SVGs to live `/ws/a2a` mesh events with animated path dash pulses.
- Reference: `references/archify_spatial_node_and_mesh_telemetry.md`.

## ⚡ 27. Canvas Load Testing, WebSocket Latency & Headless Benchmarks
- **Dual-Runtime Pattern**: Detect `"locust" in sys.argv[0].lower()` to avoid `gevent.monkey.patch_all()` recursion collisions with `pytest` discovery in multi-purpose benchmark files.
- **Thread-Local TestClient**: High-concurrency `ThreadPoolExecutor` benchmarks must store `TestClient(app)` in `threading.local()` to prevent AnyIO event portal lock contention.
- **Target Contracts**: WebSocket p95 ≤ 100ms (10–100 clients), Canvas Generate p95 ≤ 200ms, Canvas Update p95 ≤ 50ms, Stream Throughput ≥ 100 RPS.
- **Reference**: `references/canvas_load_testing_and_benchmarks.md` and benchmark report `docs/performance/BENCHMARKS.md`.

## 🧬 28. OCC Structural Graph Mutation Resolver & 3-Way Merge (Slice 16.4)
- **3-Way Resolution**: Ancestor (Base), Local (Mine), Remote (Theirs) structural graph diffing to prevent data loss in collaborative canvas & task graphs.
- **Position Strategies**: `shift` (+20px vector shift on dual modification to eliminate visual overlap) vs `last_write_wins`.
- **Node Metadata & Edges**: Set union for tags, list union for criteria/files, non-destructive description concatenation, and strict DAG cycle detection (`ConflictType.CYCLE_DETECTED` -> HTTP 409).
- **Reference**: `references/occ_structural_graph_merge.md` and `core/occ_merge.py`.

## 🕸️ 29. DAG Canvas Drag-to-Connect Cycle Prevention & AI Epic Decomposition
- **Drag-to-Connect Invariants**: Intercept self-loops (`source === target`) and calculate transitive reachability (BFS/DFS) in `isValidConnection` before dispatching edge creations to prevent DAG cycles.
- **Dual Schema Normalization**: Pydantic schemas must normalize `relation` and `dependency_type` symmetrically via `@model_validator(mode="before")` to maintain cross-client compatibility.
- **AI Epic Decomposition**: Partition Epics into Tri-Tier sequential child nodes (Spec/Arch -> Build/Implementation -> Gate/Audit) assigned to specialized swarm agents with automatic spatial layout offset.
- **Reference**: `references/dag_canvas_cycle_prevention_and_ai_decomposition.md`.

## 🕸️ 30. DAG Auto-Layout, Barycenter Heuristic & Batch Positions Persistence
- **Topological Layering**: Calculate longest-path rank depth via dependencies (`depends_on`, `blocks`, `spawns_from`) with in-degree roots forming Layer 0.
- **Barycenter Crossing Minimization**: Order nodes in layer $L$ by average $Y$-coordinate of upstream parents in layer $L-1$. Layer 0 roots sorted by priority (`critical` -> `high` -> `medium` -> `low`).
- **Spatial Grid Step**: Horizontal $\Delta X = 380\text{px}$, vertical $\Delta Y = 190\text{px}$.
- **Batch Persistence Invariant**: Provide a dedicated backend endpoint (`POST /api/v3/node_tasks/batch_positions`) to ingest the entire coordinate map atomically in $O(1)$ HTTP round-trips.
- **Reference**: `references/dag_canvas_auto_layout_and_batch_persistence.md`.

## 🕸️ 31. Live Swarm Node Execution, Neon Pulse & Ring-Buffer Terminal Logs
- **Bounded Ring-Buffer Storage**: Maintain an in-memory ring-buffer per node (`_task_logs: Dict[str, List[Dict[str, Any]]]`) capped at 100 entries to prevent memory leaks during rapid streaming.
- **Execution Lifecycle Endpoint**: `POST /api/v3/node_tasks/{node_id}/execute` supports `agent_override`, `task_instructions`, and `auto_complete` with automated graph dependency resolution and step log recording.
- **Neon Agent Halo & Runner Indicator**: Actively running nodes display an emerald pulse ring (`ring-2 ring-emerald-400/80 shadow-[0_0_25px_rgba(52,211,153,0.35)] animate-pulse`) with a pinging runner badge.
- **In-Drawer Execution Terminal**: Dark monospace terminal with color-coded level badges (`INFO`, `STEP`, `DONE`, `THOUGHT`, `ERROR`) and smooth auto-scroll.
- **Reference**: `references/dag_canvas_live_swarm_execution_and_pulse.md`.

## 🕸️ 32. Live WebSocket Streaming & Reactive Node Lifecycle (Slice 20.2)
- **Zero-Refetch State Sync**: Client subscribes to `/api/ws` and updates `nodesMap[nodeId]` directly upon `node.status_changed` and `node.executed`, recomputing visual DAG node states without calling `fetchDAG()`.
- **Real-Time Terminal Streaming**: Server pushes `node.log` events via `CanvasRuntimeBridge` (`dnk:canvas:events`), appending directly to client-side ring buffers (`nodeLogs[nodeId]`).
- **Async Broadcast Test Pattern**: In pytest with TestClient/mock WS, allow event loop ticks (`await asyncio.sleep(0.05)`) between connection and execution for background broker registration.
- **Reference**: `references/dag_canvas_reactive_websocket_streaming.md`.

## 🕸️ 33. Canvas Multi-Selection & Batch Operations Dock (Slice 20.4)
- **React Flow Marquee Selection**: Configure `selectionMode={SelectionMode.Partial}`, `selectionKeyCode="Shift"`, `multiSelectionKeyCode=['Shift', 'Meta', 'Control']`, and pane-click reset for seamless box/lasso multi-selection without drawer collisions.
- **Dual Selection State**: In Zustand store, track `selectedNodeIds: string[]` concurrently with `selectedNodeId: string | null` (single-node drawer inspector) to maintain backward compatibility.
- **Atomic Backend Batch Operations**: Implement atomic endpoints (`batch_stage_transition`, `batch_delete`, `batch_execute`) with single-pass incident edge pruning, single DAG topology recalculation, and single Obsidian disk sync.
- **Floating Batch Operations Dock**: Reveal `CanvasBatchOperationsDock` on `selectedNodeIds.length > 1` providing batch stage transition with gating/force toggle, swarm batch run, safety confirmation on delete, and deselect.
- **Reference**: `references/canvas_multi_selection_and_batch_operations.md`.

## 🕸️ 34. React Flow Drag-and-Drop, Snap-Back Prevention & Persistent Sync
- **Non-Destructive Node Selection**: Avoid rebuilding nodes via graph creation utilities in `setSelectedNodeId` / selection listeners; update only `selected: n.id === id` over existing in-memory nodes to prevent resetting live dragged coordinates.
- **Selection Conflict Removal**: Remove conflicting `onSelectionChange` handlers when `onNodesChange` is active to eliminate re-render race conditions during drag actions.
- **Defensive Position Normalization**: Harmonize disparate backend schemas (`pos_x`, `pos_y`, `position_x`, `position_y`, `position: { x, y }`) during both ingestion (`fetchGraph`) and graph rendering.
- **Interactive Element Isolation**: Apply the `nodrag` class to inner buttons, links, and form controls inside custom node components to isolate click interactions from canvas drag listeners.
- **Drag Stop Persistence**: Bind `onNodeDragStop` with rounded integer coordinates to the backend batch coordinates endpoint (`POST /api/v3/node_tasks/batch_positions`).
- **Reference**: `references/react_flow_node_dragging_and_position_sync.md`.

## 🕸️ 35. Node Tasks Live Artifacts, Diff Inspector & Verification Action Engine
- **REST Endpoints Specification**:
  - `GET /api/v3/node_tasks/{node_id}/artifacts`: Generates real git/file diff report (`NodeArtifactReport`) with additions, deletions, and per-file diffs.
  - `POST /api/v3/node_tasks/{node_id}/accept_artifacts`: Transitions task node to `TaskStatus.COMPLETED` (100% progress), updates stage to `COMPLETED`, unblocks dependent nodes via `recalculate_graph_dependencies`, triggers Obsidian note sync, and emits `node.executed`.
  - `POST /api/v3/node_tasks/{node_id}/reject_artifacts`: Resets task node to `TaskStatus.IN_PROGRESS` (50% progress), writes rejection reason to node execution logs, and broadcasts `node.status_changed`.
  - `POST /api/v3/node_tasks/{node_id}/run_verification`: Executes test-runner subprocess with `asyncio.wait_for(..., timeout=30.0)` timeout protection, appends stdout/stderr to terminal logs, and emits `node.verified`.
  - `POST /api/v3/node_tasks/{node_id}/clear_logs` and `DELETE /api/v3/node_tasks/{node_id}/logs`: Clears terminal log buffer.
- **React UI & Zustand Store Integration**:
  - `apps/web/store/nodeTasksStore.ts`: `nodeArtifacts`, `verificationResults`, `fetchNodeArtifacts`, `acceptNodeArtifacts`, `rejectNodeArtifacts`, `runNodeVerification`.
  - `apps/web/components/node-tasks/NodeTaskArtifactDiffViewer.tsx`: Diff visualization with syntax highlighting (`+` green, `-` red, `@@` purple), stats pills, and action controls.
  - `apps/web/components/node-tasks/NodeTaskDetailDrawer.tsx`: Tri-tab drawer navigation `[Огляд] | [Live Термінал] | [Diff Артефактів]`.
- **Critical Invariants & Pitfalls**:
  - **Singular Endpoint Routing**: Node item operations use `/api/v3/node_tasks/node` (singular) and `/api/v3/node_tasks/node/{id}`, NOT `/nodes`. Calling `/nodes` causes HTTP 404.
  - **Async Subprocess Termination**: Any process spawned for verification must explicitly terminate via `proc.kill()` and `await proc.wait()` on `asyncio.TimeoutError` to prevent orphaned background processes.
  - **Monorepo TypeScript Verification Invariant**: To avoid npm registry placeholder package conflicts with `npx tsc`, execute `./apps/web/node_modules/.bin/tsc --noEmit --project apps/web/tsconfig.json` or `npm --prefix apps/web exec tsc -- -p apps/web/tsconfig.json --noEmit`.
- **Reference**: `references/node_tasks_artifacts_and_diff_inspector.md`.

- `🕸️ 36. DAG Task Graph Multi-Tenant Project Partitioning & Graph Subgraph Isolation (Slice 1 & 2)`
- `📓 37. DAG Task Graph Obsidian Markdown Bidirectional Sync Engine (Slices 1 & 2)`
- **Multi-Tenant Partition Architecture**:
  - `ProjectInfo` Pydantic & TypeScript model (`id`, `name`, `slug`, `description`, `color`, `icon`, `is_active`, `tasks_count`, `created_at`) persisted to `data/projects.json`.
  - Node partitioning via `node.project_id: str = "dnk_core"`. Default projects: `dnk_core` (DNK Core), `m_craft` (M-Craft Studio), `brand_alpha` (Brand Alpha).
  - Backward compatibility: nodes without `project_id` or with empty string default to `"dnk_core"`.
- **Endpoints & Subgraph Edge Filtering Invariant**:
  - `GET /api/v3/node_tasks/projects`: Aggregates active task counts per project partition.
  - `POST /api/v3/node_tasks/projects`: Dynamic workspace/project registration.
  - `GET /api/v3/node_tasks/graph?project_id=<id>`: Subgraph query filtering.
  - **Edge Subgraph Filtering Law**: When filtering by `project_id`, edges MUST be pruned unless both `source` AND `target` belong to the partitioned node set (`e.source in valid_node_ids and e.target in valid_node_ids`). Dangling edges cause React Flow and auto-layout engine collapse.
- **Frontend Zustand Store & ProjectSwitcher (Slice 2)**:
  - Store fields: `projects: ProjectInfo[]`, `activeProjectId: string` (default `'dnk_core'`), `isProjectsLoading: boolean`.
  - Store actions: `fetchProjects()`, `setActiveProject(projectId)` (immediately calls `fetchGraph(projectId)`), `createProject(payload)`.
  - Node creation enrichment: `project_id: payload.project_id || get().activeProjectId || 'dnk_core'`.
  - Component: `ProjectSwitcherDropdown.tsx` with dark glassmorphism, project color pills, task counts, and inline project creation modal.
  - Verification: In monorepo root run `./apps/web/node_modules/.bin/tsc --noEmit --project apps/web/tsconfig.json` or `cd apps/web && npx tsc --noEmit`.
- **Reference**: `references/dag_canvas_multitenant_project_partitioning.md`.

## 📓 37. DAG Task Graph Obsidian Markdown Bidirectional Sync Engine (Slices 1 & 2)
- **ObsidianSyncEngine Architecture (`services/dnk_canvas_api/obsidian_sync_engine.py`)**:
  - `parse_markdown_note(file_path: Path)`: Parses YAML frontmatter (`id`, `title`, `stage`, `status`, `type`, `priority`, `progress`, `project_id`, `assigned_agent`, `target_module`, `dependencies`, `tags`).
  - **Soup Resilient Markdown Ingestion**: Fallback line-by-line key/value parsing when PyYAML encounters malformed human-edited frontmatter (tabs, unquoted colons, invalid delimiters).
  - **Soup Anti-Dangling Wikilinks Guard**: Auto-spawns stub `NodeType.IDEA` nodes (`#unresolved_dependency`) when dependencies reference nonexistent notes, preserving DAG topological integrity.
  - **Soup Acceptance Criteria Union**: Non-destructive boolean OR merge for completed status; newly discovered checklist items are appended without erasing existing criteria.
  - **Obsidian Wikilink Invariant**: Normalizes `[[node-id]]`, `[[node-id|Alias]]`, and raw `node-id` formats into canonical node identifiers.
  - **Acceptance Criteria Extraction**: Scans markdown body lines for checklist items (`- [ ]`, `- [x]`) and maps them to structured task criteria.
  - `sync_from_obsidian_vault(vault_dir: Path, project_id: Optional[str])`: Discovers newly added markdown notes, reconciles existing node attributes, reconstructs dependency edges with cycle detection guard (`NodeTaskGraphEngine.detect_cycle_with_new_edge`), and updates topological graph dependencies.
  - `sync_bidirectional(vault_dir: Path, project_id: Optional[str])`: Performs two-way reconciliation (Obsidian vault pull -> graph update -> markdown push) with unified telemetry reporting.
- **FastAPI Endpoints (`apps/api/routers/node_tasks_router.py`)**:
  - `POST /api/v3/node_tasks/sync_from_obsidian`: Pulls Obsidian markdown task notes into the DAG graph.
  - `POST /api/v3/node_tasks/sync_bidirectional`: Triggers full two-way state reconciliation between DAG graph and Obsidian Vault.
- **Frontend Zustand & UI 2-Way Sync Integration (Slice 2)**:
  - `apps/web/store/nodeTasksStore.ts`: Action `syncObsidianBidirectional` posts to `/api/v3/node_tasks/sync_bidirectional?project_id=...` and immediately triggers `await get().fetchGraph(activeProjectId)` on success so the React Flow canvas instantly re-renders newly imported/reconciled nodes and edges. Legacy `syncObsidian` remains as a typed backward-compatible alias.
  - `apps/web/components/node-tasks/NodeTaskGraphCanvas.tsx`: Header button replaced blocking `alert(...)` with rich non-blocking toast notifications (`showToast(...)`), dynamic spinning sync indicator (`animate-spin`), and status summaries (`imported`, `updated`, `exported`).
- **Verification Invariants**:
  - Backend: Run `.venv/bin/pytest tests/verification/test_node_tasks_obsidian_sync.py -v` (100% Green pass required).
  - Frontend: Run `./apps/web/node_modules/.bin/tsc --noEmit --project apps/web/tsconfig.json` (0 errors required).
- **Reference**: `references/dag_canvas_obsidian_bidirectional_sync_engine.md`.

## 🕸️ 38. DAG Task Graph Persistence Hygiene, Test Isolation & Conversational Intake Guard
- **Root Cause of Graph Bloat**:
  - Direct endpoint execution during `pytest` without storage isolation mutates the active development/production `data/node_task_graph.json` database via `NodeTaskPersistenceManager.get_instance()`.
  - Unconditional node creation in `POST /api/v3/node_tasks/chat_intake` turns conversational questions (e.g. "Why are there so many nodes?") into phantom task nodes (`task-chat-*`).
- **Test Persistence Isolation Invariant (`tmp_path`)**:
  - In all integration and router tests touching `NodeTaskPersistenceManager`, inject a pytest fixture using `tmp_path` to point `NodeTaskPersistenceManager._instance` to an isolated temporary file, restoring the original instance on teardown.
  - Verify baseline immutability: `git diff --exit-code data/node_task_graph.json` must remain 100% clean after running tests.
- **Conversational Intake Intent Guard (`is_conversational_inquiry` & 4-Intent Routing)**:
  - `services/dnk_node_tasks/conversational_intake.py`: Disambiguate user intent across 4 discrete pathways (`inquiry`, `auto_layout`, `execute_task`, `task_creation`) before mutating the DAG.
  - Informational questions (`inquiry`) and UI complaints return technical explanations without spawning graph nodes.
  - Execution commands (`execute_task`) trigger live agent worker execution (`action: "execute"`, `target_node_id`) instead of duplicating task nodes or giving simulated progress text.
  - Layout requests (`auto_layout`) and task creation trigger server-side topological auto-layout (`NodeTaskGraphEngine.compute_auto_layout()`), assigning non-overlapping coordinates (columns X +440px, rows Y +280px) and invoking `autoLayoutDAG()` on frontend.
- **Reference**: `references/dag_canvas_persistence_isolation_and_conversational_intake.md`.

## 🕸️ 39. Interactive Canvas-to-Swarm Triggers, Live Post-Tool Hook HUD & React Flow SSOT Bridge
- **Live Zero-Code Dashboard via Post-Tool Hook**:
  - `scripts/system/hermes_post_tool_hook.py`: Dispatches every tool completion into `VisualCanvasControlEngine().record_live_tool_execution(...)`.
  - Increments HUD call budget (`tools_count`), updates runtime status badge, moves mutating nodes (`write_file`, `patch`) to blue/in_progress (`color="5"`), and sets passing tests to green/done (`color="4"`).
- **Two-Way Interactive Canvas-to-Swarm Triggers**:
  - `poll_and_execute_canvas_triggers`: Scans Obsidian Canvas cards for `- [x] Run Tests` and `- [x] Dispatch Worker: <agent>`.
  - Executes real test suites (`bash scripts/verify_all.sh`) or dispatches domain agents via `dnk_swarm_dispatch`, stamping `[completed @ timestamp]`.
  - CLI daemon mode: `--poll-triggers` and `--watch <interval>`.
- **Bidirectional SSOT Bridge: Obsidian Canvas <-> React Flow**:
  - `canvas_to_react_flow(canvas_path)` and `react_flow_to_canvas(rf_data, output_path)` maintain 1:1 parity between native Obsidian `.canvas` files and Web React Flow graphs (`apps/web`, `apps/api`).
  - Production REST router: `apps/api/routers/canvas_bridge.py` (`/api/v1/canvas/bridge/obsidian`, `react-flow-to-canvas`, `convert/*`, `merge` [OCC 3-way merge], `trigger-check`, `sync-master`).
  - Real-time Bidirectional WebSocket Stream & Reactive FileWatcher: `apps/api/routers/canvas_bridge.py` (`/api/v1/canvas/bridge/ws`) supporting `INITIAL_STATE`, `ping/pong`, `refresh`, `trigger_check`, `update`, and `merge` (OCC 3-way merge between base, incoming, and disk state) persistence actions with background `mtime` filewatcher pushing `CANVAS_UPDATE` on external edits and echo suppression on client saves.
  - Client-Side Resilience & REST Fallback: `apps/web/store/canvasStore.ts` degrades seamlessly to REST `canvasApiClient.exportToObsidianCanvas` if WebSocket is down; strictly enforces relative `./docs/notes` path hygiene.
  - Shared TypeScript contracts: `apps/web/types/canvasBridge.ts` (`ObsidianCanvasNode`, `ReactFlowNode`, `CanvasSyncRequest`, `CanvasSyncResponse`).
  - Worker tag sanitization: worker names in markdown cards (`**Worker**: <name>`) must be stripped of backticks (`.strip().strip("\`")`) before badge lookup.
- **Reference**: `references/interactive_canvas_triggers_and_react_flow_bridge.md`.

## 🕸️ 40. Live Swarm HUD, Worker Color Mapping & WebSocket Broadcast Engine
- **Real-Time Agent Telemetry on Visual Canvas**:
  - `apps/api/routers/canvas_bridge.py`: `CanvasBridgeConnectionManager` manages WebSocket clients partitioned by `canvas_path` or global HUD listeners.
  - Streaming method `broadcast_swarm_event()` propagates agent execution status without triggering heavy disk sync or full React Flow reloads.
- **SSOT Swarm Worker Color Palette (`SWARM_WORKER_COLORS`)**:
  - `core/orchestrator/visual_canvas_control.py`: Centralized palette linking agents (`gerych_prime`, `antigravity_mentor`, `gerych_builder`, `dnk_dev_fullstack`, `dnk_shopify`, `dnk_video_ai_creator`, `gerych_auditor`, `dnk_security_guard`, `herich_librarian`) to JSON Canvas color integers (`1` to `6`), UI Hex values, and emojis.
- **REST & WebSocket Ingress**:
  - REST: `POST /api/v1/canvas/bridge/events/swarm` (and `/swarm-hud` alias) accepts worker progress with optional `update_canvas_disk` flag.
  - WebSocket: action `swarm_event` enables bidirectional in-browser debugging and client dispatch.
  - Generates dynamic visual progress bars (e.g. `██████▒▒▒▒ 65%`).
- **Reference**: `references/live_swarm_hud_and_websocket_broadcaster.md`.

## 🕸️ 41. Critical Path Method (CPM), Float/Slack & Visual Bottleneck Heatmap
- **Algorithmic Graph CPM (`NodeTaskGraphEngine.compute_critical_path`)**:
  - Computes task duration based on priority/metadata (Completed = 0h, Critical = 8h, High = 5h, Medium = 3h, Low = 1.5h).
  - Two-pass traversal: Forward Pass computes Earliest Start (`ES`) and Earliest Finish (`EF`); Backward Pass computes Latest Start (`LS`) and Latest Finish (`LF`).
  - Total Float / Slack (`LS - ES`): nodes with `Slack <= 0.001` form the critical execution chain.
  - Detects critical edges (`EF(u) == ES(v)`) and ranks bottlenecks by impact score (`out_degree * duration`).
- **API Endpoint & Zustand Synchronization**:
  - `GET /api/v3/node_tasks/critical_path`: Returns status, critical node IDs, critical edge IDs, total duration, and bottleneck rankings.
  - `nodeTasksStore.ts`: Controls `showCriticalPath`, fetches metrics on demand, and feeds reactive states to canvas components.
- **Visual Contrast & Dimming Heatmap**:
  - `CustomTaskNode.tsx`: Critical nodes render blazing rose-neon ring (`ring-2 ring-rose-500 border-rose-500 shadow-[0_0_24px_rgba(244,63,94,0.45)]`) and `CRITICAL PATH (Dur: Xh | Slack: 0h)` badge. Non-critical nodes dim to `opacity-40 saturate-50` for high contrast.
  - `CustomDependencyEdge.tsx`: Critical edges stroke in `#f43f5e` (3px) with pulsing flame marker.
  - `NodeTaskGraphCanvas.tsx`: Toolbar toggle `🔥 Critical Path` and floating analytical summary banner.
- **Reference**: `references/dag_canvas_critical_path_method_and_heatmap.md`.












