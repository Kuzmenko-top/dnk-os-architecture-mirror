<!-- --- DNK-MRH-HEADER ---
mrh_id: "docs/tech/sota_assimilation/capcut/audits/results/canvas_rendering_analysis.md"
purpose: "Deep-Dive Reverse Engineering Analysis of CapCut AI Design Canvas Rendering Engine."
canonical_source: true
alters_files: []
triggers_tasks: []
status: "Completed"
version: "1.0.0"
updated_at: "2026-09-02"
author: "DNK-e.com Maksym (Gerych Prime)"
--- END DNK-MRH-HEADER --->

# 🎨 CapCut AI Design: Canvas Rendering Engine Architecture

## 1. Executive Summary & Verification
During **CAPCUT-CANVAS-AUDIT-001**, the runtime architecture of `https://www.capcut.com/ai-design` was reverse-engineered via live browser CDP inspection, DOM tree analysis, and Scene Graph extraction.

### Key Architectural Discovery:
CapCut AI Design combines a **3-Tier Stacked HTML5 Canvas Architecture** driven by **Konva.js (v8.x+)** as the primary 2D Scene Graph Engine, coupled with offscreen canvas buffers for glyph measurement and WebAssembly/WebGL pipelines for generative AI inpainting and background cutouts.

---

## 2. Multi-Tier Layer Composition

The DOM container `.render-root` inside `#graphic-editor-render` instantiates 3 synchronized HTML5 Canvas layers (scaled at 2x Retina backing store, e.g. `3360 x 1924 px` backing store for a `1680 x 962 px` viewport):

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Top Canvas (z-index: 20)                        │
│   Selection Gizmos, Transformers, Resize Anchors, Smart Guidelines     │
├────────────────────────────────────────────────────────────────────────┤
│                       Middle Canvas (z-index: 0)                       │
│    Active Konva Stage: Feature Layer, CutOuts, Inpaint, Artboards      │
├────────────────────────────────────────────────────────────────────────┤
│                       Bottom Canvas (z-index: -1)                      │
│     Background Layer, Canvas Bounds Guide, Grid, Offscreen Cache       │
└────────────────────────────────────────────────────────────────────────┘
```

### Purpose of 3-Tier Layering:
1. **Performance Isolation**: Gizmo manipulations (drag, rotate, scale) redraw only the Top Canvas without triggering re-rendering of complex vector/bitmap graphics on the Middle Canvas.
2. **Hit Testing Optimization**: Hit detection delegates between pointer events on the top interaction group and Konva's internal color-key hit canvas buffer.

---

## 3. Extracted Konva Scene Graph Hierarchy

The live scene graph extracted from `window.Konva.stages[0]` reveals the following structure:

```
Konva.Stage (1680 x 962)
├── Layer 0: "MainLayer" (Background & Canvas Bounds)
│   ├── Rect: "MainBackground-Background" (1680x962)
│   ├── Group: Artboard Viewport (Transform matrix: [0.2, 0, 0, 0.2, 482, 350.8])
│   ├── Rect: "stage-debug-safe-zone" (Export Safe Margins)
│   └── Rect: "stage-debug-content-bounds" (Artboard Boundaries)
├── Layer 1: "BackgroundLayer" (Color & Texture Buffer)
│   └── Shape: Background Canvas Filler
├── Layer 2: "FeatureLayer" (AI Core & Interactive Modules)
│   ├── Group: "Interactive" (Active Node Selection Group)
│   ├── Group: "imageCutOut" (AI Background Removal & Alpha Masking)
│   ├── Group: "imageContainerCutOut" (Vector Clipping Paths & Smart Containers)
│   ├── Group: "gridCutOut" (Magnetic Snapping & Layout Grids)
│   ├── Group: "canvasBgImageCutOut" (Generative Background Image Layer)
│   ├── Group: "ruler" (Viewport Rulers: Top 20px, Left 20px, Corner 20x20px)
│   ├── Group: "inpaintEditor" (Generative AI Inpainting Brush & Area Mask)
│   └── Group: "imageFrameEditor" (Smart Vector Frames & Aspect Ratio Constraints)
└── Layer 3: "GizmoLayer"
    └── Transformer: Selection box, rotation anchor, 8-point scaling handles
```

---

## 4. Offscreen Buffers & Text Engine

- **Text Measurement Buffer (`#offscreenCanvas`)**: Dedicated offscreen canvas (`750 x 81 px`) used for exact font metrics, text bounding boxes, and Kerning calculation before DOM/Konva commit.
- **ProseMirror / Tiptap Integration**: Rich typography and prompt input utilize a hybrid overlay architecture where inline editing is handled via `contenteditable` ProseMirror instances synced directly to Konva Text nodes.

---

## 5. Architectural Implications for DNK OS Canvas Engine

1. **Adopt Konva.js / Multi-layer HTML5 Canvas**: Validates our DNK OS Canvas choice. Konva provides robust scene-graph abstractions while allowing hardware-accelerated 2D transforms.
2. **Adopt Isolated Gizmo Layer**: Keep selection handles and guidelines on a distinct top layer to achieve 60 FPS interactions regardless of document complexity.
3. **Structured AI Node Architecture**: Mimic CapCut's specialized group architecture (`imageCutOut`, `inpaintEditor`, `canvasBgImageCutOut`) for seamless integration with DNK AI Video and Image generation workers.
