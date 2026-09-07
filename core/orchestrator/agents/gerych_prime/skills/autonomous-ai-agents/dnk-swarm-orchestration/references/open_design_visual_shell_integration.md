# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/open_design_visual_shell_integration.md"
# purpose: "Technical Reference for Open Design (Visual Shell) Daemon, Web UI, Hermes ACP Protocol & MCP Server."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.3.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎨 Open Design (Visual Shell), Hermes ACP & MCP Architecture

## Overview
Open Design (Nexu / Visual Shell) provides the spatial canvas UI for DNK OS. It communicates with autonomous coding agents using the Agent Client Protocol (ACP) over JSON-RPC, and provides a native Model Context Protocol (MCP) server for canvas manipulation and daemon control.

---

## 🔌 Architecture & Port Topology

| Component | Port | Directory Path | Description |
|---|---|---|---|
| **DNK OS Main Command Center** | `3000` | `apps/web/` | Primary DNK OS web console and unified dashboard. Connects to FastAPI backend (`apps/api/` on port `8000`). |
| **Open Design Web UI (Visual Shell)** | `5173` | `visual_shell/open_design/apps/web/` | Next.js 16 (App Router) + React 18 + Tailwind. Visual design canvas, chat pane, and artifact viewers. Proxies `/api/*` and `/artifacts/*` to local daemon (`localhost:7456`). |
| **Open Design Daemon** | `7456` | `visual_shell/open_design/apps/daemon/` | Node.js / Express backend daemon (`apps/daemon/bin/od.mjs`). Manages ACP agent processes, WebSocket connections, project SQLite databases, and REST endpoints (`/api/health`, `/api/agents`). It does **not** serve static HTML (`Cannot GET /`). |

### Strict Boundary Invariant
- **Isolation Rule**: Zero cyclic leaks between `apps/web/` and `visual_shell/open_design/apps/web/`.
- Root `apps/web/` handles global hub orchestration and system management.
- `visual_shell/open_design/` is an autonomous creative studio for spatial canvas layout, design generation, and direct ACP sidecar integration.

---

## 🛠️ ACP Setup & Hermes Runtime Registration

### 1. Hermes ACP Requirement
Hermes Agent natively supports ACP via `hermes acp`. This requires the `[acp]` extra dependencies (such as `agent-client-protocol` / `fastmcp`):
```bash
# In core/hermes_agent:
uv pip install -p .venv -e '.[acp]'

# Verify ACP readiness:
hermes acp --check
# Must output: "Hermes ACP check OK"
```

### 2. Agent Auto-Discovery
The Open Design daemon probes available CLI agents on startup via `/api/agents`. When Hermes ACP is installed, daemon reports:
```json
{
  "id": "hermes",
  "name": "Hermes",
  "available": true,
  "modelsSource": "live",
  "command": "~/.local/bin/hermes",
  "protocol": "acp-json-rpc"
}
```

### 3. Agent Priority Invariant
In `visual_shell/open_design/apps/web/src/App.tsx`:
- Place `'hermes'` at the top of `CANONICAL_AGENT_ORDER` (index 0) so Hermes is selected by default for all new conversations and canvas projects.
- Map `'hermes': 'Hermes (Герич · DNK OS)'` in `apps/web/src/utils/agentLabels.ts`.

---

## 🧩 Native MCP Server Integration (`open-design`)

To enable Gerych / Hermes Agent to communicate directly with the Open Design Desktop daemon via MCP:

### 1. Registration via Hermes CLI (`hermes config set`)
Always use `hermes config set` to update agent configuration without triggering file protection soft-guards:
```bash
# Helper binary and daemon script args
hermes config set mcp_servers.open-design.command "/Applications/Open Design.app/Contents/Frameworks/Open Design Helper.app/Contents/MacOS/Open Design Helper"
hermes config set mcp_servers.open-design.args '["/Applications/Open Design.app/Contents/Resources/app/prebundled/daemon/daemon-cli.mjs", "mcp"]'

# Environment variables (Use tilde '~' for path hygiene compliance)
hermes config set mcp_servers.open-design.env.OD_DATA_DIR "~/Library/Application Support/Open Design/namespaces/release-stable/data"
hermes config set mcp_servers.open-design.env.OD_SIDECAR_IPC_PATH "/tmp/open-design/ipc/release-stable/daemon.sock"
hermes config set mcp_servers.open-design.env.OD_MCP_BOOTSTRAP_COMMAND "/usr/bin/open"
hermes config set mcp_servers.open-design.env.OD_MCP_BOOTSTRAP_ARGS '["-g", "-j", "/Applications/Open Design.app", "--args", "--headless"]'
hermes config set mcp_servers.open-design.env.ELECTRON_RUN_AS_NODE "1"
```

### 2. Verification
Check that the MCP server is enabled and listed:
```bash
hermes mcp list
# Expected:
# open-design      /Applications/Open Design...   all          ✓ enabled
```

### 3. Path Hygiene Invariant
- **Rule**: Never use hardcoded `/Users/<username>/...` paths in `config.yaml` or project configs.
- **Fix**: Use tilde `~` (e.g. `~/Library/Application Support/...`) or environment variables to pass `pytest tests/verification/test_path_hygiene.py` and `scripts/verify_all.sh`.

---

## 🚀 Launch & Process Management Procedure

### 1. Automated Supervised Launch (Recommended)
Use the unified startup script at repository root:
```bash
bash scripts/start_open_design.sh
```
This cleans stale port listeners (`7456`, `5173`), starts daemon and web in the background with health-check polling, and confirms when both endpoints respond with HTTP 200.

### 2. Manual Step-by-Step Launch
1. **Rebuild Native Modules (if required on macOS)**:
   ```bash
   cd visual_shell/open_design && pnpm rebuild -r
   ```
2. **Start Daemon (Port 7456)**:
   ```bash
   node apps/daemon/bin/od.mjs --no-open
   ```
3. **Start Web UI (Port 5173)**:
   *Note: Passing `-p 5173` via `pnpm run dev -- -p 5173` causes Next.js to parse `-p` as a directory path. Use env var instead:*
   ```bash
   cd visual_shell/open_design/apps/web && PORT=5173 pnpm exec next dev --turbopack
   ```
4. **Access**:
   Open **`http://localhost:5173`** in Google Chrome.

### 3. Process Hygiene & Clean Shutdown
To inspect running instances and avoid stale port locks:
```bash
# Inspect running processes
ps aux | grep -E "open_design|daemon|5173|7456" | grep -v grep

# Terminate stale listeners safely
lsof -ti :7456 | xargs kill -9 2>/dev/null || true
lsof -ti :5173 | xargs kill -9 2>/dev/null || true
```

### 4. Quality & Typecheck Verification
```bash
# Typecheck apps
pnpm --filter @open-design/web typecheck
pnpm --filter @open-design/daemon typecheck

# Unit tests
(cd visual_shell/open_design/apps/web && npx vitest run)
```
