# Mind Map AI Auto-Clusterization Patterns

## Core Architecture
- **K-Means on Text/Vector Embeddings**: Dynamic cluster count selection heuristic:
  `k = min(5, max(2, len(nodes) // 3))`
  Extracts embeddings via pgvector or deterministic bag-of-words fallback.
- **Bounding Box & Grid Positioning**:
  Calculates cluster bounding box with margin (`x_min - padding`, `y_min - padding`, `width`, `height`).
  Reposition nodes inside the cluster area in a 2-3 column grid to avoid overlap.
- **Background Container Node**:
  `MindMapClusterNode` is rendered as a custom background node with lower z-index or translucent container backdrop.
  Has properties: `cluster_id`, `name`, `color`, `bounding_box: { width, height }`.
- **Canvas Store State Integration**:
  Add `isClustering`, `clusterMetadata` to Zustand store.
  Provide both `autoClusterNodes` and `autoClusterMindMap` aliases.
  Store implementation must integrate with undo/redo history (`pushHistory`) and delta queue (`queueDelta`).
- **LSP / TypeScript Strictness**:
  Ensure all repositioned node mapping explicitly types element references to avoid implicit `any` mismatches in React Flow nodes array.
