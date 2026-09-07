# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/canvas_and_visual_engine_bridge.md"
# purpose: "Architectural Reference: Decoupled Visual Canvas AST & UI Tool Bridge Assimilation Pattern"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-01"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎨 Visual Canvas & UI Engine Assimilation Reference

## 1. Architectural Model
When assimilating interactive visual tools (e.g. `open-design`, Excalidraw, Figma-like canvas engines, web studio builders):

```
┌─────────────────────────┐          WebSocket / JSON-RPC / MCP          ┌───────────────────────────────────┐
│ Visual Canvas Frontend  │ <==========================================> │ DNK OS Hub / Gerych Meta-Agent    │
│ (Open Design / Studio)  │                                              │ (Single SSOT Brain in DNK_HUB)    │
│                         │   Payload: Canvas AST / Atomic Mutations     │                                   │
│ - useGerychBridge hook  │ ───────────────────────────────────────────> │ - Hexagonal Canvas Adapter        │
│ - Optimistic Mutation Q │ <─────────────────────────────────────────── │ - SCONES Memory v2.0 (Design Sys) │
│ - Canvas Renderer       │         Generated UI / Style Updates         │ - TaskDNA / Swarm Multi-Agent     │
└─────────────────────────┘                                              └───────────────────────────────────┘
```

## 2. Invariants & Best Practices
1. **Zero Runtime Monolith Duplication**: NEVER copy the full Hermes/Gerych core or agent orchestration dependencies into the frontend canvas app. Keep all intelligence in `DNK_HUB` behind clean adapter ports.
2. **Atomic AST Mutations**:
   - Every modification to canvas elements must be represented as a deterministic mutation: `CREATE_NODE`, `UPDATE_NODE`, `UPDATE_STYLE`, `TRANSFORM`, `DELETE_NODE`, `REORDER_CHILDREN`.
   - The adapter must handle complete roundtrip serialization/deserialization of the Node AST.
3. **Design System & Memory Integration**:
   - Cache reusable design tokens, typography, and component blueprints inside SCONES Memory Engine.
   - Synchronize active session state and design palettes during conversational turns.
4. **Multi-Format Export Pipelines**:
   - The adapter should provide zero-dependency exporters to standard web formats (SVG, clean HTML/CSS flexbox bundles, and framework components).

## 3. Local CLI Agent Discovery vs Container Isolation & Native Daemon Hosting
When visual tools (like Open Design) scan for local AI agents (`hermes`, `claude`, `cursor`, `opencode`):
- **Container Isolation Pitfall**: Running the visual shell in a standard Docker container will result in `"Daemon is not running"` / `"No agents detected"` because the container's environment cannot scan the host's PATH (`~/.local/bin/hermes`) or host-authenticated provider sessions (Google Vertex, OpenAI tokens).
- **Dual Resolution Paths**:
  1. **Host Execution (Recommended for Local Agent)**: Run the visual frontend/daemon directly on the host (e.g. `node apps/daemon/bin/od.mjs --no-open` or `pnpm dev`). The host daemon natively detects `/Users/<user>/.local/bin/hermes` and inherits all active agent credentials without manual token copying.
  2. **Native Module & Node ABI Hygiene**: When backgrounding or launching native daemons with SQLite/C++ bindings (e.g. `better-sqlite3`), verify that the invoked Node binary (e.g. `/usr/local/bin/node` vs `/opt/homebrew/bin/node`) matches the `NODE_MODULE_VERSION` used during `pnpm install` / `pnpm rebuild`.
  3. **Dual-Tier Architecture & Port Separation (Daemon vs Web UI)**:
     - In full-stack visual tools (e.g., Next.js Frontend + Node/Express Daemon), the daemon on port `7456` serves API routes (`/api/agents`, `/api/health`, WebSocket channels) and will return `Cannot GET /` if opened directly in a browser.
     - The interactive user interface is served by the Next.js frontend tier on a dedicated port (e.g., `5173` or `3001`).
     - Use `pnpm exec tools-dev restart web --daemon-port 7456 --web-port 5173` to launch both tiers in harmony, avoid port conflicts with host/Docker services, and ensure seamless frontend-to-daemon communication.
  4. **BYOK / Gateway Mode (For Container Deployments)**: In containerized setups, use "Bring Your Own Key" (BYOK) in the UI or configure the container environment to communicate with the host's Gerych WebSocket gateway via `host.docker.internal:<port>`.

