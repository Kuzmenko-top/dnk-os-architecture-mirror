# --- DNK-MRH-HEADER ---
# mrh_id: "references/dag_canvas_critical_path_method_and_heatmap.md"
# purpose: "Reference architecture & recipes for Critical Path Method (CPM), Slack calculation, bottleneck detection, and React Flow visual heatmap."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Critical Path Method (CPM) & Visual Bottleneck Heatmap Architecture

## 1. Algorithmic Foundation (NodeTaskGraphEngine)

Critical Path Method (CPM) enables project management and DAG execution by identifying the sequence of dependent tasks that directly dictates the minimum total duration to complete the graph.

### A. Task Duration Estimation Model
Task durations are inferred from node properties or priority heuristics:
- `completed` or `in_progress` nodes with high progress = `0.0h` (already completed or near completion).
- Explicit `estimated_hours` metadata if present.
- Fallback Priority Heuristic:
  - `critical`: 8.0h
  - `high`: 5.0h
  - `medium`: 3.0h
  - `low`: 1.5h
  - Default: 2.0h

### B. Two-Pass Traversal Algorithm
1. **Forward Pass (Early Start & Early Finish)**:
   - For all root nodes (in-degree = 0): `ES = 0.0`, `EF = ES + duration`.
   - For downstream nodes in topological order:
     `ES(v) = max([EF(u) for u in predecessors(v)])`
     `EF(v) = ES(v) + duration(v)`
   - Graph Total Duration: `max([EF(v) for v in nodes])`.

2. **Backward Pass (Late Finish & Late Start)**:
   - For all sink nodes (out-degree = 0): `LF(v) = Total Duration`, `LS(v) = LF(v) - duration(v)`.
   - For upstream nodes in reverse topological order:
     `LF(u) = min([LS(v) for v in successors(u)])`
     `LS(u) = LF(u) - duration(u)`

3. **Total Float / Slack**:
   - `Slack(v) = LS(v) - ES(v)` (or equivalently `LF(v) - EF(v)`).
   - Invariant: A task is **Critical** if and only if `Slack(v) <= 0.001` (due to floating point math).

4. **Critical Edges & Bottleneck Detection**:
   - Edge `(u, v)` is critical if:
     - `u` is critical AND `v` is critical AND `abs(EF(u) - ES(v)) <= 0.001`.
   - **Bottlenecks**: Critical nodes that block multiple tasks (out-degree > 1) or have long durations, ranked by impact score `out_degree * duration`.

---

## 2. API Endpoint Architecture (`apps/api/routers/node_tasks_router.py`)

- **Route**: `GET /api/v3/node_tasks/critical_path`
- **Query Params**: `project_id: Optional[str] = None`
- **Response Shape**:
```json
{
  "status": "success",
  "project_id": "proj-default",
  "total_nodes": 12,
  "critical_node_ids": ["task-1", "task-3", "task-7"],
  "critical_edge_ids": ["edge-task-1-task-3", "edge-task-3-task-7"],
  "total_duration_hours": 16.0,
  "bottlenecks": [
    {
      "node_id": "task-3",
      "title": "Core Auth Engine",
      "duration": 5.0,
      "blocked_tasks_count": 4,
      "impact_score": 20.0
    }
  ],
  "node_metrics": {
    "task-1": { "duration": 8.0, "es": 0.0, "ef": 8.0, "ls": 0.0, "lf": 8.0, "slack": 0.0, "is_critical": true }
  }
}
```

---

## 3. Zustand State Store Integration (`nodeTasksStore.ts`)

```typescript
interface NodeTasksState {
  showCriticalPath: boolean;
  criticalPathNodeIds: string[];
  criticalEdgeIds: string[];
  criticalPathTotalDuration: number;
  criticalPathBottlenecks: any[];
  criticalPathMetrics: Record<string, any>;
  setShowCriticalPath: (show: boolean) => void;
  fetchCriticalPath: (projectId?: string) => Promise<void>;
}
```

When `showCriticalPath` is toggled ON:
1. `fetchCriticalPath()` requests `/api/v3/node_tasks/critical_path`.
2. Stores `criticalPathNodeIds` and `criticalEdgeIds`.
3. Triggers reactive rendering in React Flow nodes and edges.

---

## 4. Visual Heatmap & High-Contrast Dimming (React Flow)

### A. Custom Task Node (`CustomTaskNode.tsx`)
- **Critical Nodes**:
  - Border and Ring: `ring-2 ring-rose-500/80 border-rose-500 shadow-[0_0_24px_rgba(244,63,94,0.45)]`
  - Flame Badge: `CRITICAL PATH (Dur: Xh | Slack: 0h)`
- **Non-Critical Nodes**:
  - When CPM is active, non-critical nodes apply `opacity-40 saturate-50 transition-opacity` so the critical path instantly pops out to the user.

### B. Custom Edge (`CustomDependencyEdge.tsx`)
- **Critical Edges**:
  - Stroke: `#f43f5e` (Rose-500)
  - Stroke Width: `3px`
  - Marker / Badge: `🔥 CPM` pill with pulsing neon indicator.

### C. Canvas Analytics Banner (`NodeTaskGraphCanvas.tsx`)
- Floating top banner displays:
  - Critical Path Duration in hours.
  - Number of critical blocking tasks.
  - Chief bottleneck node with instant jump-to link.
