# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/canvas-engine-architecture/references/canvas_multi_selection_and_batch_operations.md"
# purpose: "Technical reference for React Flow multi-selection, lasso/box selection, and atomic batch operations."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime"
# --- END DNK-MRH-HEADER ---

# Canvas Multi-Selection & Batch Operations Reference (Slice 20.4)

## 1. React Flow Multi-Selection Configuration
To enable box/lasso multi-selection alongside single node inspection without gesture conflicts:
```tsx
import { SelectionMode } from '@xyflow/react';

<ReactFlow
  selectionMode={SelectionMode.Partial}
  selectionKeyCode="Shift"
  multiSelectionKeyCode={['Shift', 'Meta', 'Control']}
  onSelectionChange={({ nodes }) => {
    const ids = nodes.map((n) => n.id);
    setSelectedNodeIds(ids);
  }}
  onPaneClick={() => {
    setSelectedNodeIds([]);
    setSelectedNodeId(null);
  }}
  ...
/>
```

## 2. Zustand Store Selection Dual-Tracking Pattern
Maintain backwards compatibility with existing single-node inspection drawers while enabling multi-node batch operations:
```typescript
interface NodeTasksState {
  selectedNodeId: string | null;      // Single-node inspector drawer target
  selectedNodeIds: string[];          // Multi-selection array
}

// In buildRFNodesAndEdges:
selected: selectedIds.includes(taskNode.id)

// In onNodesChange:
if (change.type === 'select') {
  set((s) => ({
    selectedNodeIds: change.selected
      ? Array.from(new Set([...s.selectedNodeIds, change.id]))
      : s.selectedNodeIds.filter((id) => id !== change.id),
  }));
}
```

## 3. Node Click Multi-Selection Protection
In custom nodes (`CustomTaskNode.tsx`), ensure clicking a node that is already part of a multi-selection does not immediately collapse the selection unless clicked without modifiers:
```typescript
const isMultiSelected = selectedNodeIds.length > 1 && selectedNodeIds.includes(id);

onClick={(e) => {
  if (e.shiftKey || e.metaKey || e.ctrlKey) {
    e.stopPropagation();
    const next = selectedNodeIds.includes(id)
      ? selectedNodeIds.filter((x) => x !== id)
      : [...selectedNodeIds, id];
    setSelectedNodeIds(next);
    setSelectedNodeId(next.length === 1 ? next[0] : null);
    return;
  }
  if (!isMultiSelected) {
    setSelectedNodeId(id);
    setSelectedNodeIds([id]);
  }
}}
```

## 4. Backend Atomic Batch Endpoints Invariants
Avoid N individual updates, N graph recalculations, and N disk syncs:
1. `POST /api/v3/node_tasks/batch_stage_transition`:
   - Validates transition gating per node (`can_transition(current, target)` unless `force=True`).
   - Updates all valid nodes in-memory.
   - Triggers a single `_recalculate_graph_topology()`.
   - Performs a single Obsidian sync / disk persistence write.
   - Emits a WebSocket broadcast or returns `{ status: "success", updated_ids: [...], skipped: [...] }`.
2. `POST /api/v3/node_tasks/batch_delete`:
   - Removes all incident edges (both `source` and `target` in target IDs) in a single pass.
   - Removes target nodes from graph.
   - Recalculates topology and syncs once to storage.
3. `POST /api/v3/node_tasks/batch_execute`:
   - Validates node IDs.
   - Dispatches autonomous swarm execution tasks in the background for each node.
