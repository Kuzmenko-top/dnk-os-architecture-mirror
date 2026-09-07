# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/beads-task-forest-integration/references/task-forest-spatial-lod-timetravel.md"
# purpose: "Reference architecture for Task Forest Spatial LOD (Level-of-Detail) and Time-Travel Evolution Scrubber."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "Gerych Core"
# --- END DNK-MRH-HEADER ---

# Task Forest Spatial LOD & Time-Travel Architecture

## 1. Five-Tier Taxonomy & Spatial Zoom Mapping (LOD)

| Taxonomy Level | Semantic Concept | Canvas Zoom Range | Visual Representation | Target Information Density |
|:---|:---|:---|:---|:---|
| **Level 1: 🌾 Field** | Macro Workspace / Strategic Domain | Zoom < 0.3x (LOD 0.2x) | Heatmap Card / Bounding Region | Total Domain Health (e.g. `88% 🟢`), sector count |
| **Level 2: 🏞️ Sector** | Architectural Area / Subsystem | Zoom < 0.5x (LOD 0.2x) | Clustered Group Box | Aggregated progress bar, active agent counts |
| **Level 3: 🌳 Tree** | Epic / Feature Milestone | 0.5x ≤ Zoom < 1.8x (LOD 1.0x) | Node Header + Progress Ring | Milestone title, completion ratio, lead agent badge |
| **Level 4: 🌿 Bush** | Feature Branch / Task Group | 0.8x ≤ Zoom < 2.0x (LOD 1.0x) | Branch Node Card | Branch checklist summary, dependency edges |
| **Level 5: 🌸 Flower** | Atomic Subtask / PR / Unit of Work | Zoom ≥ 2.0x (LOD 2.5x) | Full Interactive Card | Acceptance criteria, `git_diff` inspector, direct mutation buttons |

## 2. Canvas LOD Implementation Pattern (React Flow)

In React Flow or custom canvas renderers, use viewport hooks (`useViewport` / `zoom` listener) to dynamically toggle node card detail without unmounting:

```tsx
import React from 'react';
import { useViewport, NodeProps } from 'reactflow';

export const TaskForestSpatialNode: React.FC<NodeProps> = ({ data }) => {
  const { zoom } = useViewport();

  // Dynamic Level of Detail evaluation
  const lodLevel = zoom < 0.4 ? 'macro' : zoom > 1.8 ? 'micro' : 'meso';

  if (lodLevel === 'macro') {
    // LOD 0.2x: Aggregated metric view (Field / Sector)
    return (
      <div className="p-2 rounded-lg bg-slate-900 border border-slate-700 text-xs">
        <span className="font-bold">{data.title}</span>: {data.progress}%
      </div>
    );
  }

  if (lodLevel === 'micro') {
    // LOD 2.5x: High-fidelity atomic view (Flower with diff/status)
    return (
      <div className="p-4 rounded-xl bg-slate-900 border border-emerald-500 shadow-xl">
        <h4 className="font-semibold text-sm">{data.title}</h4>
        <span className="badge">{data.status}</span>
        {data.git_diff && <pre className="text-[10px] bg-black p-2 mt-2">{data.git_diff}</pre>}
      </div>
    );
  }

  // LOD 1.0x: Structural hierarchy (Tree / Bush)
  return (
    <div className="p-3 rounded-lg bg-slate-900 border border-slate-600">
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium">{data.title}</span>
        <span className="text-xs text-slate-400">{data.assigned_agent}</span>
      </div>
      <div className="w-full bg-slate-800 h-2 rounded mt-2">
        <div className="bg-blue-500 h-2 rounded" style={{ width: `${data.progress}%` }} />
      </div>
    </div>
  );
};
```

## 3. Time-Travel Rail & Mutation Scrubber

### API Endpoints
- `GET /api/v3/task_forest/graph`: Returns active snapshot of hierarchical forest graph (`nodes` can be a dict `{node_id: node}` or array). Always normalize:
  `const rawNodes = Array.isArray(data.nodes) ? data.nodes : Object.values(data.nodes || {});`
- `GET /api/v3/task_forest/evolution_history`: Returns ordered mutation event stream:
  ```json
  [
    {
      "mutation_id": "mut-001",
      "timestamp": "2026-09-04T12:00:00Z",
      "mutation_type": "status_update",
      "node_id": "bd-11.4.1",
      "delta": { "from_status": "in_progress", "to_status": "completed", "progress": 100 },
      "actor": "gerych_builder"
    }
  ]
  ```
  *Note on Cascades*: Bottom-up recalculations append multiple events up to the root Field. To locate an atomic mutation, filter by `node_id` instead of assuming it is the last item.

### Replay Semantics
1. **Initial Baseline ($T_0$)**: Initial graph structure before mutation events.
2. **Scrubber Delta Apply ($T_k$)**: Successively replay mutations up to index $k$.
3. **Pulse Highlight**: Emit visual glow/highlight on the node modified at index $k$.
4. **Read-Only Lock during Time-Travel**: Mutating operations on the canvas are disabled while viewing $T_k < T_{head}$.
