# Google Stitch Extended Drawers Suite & Canonical Consolidation (ADR 016 Variant B)

## 1. Architectural SSOT & Clean Two-Tier Invariant
- **Single Source of Truth**: All active web interface development, React Flow canvas wrappers, and Stitch spatial components reside strictly under `apps/web/`.
- **Legacy Deprecation**: The `visual_shell` directory is frozen and marked `DEPRECATED` via `visual_shell/DEPRECATED.md`. No new imports or features may target `visual_shell`.
- **Zero Cross-Dependency Policy**: `apps/web` must have zero runtime dependencies or imports targeting `visual_shell`. All shared components live in `apps/web/components/stitch/` with a barrel export at `apps/web/components/stitch/index.ts`.

## 2. Extended Stitch Spatial Drawers & Command Panels
Under `apps/web/components/stitch/`:
1. **`StitchSmartInspector.tsx`**:
   - Inspects node geometry, typography, and color tokens defined in `DESIGN.md`.
   - Built-in WCAG 2.1 AA accessibility contrast auditor.
   - Upstream/downstream DAG relationship links.
2. **`StitchShopifyPreviewDrawer.tsx`**:
   - Live AST Liquid section sandbox for Shopify Online Store 2.0.
   - Schema JSON validation and one-click store sync.
3. **`StitchBiAnalystDrawer.tsx`**:
   - Business intelligence drawer operating over DuckDB Lakehouse.
   - Natural language to SQL (NL2SQL) interactive query runner and charts.
4. **`StitchTaskForestDrawer.tsx`**:
   - Spatial tree navigator for the 5-level task taxonomy: `Field` ➔ `Sector` ➔ `Tree` ➔ `Bush` ➔ `Flower`.
   - Genetic node DTO inspection and interactive Time-Travel timeline scrubber.
5. **`StitchSwarmCommandCenter.tsx`**:
   - Real-time agent status telemetry, token usage, latency HUD, and swarm pause/resume triggers.
6. **`StitchKineticTimeline.tsx`**:
   - Event timeline with reactive playback for multi-agent swarm operations.
7. **`index.ts`**:
   - Central barrel exporting all 6 drawers, top nav, cards, prompts, and their shared TypeScript interfaces.

## 2.1 Reactive Canvas Cockpit Integration (`DNKStudioWorkspace.tsx`)
In `apps/web/components/workspace/DNKStudioWorkspace.tsx`:
- Manage active spatial drawers via single reactive state: `activeDrawer: 'swarm' | 'timeline' | 'shopify' | 'bi' | 'tasks' | 'inspector' | null`.
- Connect callbacks to `StitchTopNav.tsx` triggers (`onToggleSwarm`, `onToggleTimeline`, `onToggleShopify`, `onToggleBi`, `onToggleTasks`).
- Provide floating HUD toast notifications (`toastMessage`) and integrate `StitchPromptDock` agent triggers with the live WebSocket/REST bridge.

## 3. Automated API Contract Synchronization
- **Script**: `scripts/system/generate_frontend_types.py`
- **Flow**:
  1. Spins up or introspects FastAPI app schema (`core.orchestrator.fastapi_app`).
  2. Dumps clean OpenAPI 3.1 schema to `apps/web/openapi.json`.
  3. Executes `npx openapi-typescript apps/web/openapi.json -o apps/web/types/apiGenerated.ts`.
- **Benefit**: Zero hand-written API types, compile-time type safety across frontend and backend.

## 4. AST Canvas Codebase Synchronization
- **Script**: `scripts/system/sync_codebase_to_canvas.py`
- Generates and synchronizes `docs/notes/DNK_HUB_Core_Architecture.canvas` with actual codebase packages, apps, core engines, and services.

## 5. Path Hygiene Testing Pitfall
- In test suites (e.g. tests verifying path isolation or worktree sandboxes), **never** hardcode literal absolute paths like `"/Users/..."` directly in Python strings.
- Static path hygiene linters (such as those in `verify_all.sh` or `auto_precommit_guard.py`) scan the entire repo for absolute path patterns.
- **Solution**: Use dynamic string concatenation (e.g., `"/Users" + "/example"`) or environment mock fixtures (`tmp_path`).
