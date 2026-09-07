# React Flow Node Dragging, Snap-Back Prevention & Persistent Sync

## 1. Context & Architecture
In canvas environments based on React Flow (@xyflow/react), node dragging must be smooth, persistent across sessions, and resistant to coordinate reset / snap-back bugs caused by component re-renders or reactive store synchronization.

## 2. Core Pitfalls & Root Causes

### A. The Selection Rebuild Snap-Back Pitfall
- **Symptom**: When a user drags a node or clicks on it to open an inspector drawer, the node instantly snaps back to its initial/previous coordinates.
- **Root Cause**: The store's selection action (e.g. `setSelectedNodeId`) invokes a graph rebuild function (e.g. `buildRFNodesAndEdges`) from initial task models. Because in-memory drag movement updates React Flow's internal state first, rebuilding `rfNodes` replaces the current coordinates with the stale coordinates from the initial model.
- **Solution**: Selection must be non-destructive. Only update the `selected` boolean on existing nodes:
  ```ts
  setSelectedNodeId: (id) => {
    set((state) => ({
      selectedNodeId: id,
      rfNodes: state.rfNodes.map((n) => ({
        ...n,
        selected: n.id === id,
      })),
    }));
  }
  ```

### B. Conflicting Selection Event Handlers
- **Symptom**: Uncontrolled selection event loops and erratic node snapping during drag initiation.
- **Root Cause**: Using `onSelectionChange` on `<ReactFlow>` alongside `onNodesChange` and node click listeners causes duplicate and conflicting state dispatches during drag operations.
- **Solution**: Rely on React Flow's `onNodesChange` and direct `onNodeClick`. Remove redundant `onSelectionChange` handlers that trigger store updates during drag gestures.

### C. Property Mismatch & Position Normalization
- **Symptom**: Nodes render at `(0, 0)` or stack on top of each other despite having database coordinates.
- **Root Cause**: Backend models use `pos_x` / `pos_y` or `position_x` / `position_y`, while React Flow nodes expect `{ position: { x, y } }`. Ingestion and conversion routines that only check one variation drop valid coordinates.
- **Solution**: Normalize position defensively across all accessors:
  ```ts
  const rawPos = (taskNode as any).position;
  let posX = rawPos?.x ?? (taskNode as any).position_x ?? (taskNode as any).pos_x ?? 0;
  let posY = rawPos?.y ?? (taskNode as any).position_y ?? (taskNode as any).pos_y ?? 0;
  ```

### D. Custom Node Interactive Element Interception
- **Symptom**: Clicking buttons, dropdowns, or checkboxes inside a custom node accidentally initiates a canvas drag operation or drops selection.
- **Root Cause**: React Flow interprets mouse-down events on unflagged child elements as drag starts.
- **Solution**: Add the `nodrag` class to all buttons, inputs, links, and interactive elements inside custom nodes:
  ```tsx
  <button
    onClick={(e) => {
      e.stopPropagation();
      handleAction();
    }}
    className="nodrag flex items-center ..."
  >
    Action
  </button>
  ```

## 3. Persistent Drag-and-Drop Pipeline

1. **Enable Canvas Dragging**: Explicitly pass `nodesDraggable={true}` to `<ReactFlow>`.
2. **Hook Drag Stop Event**:
   ```tsx
   const handleNodeDragStop = useCallback(
     (_event: unknown, node: Node) => {
       const roundedX = Math.round(node.position.x);
       const roundedY = Math.round(node.position.y);
       saveNodePosition(node.id, roundedX, roundedY);
     },
     [saveNodePosition]
   );
   ```
3. **Store Ingestion & Persistence**:
   - `saveNodePosition(id, x, y)` updates both the local store (`nodesMap`, `rfNodes`) and dispatches to the backend batch coordinates endpoint (`POST /api/v3/node_tasks/batch_positions` with `{ positions: [{ id, pos_x, pos_y }] }`).
