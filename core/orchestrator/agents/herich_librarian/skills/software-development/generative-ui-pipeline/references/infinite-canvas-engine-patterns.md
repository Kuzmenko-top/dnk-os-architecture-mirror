# Infinite Canvas Engine & Viewport Culling Patterns

Interactive Infinite Canvas Engine architecture combining React Flow (XYFlow) for frontend visual node rendering, Zustand for client state management, Viewport Culling for performance optimization, and FastAPI for backend graph topology validation (Kahn's algorithm cycle detection and DAG topological sorting).

## 1. Viewport Culling Math & Formula

Viewport culling filters out nodes that sit outside the user's current visible screen coordinates, keeping rendering fast even with thousands of nodes in the graph.

```typescript
// apps/web/utils/viewportCulling.ts
import { Node, Viewport } from 'reactflow';

export function cullNodesToViewport(
  nodes: Node[],
  viewport: Viewport,
  bufferSize: number = 100,
  screenDimension?: { width: number; height: number }
): Node[] {
  const { x, y, zoom } = viewport;
  const safeZoom = zoom <= 0 ? 1 : zoom;
  
  const screenWidth = screenDimension?.width || (typeof window !== 'undefined' ? window.innerWidth : 1920);
  const screenHeight = screenDimension?.height || (typeof window !== 'undefined' ? window.innerHeight : 1080);

  // Calculate visible bounds in canvas space
  const visibleXStart = -x / safeZoom;
  const visibleXEnd = (-x + screenWidth) / safeZoom;
  const visibleYStart = -y / safeZoom;
  const visibleYEnd = (-y + screenHeight) / safeZoom;

  return nodes.filter((node) => {
    const nodeX = node.position.x;
    const nodeY = node.position.y;
    const nodeWidth = node.width || 200;
    const nodeHeight = node.height || 150;

    return (
      nodeX + nodeWidth >= visibleXStart - bufferSize &&
      nodeX <= visibleXEnd + bufferSize &&
      nodeY + nodeHeight >= visibleYStart - bufferSize &&
      nodeY <= visibleYEnd + bufferSize
    );
  });
}
```

## 2. Zustand Store for Canvas State Management

```typescript
// apps/web/store/canvasStore.ts
import { create } from 'zustand';
import { Node, Edge, Viewport } from 'reactflow';

interface CanvasState {
  nodes: Node[];
  edges: Edge[];
  viewport: Viewport;
  selectedNodeIds: string[];
  collaboration: {
    cursors: Record<string, { x: number; y: number }>;
    selections: Record<string, string[]>;
  };

  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  setViewport: (viewport: Viewport) => void;
  addNode: (node: Node) => void;
  updateNode: (nodeId: string, data: any) => void;
  removeNode: (nodeId: string) => void;
  addEdge: (edge: Edge) => void;
  removeEdge: (edgeId: string) => void;
}

export const useCanvasStore = create<CanvasState>((set) => ({
  nodes: [],
  edges: [],
  viewport: { x: 0, y: 0, zoom: 1 },
  selectedNodeIds: [],
  collaboration: { cursors: {}, selections: {} },

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setViewport: (viewport) => set({ viewport }),

  addNode: (node) => set((state) => ({ nodes: [...state.nodes, node] })),
  updateNode: (nodeId, data) =>
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === nodeId ? { ...node, ...data } : node
      ),
    })),
  removeNode: (nodeId) =>
    set((state) => ({
      nodes: state.nodes.filter((node) => node.id !== nodeId),
      edges: state.edges.filter(
        (edge) => edge.source !== nodeId && edge.target !== nodeId
      ),
    })),
  addEdge: (edge) => set((state) => ({ edges: [...state.edges, edge] })),
  removeEdge: (edgeId) =>
    set((state) => ({
      edges: state.edges.filter((edge) => edge.id !== edgeId),
    })),
}));
```

## 3. Python Graph Topology & Cycle Detection (Kahn's Algorithm)

```python
# apps/api/services/canvas_engine_service.py
from collections import defaultdict, deque
from typing import List, Dict, Any

class CanvasEngineService:
    @staticmethod
    def validate_graph(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
        node_ids = {str(n["id"]) for n in nodes if "id" in n}
        adj_list = defaultdict(list)
        in_degree = defaultdict(int)

        for nid in node_ids:
            in_degree[nid] = 0

        for edge in edges:
            src, tgt = str(edge.get("source", "")), str(edge.get("target", ""))
            if src in node_ids and tgt in node_ids:
                adj_list[src].append(tgt)
                in_degree[tgt] += 1

        queue = deque([nid for nid in node_ids if in_degree[nid] == 0])
        topological_order = []

        while queue:
            curr = queue.popleft()
            topological_order.append(curr)
            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        has_cycle = len(topological_order) < len(node_ids)
        return {
            "valid": not has_cycle,
            "has_cycle": has_cycle,
            "topological_order": topological_order,
        }
```

## 4. Key Invariants & Pitfalls

- **Comment Headers in TypeScript / TSX**: All Machine-Readable Headers (MRH) or top comments in `.ts` / `.tsx` files MUST start with `//`, NEVER `#`. Using `#` causes `Invalid character` compiler errors in Next.js / TypeScript.
- **Node Dimension Handling**: Default to `width: 200` and `height: 150` in culling calculations when `node.width` or `node.height` are not explicitly defined in React Flow node state.
- **Cascading Node Deletion**: Removing a node from `canvasStore` MUST clean up all connected edges (`source !== nodeId && target !== nodeId`) to avoid orphaned edges in graph execution.
