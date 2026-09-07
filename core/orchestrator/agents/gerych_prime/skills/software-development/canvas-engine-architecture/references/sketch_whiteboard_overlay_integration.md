# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/canvas-engine-architecture/references/sketch_whiteboard_overlay_integration.md"
# purpose: "Technical blueprint and mathematical projection for transparent SVG drawing overlay over reactive node canvases with shared Undo/Redo history."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Transparent SVG Sketch/Whiteboard Overlay Integration

This reference describes the architectural pattern, mathematical projection, and state synchronization rules for overlaying a highly performant freehand whiteboard drawing layer directly on top of an infinite, zoomable structured node canvas (such as React Flow / `@xyflow/react`).

---

## 📐 1. Dynamic Coordinate Projection (Client to Canvas Space)

When drawing on a transparent SVG or Canvas layer positioned over a zoomable board, screen-space cursor coordinates (`clientX, clientY`) must be projected into the zoomed and panned space of the canvas. 

Using `@xyflow/react`'s `useViewport()` hook, which returns `{ x: number, y: number, zoom: number }`:

```typescript
import { useViewport } from '@xyflow/react';

const viewport = useViewport(); // SSOT translation matrix of the parent stage

const getCanvasCoords = (e: React.MouseEvent<SVGSVGElement>, svgElement: SVGSVGElement | null) => {
  if (!svgElement) return { x: 0, y: 0 };
  const rect = svgElement.getBoundingClientRect();
  
  // Projection formula:
  return {
    x: (e.clientX - rect.left - viewport.x) / viewport.zoom,
    y: (e.clientY - rect.top - viewport.y) / viewport.zoom,
  };
};
```

---

## 🚀 2. 60 FPS SVG Transform & Scale Syncing

Instead of manually updating the position and dimensions of every individual drawn stroke or shape upon pan/zoom (which causes severe lag and O(N) calculations), wrap the entire vector workspace in a single coordinate-translated SVG group (`<g>`):

```tsx
<svg 
  ref={svgRef}
  className="absolute inset-0 w-full h-full pointer-events-auto"
  onMouseDown={handleMouseDown}
  onMouseMove={handleMouseMove}
  onMouseUp={handleMouseUp}
>
  <g transform={`translate(${viewport.x}, ${viewport.y}) scale(${viewport.zoom})`}>
    {/* All shapes render in pure canvas-space coordinates [x, y] with 0 translation/scale logic! */}
    {elements.map((el) => {
      if (el.type === 'pencil') {
        const d = el.points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
        return <path key={el.id} d={d} stroke={el.strokeColor} strokeWidth={el.strokeWidth} fill="none" />;
      }
      if (el.type === 'rect') {
        return <rect key={el.id} x={el.x} y={el.y} width={el.width} height={el.height} stroke={el.strokeColor} fill={el.fillColor} />;
      }
      // Other shapes...
    })}
  </g>
</svg>
```

---

## ⚡ 3. High-Performance Pointer Events Interception

When the whiteboard sketching mode is turned **OFF**, we must let all hover, click, and drag events fall through directly to the living interactive node graphs beneath. When turned **ON**, we capture events to draw on our overlay.

Implement a dual-state `pointer-events` class binding on the root SVG layer:

```tsx
const svgClass = isWhiteboardActive 
  ? "absolute inset-0 w-full h-full pointer-events-auto cursor-crosshair select-none z-30" 
  : "absolute inset-0 w-full h-full pointer-events-none z-0";
```

### Pointer Events Layering Checklist:
1. **Sketch Mode Active (`isWhiteboardActive === true`)**:
   - SVG layer: `pointer-events-auto`.
   - Toolbars: `pointer-events-auto` with higher `z-index` (e.g., `z-40`).
   - Interaction is captured for drawing.
2. **Sketch Mode Inactive (`isWhiteboardActive === false`)**:
   - SVG layer: `pointer-events-none`.
   - React Flow nodes / Canvas: fully interactive, user can select, double click, type, and drag nodes.

---

## 🔄 4. Consolidated Undo/Redo & Cohesive Transaction History

To prevent disjointed user workflows (where drawing an arrow and moving a node require separate, non-synchronous Undo actions), merge `whiteboardElements` into the master canvas state history snapshot ring-buffer:

### State Interface Expansion:
```typescript
interface CanvasHistorySnapshot {
  nodes: Node[];
  edges: Edge[];
  whiteboardElements: WhiteboardElement[]; // Merged into the SAME historical snapshot!
}
```

### Synchronized History Manager:
```typescript
export const useCanvasStore = create<CanvasState>((set, get) => ({
  nodes: [],
  edges: [],
  whiteboardElements: [],
  history: [],
  historyIndex: -1,

  pushHistory: () => {
    const { nodes, edges, whiteboardElements, history, historyIndex } = get();
    const cleanHistory = history.slice(0, historyIndex + 1);
    
    set({
      history: [...cleanHistory, { nodes, edges, whiteboardElements }],
      historyIndex: cleanHistory.length
    });
  },

  undo: () => {
    const { history, historyIndex } = get();
    if (historyIndex <= 0) return;
    
    const prevIndex = historyIndex - 1;
    const snapshot = history[prevIndex];
    
    set({
      nodes: snapshot.nodes,
      edges: snapshot.edges,
      whiteboardElements: snapshot.whiteboardElements,
      historyIndex: prevIndex
    });
  }
}));
```

---

## 💾 5. Double-Serialization & JSON Canvas Compatibility

When exporting the canvas workspace to standard JSON Canvas v1.0, embed freehand sketching layers inside a specialized `whiteboard` metadata block or custom background element coordinates to ensure the entire view-state is easily restored by downstream agents or collaborative clients.
