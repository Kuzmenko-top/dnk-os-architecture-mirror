---
name: architecture-invariants-and-blast-radius
description: "Use when enforcing architecture boundaries or blast radius."
version: 1.0.0
author: Gerych Prime & DNK OS
license: MIT
metadata:
  hermes:
    tags: [architecture, blast-radius, import-cycles, layer-isolation, quality-gate, clean-architecture]
    related_skills: [requesting-code-review, test-driven-development, canvas-engine-architecture]
---

# Architecture Invariants, Import Cycle Defense & Blast Radius Analysis

Enforce architectural boundaries, eliminate circular dependencies, decompose God Components, and determine precise test blast radius before committing.

## When to Use

- When refactoring large monolithic files (>1,000 LOC) or God Components into modular packages.
- When resolving cyclic imports or type recursion across client/server layers.
- When designing pre-commit or CI gates to prevent cross-tier layer leaks.
- When selecting a targeted subset of unit/integration tests instead of running an entire slow monolithic suite.

## Step 1 — Verify Layer Isolation

Prevent upper presentation layers (e.g. `apps/web/`) from directly importing lower-tier private runtimes or daemon modules (e.g. `visual_shell/`, `agent-core/`):

1. **Mirror Shared Contracts**: Instead of importing internal runtime models or error helpers, define a pure TypeScript/Python schema mirror in the client layer (e.g. `apps/web/types/apiProtocol.ts`).
2. **Automated Static Scan**:
   ```python
   # Scan all client files for forbidden imports
   forbidden = ["visual_shell", "packages/agent-core"]
   for path in web_files:
       content = path.read_text()
       for pkg in forbidden:
           assert pkg not in content, f"Layer leak in {path}: imports {pkg}"
   ```

## Step 2 — Detect and Break Circular Dependencies

Circular imports create runtime initialization deadlocks, `undefined` module exports, and tightly coupled codebases.

1. **Extract Shared Types**: Move shared interfaces and enums into a dedicated leaf module (`types.ts`) with zero runtime dependencies. Both mutually importing modules then import from `types.ts`.
2. **Cycle Detection Algorithm (Tarjan / DFS)**:
   - Parse all local relative imports (`import ... from './...'`) to build a directed graph.
   - Run Strongly Connected Components (SCC) or recursive DFS to detect back-edges.
   - Any SCC with size > 1 represents a cycle that must fail the CI gate.
   ```bash
   python3 scripts/system/architecture_and_cycle_guard.py
   ```

## Step 3 — Decompose God Components

Monolithic components (e.g. >5,000 LOC handling layout, state, stream buffering, and rendering) should be decomposed into a cohesive directory package:

1. **Extract Pure Utilities**:
   - `layoutUtils.ts`: Pure calculations, dimensions, and storage persistence.
   - `conversationUtils.ts`: Message normalization, stream buffering, run lifecycle.
   - `artifactRecoveryUtils.ts`: File scanning and artifact restoration.
2. **Expose a Unified Facade**: Create `index.ts` exporting only the clean public surface.
3. **Decouple Existing Consumers**: Migrate external hooks and views to import from the package barrel rather than the monolith.

## Step 4 — Deterministic Blast Radius & Targeted Testing

Running an entire 2,000+ test suite on every minor change causes developer fatigue and timeouts. Use deterministic blast radius tracking:

1. **Inspect Staged / Changed Files**:
   ```bash
   git diff --name-only HEAD
   ```
2. **Reverse Dependency Graph**: Map which modules import the touched files (transitive closure).
3. **Domain Classification & Risk Scoring**:
   - Classify changed paths into system domains (`core`, `api`, `web`, `services`, `scripts`).
   - Assign risk levels:
     - `LOW`: Documentation, markdown, static assets.
     - `MEDIUM`: Isolated CLI script, single UI component.
     - `HIGH`: Shared utility, provider adapter, protocol contract.
     - `CRITICAL`: Orchestrator core, base state machine, root schema.
4. **Discover Targeted Tests & Instant Affected Runner**:
   - Automatically select matching Vitest and Pytest files covering only the affected surface.
   ```bash
   python3 scripts/system/blast_radius_analyzer.py --staged
   # Or invoke the master verification suite in targeted affected mode:
   bash scripts/verify_all.sh --affected   # or: bash scripts/verify_all.sh -a
   ```
5. **Programmatic API Integration**:
   ```python
   from scripts.system.blast_radius_analyzer import BlastRadiusAnalyzer

   analyzer = BlastRadiusAnalyzer(hub_root=".")
   report = analyzer.run(staged_only=False)
   pytest_args = report["targeted_tests"]["pytest"]
   vitest_args = report["targeted_tests"]["vitest"]
   ```

## Step 5 — Option B: Legacy Shell Consolidation into Root Web SSOT & Contract Sync

When deprecating secondary or experimental shells (e.g. `visual_shell/`):
1. **Identify High-Value Unique Widgets**: Extract specialized canvas nodes, timeline rails, and artifact panes.
2. **Port Directly into Root Presentation Layer**: Move them to `apps/web/components/stitch/` following standard contracts and zero-leak imports.
3. **Automate API Contracts**: Generate frontend TypeScript contracts directly from FastAPI OpenAPI schema (`scripts/system/generate_frontend_types.py` ➔ `apps/web/types/apiGenerated.ts`) with unique `operationId` deduplication.
4. **AST Codebase ➔ Canvas Sync**: Update spatial architecture graphs (`scripts/system/sync_codebase_to_canvas.py` ➔ `docs/notes/DNK_HUB_Core_Architecture.canvas`).
5. **Archive Deprecated Sub-Shell**: Eliminate redundant `node_modules` trees, divergent TypeScript configs, and isolate legacy directories.

## Step 6 — Integrate into Pre-Commit and Master CI Gate

Ensure architecture guards and blast radius calculators run automatically:

- **Pre-Commit Hook**: Execute fast static checks (<0.1s) before commits land.
- **CI Master Gate**: Run full architectural and targeted test validation on pull requests.

## Supporting References

- `references/algorithms.md`: Complete implementations of DFS cycle detection for relative imports and reverse dependency blast radius tracking.
- `references/targeted_affected_testing_and_shell_consolidation.md`: Guide to `verify_all.sh --affected` / `-a` and Option B sub-shell consolidation.
- `references/capability_baseline_audit_protocol.md`: Read-only capability baseline & architecture audit protocol for large multi-domain codebases.

## Pitfalls to Avoid

- **Blind Monolithic Runs**: Don't run the entire multi-suite test runner for a single CSS or markdown change. Check blast radius first.
- **Circular Type-Only Imports in Bundlers**: Even if TypeScript allows `import type`, bundlers (Vite/Rollup) or transpilers may emit cyclic runtime references if re-exported through barrels. Always isolate leaf interfaces into `types.ts`.
- **Ignoring Untracked Tests**: Git hygiene guards should block pre-commit if new test files remain untracked.
- **Literal Forbidden Paths in Negative Tests**: Static grep sanitizers in pre-commit scripts scan for forbidden patterns (e.g. `/Users/`). Construct test strings dynamically (`"/Users" + "/fake/path"`) in negative test cases to prevent false-positive sanitizer failures.
