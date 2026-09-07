# Upstream Monorepo Assimilation & Cycle Preservation Invariants

## 1. Context & Architectural Challenge
When assimilating a major upstream release (e.g., Open Design v0.18.1 -> v0.21.1) in an embedded runtime like `visual_shell/open_design`:
- Upstream introduces hundreds of commits, new dependencies, and file renames.
- DNK OS maintains strict architectural boundaries enforced by `scripts/system/architecture_and_cycle_guard.py`:
  1. Zero layer leaks between `apps/web` and `visual_shell`.
  2. Zero circular dependencies in `providers/` and `updater/` subsystems.
  3. Decoupling of monolithic God Components (e.g. `ProjectView.tsx` into modular sub-package `project-view/`).
- Blind copying or standard git merging of upstream tags will inadvertently clobber these cycle mitigations and restore circular dependencies.

## 2. Invariant Workflow: 5-Stage Controlled Ingestion

### Stage 0: Cold Backup Oracle Isolation
Before touching anything in the working tree:
```bash
cp -a visual_shell/open_design visual_shell/open_design.bak-<version>
```
- Serves as the <10s rollback safety net.
- Acts as the exact AST oracle for custom decoupled modules (`updater/types.ts`, `providers/types.ts`, `project-view/`).

### Stage 1: Isolated Staging Clone & Target Tag Extraction
Never pull upstream directly into the active working tree. Clone into an isolated sandbox:
```bash
git clone --depth 1 --branch <upstream-tag> <upstream-repo-url> /tmp/<project>_staging
```

### Stage 2: Selective Replay of In-House Subsystems
Replay all DNK OS extensions and custom components into the staging tree:
1. UI components (e.g., `components/stitch/`, QuickBar, entrypoints).
2. Daemon persistence, routes, event buses (`routes/canvas-persistence.ts`, `redis-event-bus.ts`).
3. Custom AI providers and protocol utilities (`apps/web/src/providers/`, `apps/web/src/utils/apiProtocol.ts`).
   - **Circular Re-export Pitfall**: Ensure canonical logic lives in the utility layer (`apiProtocol.ts`) and is imported by provider adapters, not vice versa. Maintain casing alias exports (`export { isOpenAICompatible as isOPenAICompatible }`) to avoid breakages across custom and upstream modules.
4. Cycle mitigation SSOTs (`providers/types.ts`, `apps/desktop/src/main/updater/types.ts`).
5. Decoupled packages (`components/project-view/`).

### Stage 3: Native Node ABI Rebuild (`better-sqlite3`)
Upstream checkouts frequently bundle or pull native C++ prebuilds compiled for different Node.js ABIs (e.g. Node 20 vs Node 25):
```bash
# Force rebuild against the current active Node runtime
pnpm --filter @open-design/daemon exec npm rebuild better-sqlite3
```
Verification:
```bash
node -e "require('./visual_shell/open_design/node_modules/better-sqlite3')"
```

### Stage 4: Post-Replay Architectural Guard & Typecheck Gate
BEFORE performing hot-swap or reporting completion, run the architecture guard and typecheck:
```bash
./.venv/bin/python3 scripts/system/architecture_and_cycle_guard.py
pnpm --filter @open-design/daemon typecheck
pnpm --filter @open-design/web typecheck
```
If circular references are flagged (e.g., `payload.ts imports parent updater.ts`):
- Check backup oracle: restore the decoupled `types.ts` and update relative imports from `"./types.js"` instead of `"../updater.js"`.

### Stage 5: Atomic Hot-Swap & Multi-Layer Health Probe
1. Move the verified staging build into `visual_shell/open_design`.
2. Launch via supervisor: `bash scripts/start_open_design.sh`.
3. Probe `/api/health` and verify HTTP 200 OK with expected version string.
4. **Turbopack Dev Overlay Verification Trap**: Next.js returns HTTP 200 on `http://localhost:5173` even when a full-screen build error overlay is rendering (`nextjs-portal`). Never declare web readiness based on HTTP status code alone. Always:
   - Check build logs (`/tmp/open_design_web.log`) for `✓ Compiled in ...` without compilation errors.
   - Inspect the live DOM or `nextjs-portal` shadowRoot (via `browser_exec` or CDP) to verify that zero error dialogs exist.
5. Execute Python regression suite: `pytest tests/verification/test_visual_shell.py tests/test_web_layer_isolation.py tests/test_project_view_decomposition.py`.
