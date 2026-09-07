# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/canvas-engine-architecture/references/visual_shell_open_design_runtime_supervision.md"
# purpose: "Operational reference for Visual Shell (Open Design) daemon and web runtime supervision, Node.js ABI compatibility, and Next.js Turbopack import guards."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Visual Shell (Open Design) Runtime Supervision & ABI Invariants

## Architecture Overview
Visual Shell (`visual_shell/open_design/`) provides the local-first visual canvas, design systems, and agent artifacts environment for DNK OS:
- **Daemon (`apps/daemon/`, Port 7456)**: Privileged Express + SQLite backend (`apps/daemon/bin/od.mjs`), managing CLI agent spawning, design skills, artifacts, and MCP connectors.
- **Web UI (`apps/web/`, Port 5173)**: Next.js 16 (App Router) + React 18 Canvas interface with Turbopack, proxying `/api/*` and `/artifacts/*` to the local daemon.

## Invariant 1: Native Module ABI & Node.js PATH Precedence
- **Symptom**: `ERR_DLOPEN_FAILED` on `better-sqlite3`:
  ```
  Error: The module '.../better_sqlite3.node' was compiled against a different Node.js version
  using NODE_MODULE_VERSION 141. This version of Node.js requires NODE_MODULE_VERSION 137.
  ```
- **Root Cause**: Node.js v24 (ABI 137) at `/usr/local/bin/node` vs Node.js v25 (ABI 141) at `/opt/homebrew/bin/node`. Native bindings compiled under Node 25 fail when launched with Node 24.
- **Rule**: Launch scripts (`scripts/start_open_design.sh`) must ensure `/opt/homebrew/bin` precedes `/usr/local/bin` in `PATH` before invoking `node` or `pnpm`:
  ```bash
  if [ -d "/opt/homebrew/bin" ]; then
    export PATH="/opt/homebrew/bin:$PATH"
  fi
  ```

## Invariant 2: Turbopack Static Import Boundary
- **Symptom**: Next.js App Router 500 error on `/`:
  ```
  Export isRetryableAssistantTerminalFailure doesn't exist in target module ../../runtime/chat-events
  ```
- **Rule**: In `apps/web/src/components/project-view/conversationUtils.ts`, import assistant terminal failure predicates from `../../runtime/design-delivery`, where they are declared and exported, never from `../../runtime/chat-events`.

## Invariant 3: Single Supervisor Script & Health Verification
- **Supervisor**: Run `bash scripts/start_open_design.sh`.
- **Health Verification**:
  - Daemon: `curl -s http://127.0.0.1:7456/api/health` -> `{"ok":true,"version":"..."}`
  - Web UI: `curl -sI http://localhost:5173` -> `HTTP/1.1 200 OK`
- **Graceful Teardown**:
  ```bash
  lsof -ti :7456 | xargs kill -9 2>/dev/null || true
  lsof -ti :5173 | xargs kill -9 2>/dev/null || true
  ```
