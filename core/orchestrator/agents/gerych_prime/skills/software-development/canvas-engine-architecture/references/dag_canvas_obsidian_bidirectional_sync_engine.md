# DAG Canvas & Obsidian Task Notes Bidirectional Sync Engine (Slice 1)

## Overview
Architecture, contracts, and invariants for bidirectional synchronization between the DAG Node Task Canvas graph (`NodeTaskGraph`) and Obsidian Markdown notes (`docs/notes/tasks_and_ideas/*.md`), enriched with SOTA resilience patterns from the **Soup** ecosystem (`MakazhanAlpamys/Soup`).

## Core Components (`services/dnk_canvas_api/obsidian_sync_engine.py`)

### 1. Markdown Parsing & Frontmatter Normalization (`parse_markdown_note`)
- **YAML Frontmatter Mapping**:
  - `id`: unique identifier for the DAG node.
  - `title`: human-readable node name.
  - `stage`: lifecycle stage (`backlog`, `research`, `planning`, `in_progress`, `review`, `completed`).
  - `status`: execution status (`pending`, `running`, `blocked`, `completed`, `failed`).
  - `type` / `node_type`: node category (`epic`, `task`, `bug`, `research`, `milestone`, `idea`).
  - `priority`: priority weighting (`low`, `medium`, `high`, `critical`).
  - `progress`: numeric completion percentage (0 - 100).
  - `project_id`: multi-tenant project boundary (defaults to `'dnk_core'`).
  - `assigned_agent`: worker tag (e.g. `'gerych_builder'`, `'dnk_shopify'`).
  - `target_module`: module anchor (e.g. `'apps/web'`, `'core'`).
- **Soup Resilient Markdown Ingestion (Data Hygiene Fallback)**:
  - If PyYAML / frontmatter parsing raises `yaml.YAMLError` (e.g. unquoted colons, tab indentations, broken delimiters):
    - Activates resilient line-by-line fallback parser instead of discarding the note.
    - Strips lines, isolates standard key-value pairs (`key: value`), and parses list items (`- item`).
    - Guarantees zero note dropouts across dirty human-edited Obsidian vaults.
- **Obsidian Wikilink Invariant**:
  - Upstream dependencies extracted from `dependencies` frontmatter field and Markdown links.
  - Normalizes formats:
    - `[[node-id]]` -> `node-id`
    - `[[node-id|Custom Label]]` -> `node-id`
    - `node-id` -> `node-id`
  - Sanitizes wikilink brackets and anchors (`#heading`).
- **Acceptance Criteria Extraction & Soup 3-Way Layered Union**:
  - Scans markdown body lines for checklist items:
    - `- [ ] <text>` -> `{"text": ..., "completed": False}`
    - `- [x] <text>` -> `{"text": ..., "completed": True}`
  - **Soup Layered Merge Rule**:
    - When updating an existing node with incoming Markdown checklist items, criteria are merged non-destructively.
    - Status is resolved via boolean OR: if existing is `completed=True` or incoming is `completed=True`, the resolved state remains `True`.
    - New criteria discovered in markdown are appended without wiping existing graph criteria.
- **Body Markdown Retention**:
  - Raw markdown body content following frontmatter is extracted and preserved in `body_markdown` to prevent arbitrary user prose loss during bidirectional roundtrips.
- **Position Metadata**:
  - Optional `position: {x: N, y: N}` in frontmatter preserved for spatial canvas layout.

### 2. Vault Reconciler & Ingestion (`sync_from_obsidian_vault`)
- **Scanning**:
  - Scans target vault folder (defaults to `docs/notes/tasks_and_ideas/*.md`).
  - Filters by `project_id` when scoped.
- **Node Ingestion**:
  - Creates newly discovered notes as canvas nodes.
  - Updates existing nodes with latest frontmatter metadata and checklist progress.
- **Soup Anti-Dangling Wikilinks Guard (Auto-Stubbing)**:
  - If a note declares a dependency on `[[missing-task]]` that does not exist in the graph or vault:
    - Instead of throwing a foreign key violation or creating a disconnected broken edge:
    - Automatically creates a placeholder stub node of `type: NodeType.IDEA`, `stage: ExecutionStage.IDEATION`, `status: NodeStatus.BACKLOG`, `assigned_agent: "herich_librarian"`, and tag `#unresolved_dependency`.
    - Links the edge safely, preserving DAG topological validity and surfacing the missing prerequisite to the user on the canvas.
- **Edge Reconciliation & Cycle Prevention**:
  - Builds edges from parsed upstream dependencies (`dep -> node.id`).
  - Before adding each edge, executes `NodeTaskGraphEngine.detect_cycle_with_new_edge(graph, source, target)`.
  - Discards or flags cyclic edges to prevent DAG engine collapse.
- **Dependency Recalculation**:
  - Invokes `NodeTaskGraphEngine.recalculate_graph_dependencies(graph)`.
  - Atomically saves updated state via `NodeTaskPersistenceManager.get_instance().save_graph()`.

### 3. Bidirectional Orchestration (`sync_bidirectional`)
- Executes two-phase sync:
  1. Phase 1: `sync_from_obsidian_vault` (pull Obsidian changes into DAG graph).
  2. Phase 2: `NodeTaskPersistenceManager.get_instance().sync_to_obsidian(vault_dir)` (push updated DAG state to markdown notes).
- Returns unified telemetry payload:
  `{"status": "ok", "imported_count": int, "updated_count": int, "edges_created": int, "exported_count": int}`

## API Contracts (`apps/api/routers/node_tasks_router.py`)

- `POST /api/v3/node_tasks/sync_from_obsidian`:
  - Request: `{"vault_dir": "docs/notes/tasks_and_ideas", "project_id": "dnk_core"}`
  - Response: Telemetry with imported/updated node counts.
- `POST /api/v3/node_tasks/sync_bidirectional`:
  - Request: `{"vault_dir": "docs/notes/tasks_and_ideas", "project_id": "dnk_core"}`
  - Response: Telemetry with bidirectional reconciliation results.

## Frontend Integration (Slice 2)

### 1. Zustand Store (`apps/web/store/nodeTasksStore.ts`)
- **`syncObsidianBidirectional` Action**:
  - Issues `POST /api/v3/node_tasks/sync_bidirectional?project_id=${projectId}`.
  - Automatically triggers `await get().fetchGraph(projectId)` on success so all newly imported notes and updated dependencies immediately re-render on the React Flow canvas.
  - Returns `{ success: boolean, scanned?: number, imported?: number, updated?: number, exported?: number, edges_synced?: number }`.
  - Backward compatibility: `syncObsidian()` aliases `syncObsidianBidirectional()` with `syncedCount: res.exported`.

### 2. Canvas UI Header Button (`apps/web/components/node-tasks/NodeTaskGraphCanvas.tsx`)
- Replaced blocking modal `alert(...)` with non-blocking toast notifications via `showToast`:
  - Success: `🔄 Двостороння синхронізація: ${res.imported ?? 0} нових, ${res.updated ?? 0} оновлено, ${res.exported ?? 0} експортовано!`
  - Error: `Помилка при синхронізації з Obsidian Vault`
- Button displays spinning animation during sync (`animate-spin`), disabled state, and status label toggle (`Синхронізація...` vs `🔄 2-Way Sync`).

## Headless Verification Invariant

Run with project virtual environment:
```bash
# Backend verification:
.venv/bin/pytest tests/verification/test_node_tasks_obsidian_sync.py -v

# Frontend TypeScript verification:
./apps/web/node_modules/.bin/tsc --noEmit --project apps/web/tsconfig.json
```
