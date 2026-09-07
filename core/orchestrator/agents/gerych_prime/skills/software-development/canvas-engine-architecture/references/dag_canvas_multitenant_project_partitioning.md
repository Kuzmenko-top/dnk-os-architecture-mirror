# DAG Task Graph Multi-Tenant Project Partitioning & Subgraph Isolation

## Overview
Architectural pattern and reference implementation for multi-tenant / multi-project partitioning within the DAG Task Graph ecosystem in DNK OS (`services/dnk_node_tasks` & `apps/api/routers/node_tasks_router.py`), alongside the React / Zustand frontend integration (`apps/web/store/nodeTasksStore.ts`, `apps/web/components/node-tasks/ProjectSwitcherDropdown.tsx`).

## Core Invariants

### 1. Backwards Compatibility & Default Project Fallback
- Every node in the task graph belongs to a project partition specified by `node.project_id`.
- If `project_id` is omitted, `None`, or empty, it MUST automatically default to `"dnk_core"` (DNK Core workspace).
- System bootstraps with initial default projects:
  - `dnk_core` (DNK Core, icon: `dna`, color: `#06b6d4`)
  - `m_craft` (M-Craft Studio, icon: `boxes`, color: `#8b5cf6`)
  - `brand_alpha` (Brand Alpha, icon: `sparkles`, color: `#10b981`)

### 2. Edge Subgraph Filtering Invariant (Critical Pitfall)
When filtering a graph by project partition:
```python
valid_node_ids = {n.id for n in project_nodes}
filtered_edges = [
    e for e in all_edges 
    if e.source in valid_node_ids and e.target in valid_node_ids
]
```
**Strict Rule**: Never retain an edge whose `source` or `target` belongs to a different project partition. Dangling edges in the frontend React Flow / Dagre engine cause graph auto-layout collapse, infinite render loops, and desynchronized selection states.

### 3. Topological Sort Recalculation on Subgraph
- After isolating project nodes and edges, the topological order and execution stages must be recalculated exclusively on the filtered subgraph using Kahn's algorithm or DFS.
- Nodes with no internal in-degree inside the active partition are evaluated as root execution nodes.

### 4. API Endpoints Specification
- `GET /api/v3/node_tasks/projects`: Returns list of `ProjectInfo` dictionaries enriched with dynamically computed `tasks_count`.
- `POST /api/v3/node_tasks/projects`: Creates or updates a project definition stored in `data/projects.json`.
- `GET /api/v3/node_tasks/graph?project_id=<id>`: Returns the isolated `NodeTaskGraph` for the requested project partition.

### 5. Frontend Zustand Reactive Store Integration (Slice 2)
In `apps/web/store/nodeTasksStore.ts`:
- **State Properties**:
  - `projects: ProjectInfo[]` (initial: `[]`)
  - `activeProjectId: string` (initial: `'dnk_core'`)
  - `isProjectsLoading: boolean` (initial: `false`)
- **Actions**:
  - `fetchProjects()`: Fetches `/api/v3/node_tasks/projects` and updates `projects`.
  - `setActiveProject(projectId: string)`: Updates `activeProjectId` and immediately triggers `get().fetchGraph(projectId)` to refresh canvas nodes & edges.
  - `createProject(payload)`: POSTs to `/api/v3/node_tasks/projects`, refreshes project list, and sets the newly created project as active.
- **Node Creation Enrichment**:
  In `createOrUpdateNode`, automatically enrich node data with active tenant:
  ```typescript
  project_id: payload.project_id || get().activeProjectId || 'dnk_core'
  ```

### 6. ProjectSwitcher Dropdown UI Specification
In `apps/web/components/node-tasks/ProjectSwitcherDropdown.tsx`:
- Trigger button with active project color indicator, folder icon, truncated name, task count badge, and animated chevron.
- Dark glassmorphism dropdown menu (`bg-zinc-950/95 backdrop-blur-xl border-zinc-800/80 shadow-2xl`).
- 1-click project switching with instant canvas reload.
- Inline modal or drawer to create new projects with custom title, slug ID, description, and color presets.
- Click-outside listener cleanup via `useRef` and `document.addEventListener('mousedown')`.

### 7. Monorepo TypeScript Toolchain Invariant
When verifying frontend code in a monorepo setup where `typescript` is installed in `apps/web/node_modules/`:
- Do NOT run bare `npx tsc` from the repository root (will fail with "This is not the tsc command you are looking for").
- Run `./apps/web/node_modules/.bin/tsc --noEmit --project apps/web/tsconfig.json` or `cd apps/web && npx tsc --noEmit`.
