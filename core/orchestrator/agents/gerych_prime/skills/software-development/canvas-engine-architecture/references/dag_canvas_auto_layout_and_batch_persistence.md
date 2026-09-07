# DAG Canvas Auto-Layout with Barycenter Heuristic & Batch Positions Persistence

## 1. Overview
Automated DAG topological layout for node task graphs (`@xyflow/react` / ReactFlow) that organizes task nodes from left to right based on dependency hierarchy, minimizes edge crossings via a Barycenter heuristic, and atomically persists the newly calculated coordinates to the backend in a single request.

---

## 2. Core Architectural Patterns

### A. Topological Depth & Layering (Rank Assignment)
1. **Dependency Normalization**: Extract both forward prerequisites (`depends_on`, `spawns_from`) and blocking targets (`blocks`).
2. **In-Degree Calculation**: Nodes with no incoming dependencies (`in_degree === 0`) are assigned to Layer 0 (roots).
3. **Longest-Path Layer Assignment**:
   For any edge $u \to v$, $\text{rank}(v) \ge \text{rank}(u) + 1$.
   Nodes at the same depth share the same horizontal coordinate ($X$).

### B. Barycenter Edge-Crossing Minimization Heuristic
Within each layer $L > 0$, order nodes vertically by the average $Y$-coordinate of their upstream parent nodes in layer $L-1$:
$$B(v) = \frac{1}{|P(v)|} \sum_{u \in P(v)} \text{position}_Y(u)$$
- If a node has no upstream parents in $L-1$, preserve its original relative ordering or priority rank.
- Within Layer 0 (roots), sort by priority weight: `critical` (0) $\to$ `high` (1) $\to$ `medium` (2) $\to$ `low` (3).

### C. Discrete Spatial Grid Constants
- **Horizontal Step**: $\Delta X = 380\text{px}$ (accommodates 320px node width + 60px inter-node wire corridor).
- **Vertical Step**: $\Delta Y = 190\text{px}$ (accommodates node height + 40px spacing).
- **Base Offset**: $X_0 = 100\text{px}, Y_0 = 100\text{px}$.

---

## 3. Atomic Batch Persistence Contract

### FastAPI Router (`POST /api/v3/node_tasks/batch_positions`)
Instead of issuing individual `PATCH /node_tasks/{id}` requests per node (which triggers $O(N)$ HTTP round-trips and repeated file disk flushes), provide a batch coordinate ingestion endpoint:

```python
class NodePosition(BaseModel):
    x: float
    y: float

class BatchPositionsRequest(BaseModel):
    positions: Dict[str, NodePosition]

@router.post("/batch_positions")
def update_node_positions(payload: BatchPositionsRequest):
    graph = load_graph()
    updated = 0
    for node_id, pos in payload.positions.items():
        if node_id in graph.nodes:
            graph.nodes[node_id].position = {"x": pos.x, "y": pos.y}
            updated += 1
    save_graph(graph)
    return {"status": "ok", "updated_nodes": updated}
```

---

## 4. Zustand Store & ReactFlow Integration Pattern

```typescript
autoLayoutDAG: async () => {
  const { nodes, edges } = get();
  if (nodes.length === 0) return;

  // 1. Calculate topological layers
  const layers = computeTopologicalLayers(nodes, edges);

  // 2. Order within layers using Barycenter heuristic
  const newPositions: Record<string, { x: number; y: number }> = {};
  layers.forEach((layerNodes, depth) => {
    const sorted = sortLayerByBarycenter(layerNodes, depth, newPositions, edges);
    sorted.forEach((node, index) => {
      newPositions[node.id] = {
        x: 100 + depth * 380,
        y: 100 + index * 190,
      };
    });
  });

  // 3. Optimistic local update in Zustand store
  const updatedNodes = nodes.map((n) => ({
    ...n,
    position: newPositions[n.id] || n.position,
  }));
  set({ nodes: updatedNodes });

  // 4. Batch persistence to API
  await api.post('/api/v3/node_tasks/batch_positions', { positions: newPositions });
}
```

---

## 5. UI Canvas Toolbar Integration
- Disable button while computing (`disabled={isLayingOut}`).
- Trigger smooth camera repositioning after layout:
  ```typescript
  fitView({ duration: 500, padding: 0.2 });
  ```
- Surface visual feedback via toast (`✨ Топологію графа впорядковано (${count} вузлів)`).
