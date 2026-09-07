# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/canvas-engine-architecture/references/node_tasks_artifacts_and_diff_inspector.md"
# purpose: "Architecture specification & invariants for Node Tasks Live Artifacts, Diff Inspector, and Verification Action Engine"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# Node Tasks Live Artifacts, Diff Inspector & Verification Action Engine

## 1. Overview
In the DNK OS Swarm Canvas environment, each executing node produces code mutations, files, and diff artifacts. The **Artifact Diff Inspector & Verification Action Engine** provides a tight verification loop directly on the canvas without leaving the UI.

## 2. REST API Specification (`apps/api/routers/node_tasks_router.py`)

### A. Artifact Retrieval (`GET /api/v3/node_tasks/{node_id}/artifacts`)
- **Purpose**: Generates or retrieves the execution diff report for a node.
- **Payload/Output**:
  ```json
  {
    "node_id": "task-node-001",
    "agent": "gerych_builder",
    "status": "ready_for_review",
    "files": [
      {
        "path": "apps/api/routers/node_tasks_router.py",
        "change_type": "modified",
        "additions": 45,
        "deletions": 2,
        "diff_content": "@@ -1,5 +1,8 @@\n..."
      }
    ],
    "total_additions": 45,
    "total_deletions": 2,
    "summary": "1 files changed (+45, -2)",
    "executed_at": "2026-09-06T12:00:00Z"
  }
  ```
- **Invariant**: Uses `git diff` against HEAD or working tree when available, falling back to a structured inspection of `target_files` in task metadata if the git diff is empty.

### B. Artifact Acceptance Gate (`POST /api/v3/node_tasks/{node_id}/accept_artifacts`)
- Transitions node to `TaskStatus.COMPLETED` (100% progress).
- Marks task stage as `TaskStage.COMPLETED`.
- Recalculates DAG dependencies (`recalculate_graph_dependencies`) to unlock downstream consumer nodes.
- Syncs state to Obsidian vault note.
- Broadcasts `node.executed` event over WebSocket/SSE bridge.

### C. Artifact Rejection Gate (`POST /api/v3/node_tasks/{node_id}/reject_artifacts`)
- Accepts optional `reason` in `RejectArtifactsRequest`.
- Transitions node back to `TaskStatus.IN_PROGRESS` (progress reset to 50%).
- Appends `[WARNING]` entry into the node's ring-buffer terminal log with the rejection reason.
- Broadcasts `node.status_changed` event over WebSocket bridge.

### D. Verification Action Engine (`POST /api/v3/node_tasks/{node_id}/run_verification`)
- Executes automated test command (`.venv/bin/pytest <target>` or custom suite).
- Invariant: Guarded with `asyncio.wait_for(..., timeout=30.0)` to eliminate headless process hangs.
- Streams stdout and stderr into node terminal logs.
- Emits `node.verified` event with `passed: boolean` and exit code.

### E. Terminal Log Management
- `POST /api/v3/node_tasks/{node_id}/clear_logs` and `DELETE /api/v3/node_tasks/{node_id}/logs`: Clears the ring buffer.

## 3. Frontend Architecture & React UI Components (Slice 2)

### A. Zustand State Store (`apps/web/store/nodeTasksStore.ts`)
- **State Properties**:
  - `nodeArtifacts: Record<string, NodeArtifactReport>`: Keyed by `nodeId`.
  - `isArtifactsLoading: boolean`: Global/per-node spinner indicator.
  - `isVerifying: boolean`: Verification runner execution indicator.
  - `verificationResults: Record<string, VerificationResult>`: Maps `nodeId` to exit code, status, and raw terminal log output.
- **Asynchronous Actions**:
  - `fetchNodeArtifacts(nodeId)`: Fetches `/api/v3/node_tasks/{nodeId}/artifacts`.
  - `acceptNodeArtifacts(nodeId)`: Triggers acceptance gate, updates node to completed.
  - `rejectNodeArtifacts(nodeId, reason?)`: Triggers rejection gate with feedback reason.
  - `runNodeVerification(nodeId, testCommand?)`: Executes backend verification suite.

### B. Artifact Diff Inspector (`apps/web/components/node-tasks/NodeTaskArtifactDiffViewer.tsx`)
- Visualizes git unified diff output per file.
- Line coloring conventions:
  - `+` (green background `emerald-950/40`, text `emerald-400`): additions.
  - `-` (red background `rose-950/40`, text `rose-400`): deletions.
  - `@@` (violet background `purple-950/40`, text `purple-300`): hunk markers.
- Inline summary pills: `+N additions`, `-N deletions`, and file selector tab-bar.
- Inline action bar for `runNodeVerification`, `acceptNodeArtifacts`, and modal-guided `rejectNodeArtifacts`.

### C. Tri-Tab Drawer Integration (`apps/web/components/node-tasks/NodeTaskDetailDrawer.tsx`)
- Standardized header tab switcher:
  - `[Огляд]` (`overview`): Task parameters, description, worker agent dispatch, dependencies.
  - `[Live Термінал]` (`terminal`): Fullscreen-height terminal ring-buffer log stream with color-coded severity badges.
  - `[Diff Артефактів]` (`diff`): Embedded `NodeTaskArtifactDiffViewer` with dynamic badge showing changed file count (`files.length`).

## 4. Critical Implementation Pitfalls & Rules

1. **Singular Endpoint Naming Invariant**:
   - The REST endpoints for creating and deleting node objects in `node_tasks_router` use `/api/v3/node_tasks/node` (singular), NOT `/nodes`.
   - Calling `/api/v3/node_tasks/nodes` returns `404 Not Found`.

2. **Timeout & Process Cleanup Guard**:
   - Subprocesses created via `asyncio.create_subprocess_shell` must always be terminated upon timeout:
     ```python
     except asyncio.TimeoutError:
         try:
             proc.kill()
             await proc.wait()
         except Exception:
             pass
     ```

3. **Virtualenv Priority for Test Commands**:
   - Custom test runners must prefer `./.venv/bin/pytest` over raw `pytest` to guarantee matching dependency contexts in CI and development.

4. **Monorepo TypeScript Verification Command Invariant**:
   - In Next.js / Turborepo monorepos, running a bare `npx tsc` can attempt to download the npm placeholder package `tsc` instead of using the local compiler.
   - Always run `./apps/web/node_modules/.bin/tsc --noEmit --project apps/web/tsconfig.json` or `npm --prefix apps/web exec tsc -- -p apps/web/tsconfig.json --noEmit` for reliable type checking without network calls or path confusion.
