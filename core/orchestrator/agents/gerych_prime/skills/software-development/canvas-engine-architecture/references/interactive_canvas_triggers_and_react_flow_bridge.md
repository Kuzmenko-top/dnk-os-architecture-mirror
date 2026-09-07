# Interactive Canvas-to-Swarm Triggers, Live Post-Tool Hook HUD & React Flow SSOT Bridge

## 1. Real-Time Zero-Code Dashboard via Post-Tool Hook
- **Integration**: `scripts/system/hermes_post_tool_hook.py` executes on every Hermes tool completion, passing `tool_name`, `status`, `duration_ms`, and `output_snippet`.
- **Canvas Lifecycle Hook**:
  - `VisualCanvasControlEngine().record_live_tool_execution(tool_name, tool_status, execution_time, active_agent, target_file, canvas_path)`
  - Tool execution increments `tools_count` in the Master HUD card and updates runtime status (`🟢 ACTIVE: executing <tool>` or `🔴 FAILING`).
  - File mutations (`write_file`, `patch`) switch the active TaskDNA node on the canvas to `color: "5"` (Cyan/In Progress).
  - Test suites (`terminal` containing `pytest` or `verify_all.sh`) switch the active node to `color: "4"` (Green/Done) on pass, or `color: "1"` (Red/Failed) on failure.

## 2. Interactive Canvas-to-Swarm Triggers & Watchdog Daemon
- **Two-Way Control**: Users or architects can trigger actions directly inside Obsidian Canvas by checking markdown boxes in node text:
  - `- [x] Run Tests` / `- [x] Verify All`: Executes `bash scripts/verify_all.sh` or targeted pytest command, updates node badge to `✅ [Tests Passed] (HH:MM:SS)`.
  - `- [x] Dispatch Worker: <agent>` / `- [x] Dispatch Worker`: Extracts worker name, dispatches task via `dnk_swarm_dispatch(agent=agent, task_description=...)`, switches node color to `5`, and annotates with `🚀 [Dispatched <agent>]`.
- **Watchdog Execution**:
  - `python3 scripts/system/visual_canvas_control_runner.py --poll-triggers` (one-off poll).
  - `python3 scripts/system/visual_canvas_control_runner.py --watch 2.0` (daemon loop with interval).

## 3. Bidirectional SSOT Bridge: Obsidian Canvas <-> React Flow
- **Obsidian Canvas JSON Format**:
  - Uses `nodes` (`id`, `x`, `y`, `width`, `height`, `type="text"|"file"|"group"`, `text`, `color`), `edges` (`id`, `fromNode`, `toNode`, `label`).
- **React Flow Format**:
  - Uses `nodes` (`id`, `type="taskForestNode"|"default"`, `position: {x, y}`, `style: {width, height}`, `data: {label, text, status, color, ...}`), `edges` (`id`, `source`, `target`, `label`).
- **Translation Engine**:
  - `VisualCanvasControlEngine.canvas_to_react_flow(canvas_path)`: Converts JSON Canvas into standard React Flow state dictionary.
  - `VisualCanvasControlEngine.react_flow_to_canvas(rf_data, output_path)`: Translates React Flow state back into valid JSON Canvas.
  - CLI commands: `--export-react-flow <path>` and `--import-react-flow <path>`.

## 4. FastAPI REST Endpoints (`apps/api/routers/canvas_bridge.py`)
- Exposes production REST interface connected to `apps/api/main.py`:
  - `GET /api/v1/canvas/bridge/status`: Verifies bridge engine availability and default canvas paths.
  - `GET /api/v1/canvas/bridge/obsidian`: Reads target `.canvas` file and returns serialized React Flow `{ nodes, edges, file_path }`.
  - `POST /api/v1/canvas/bridge/react-flow-to-canvas`: Translates React Flow payload and persists it to target `.canvas` file.
  - `POST /api/v1/canvas/bridge/convert/canvas-to-flow`: In-memory conversion of Obsidian Canvas JSON into React Flow.
  - `POST /api/v1/canvas/bridge/convert/flow-to-canvas`: In-memory conversion of React Flow JSON into Obsidian Canvas.
  - `POST /api/v1/canvas/bridge/merge`: Triggers zero-loss OCC 3-way merge (`incoming_flow`, `base_flow`, `canvas_path`, `persist_to_disk`, `position_strategy`) against disk state (`theirs`) using `OCCConcurrencyEngine.three_way_merge`.
  - `POST /api/v1/canvas/bridge/trigger-check`: Triggers checkbox scan (`- [x] Run Tests`, `- [x] Dispatch Worker`) and executes pending actions.
  - `POST /api/v1/canvas/bridge/sync-master`: Regenerates TaskDNA Master HUD Canvas.

## 5. TypeScript Shared Contracts (`apps/web/types/canvasBridge.ts`)
- Strict type definitions for React Flow ↔ Obsidian synchronization:
  - `ObsidianCanvasNode`, `ObsidianCanvasEdge`, `ObsidianCanvasData`.
  - `ReactFlowNode`, `ReactFlowEdge`, `ReactFlowData`.
  - `CanvasSyncRequest`, `CanvasSyncResponse`, `TriggerCheckResponse`.

## 6. Worker Badge Parsing & Formatting Invariant
- **Markdown Backticks Sanitization**:
  - When extracting worker tags via regex `\*\*Worker\*\*:\s*([^\n]+)`, architects or generators may format worker names as ``dnk_dev_fullstack`` or `dnk_dev_fullstack`.
  - Always clean names using `.strip().strip("`")` before mapping against `REVERSE_AGENT_BADGES` to prevent fallback to `gerych_builder`.

## 7. Real-Time Bidirectional WebSocket Stream (`/api/v1/canvas/bridge/ws`)
- **Connection Handshake**:
  - Accepts `canvas_path` query parameter (defaults to Master Control Panel Canvas).
  - Immediately transmits `INITIAL_STATE` event with `react_flow` payload, `node_count`, and `edge_count`.
- **Reactive Background FileWatcher (Push vs Polling)**:
  - An asynchronous background task (`file_watcher`) polls `os.path.getmtime(canvas_path)` every `0.5s`.
  - When the `.canvas` file on disk is modified externally (e.g. edited by user in Obsidian), the server pushes a `{"type": "CANVAS_UPDATE", "source": "file_watcher", "canvas_path": "...", "react_flow": {...}}` event automatically without client polling.
  - **Echo Suppression Invariant**: On client-initiated `{"action": "update"}`, `last_mtime` is synchronized immediately after writing to disk to prevent redundant echo-back events.
  - **Task Lifecycle**: The `file_watcher` task is cleanly cancelled (`watcher_task.cancel()`) in the handler's `finally:` block upon WebSocket disconnect.
- **Bidirectional Event Protocol**:
  - `{"action": "ping"}` ➔ Responds with `{"type": "PONG", "status": "ok"}` for keepalive.
  - `{"action": "refresh"}` ➔ Reads on-disk `.canvas` file and broadcasts `{"type": "CANVAS_UPDATE", "source": "refresh", "react_flow": {...}}`.
  - `{"action": "trigger_check"}` ➔ Runs `poll_and_execute_canvas_triggers()`, returns triggered action list and updated React Flow graph in `{"type": "TRIGGER_EXECUTED", ...}`.
  - `{"action": "update", "react_flow": {...}}` ➔ Serializes React Flow nodes/edges to `.canvas` format, writes to disk, and acknowledges with `{"type": "SAVED", "status": "success"}`.
  - `{"action": "merge", "incoming_flow": {...}, "base_flow": {...}}` (or `action: "update"` with `base_flow`): Executes deterministic OCC 3-way merge between `base_flow`, on-disk `theirs` canvas, and `incoming_flow` (`mine`), persists merged canvas, updates `last_mtime` to prevent echo loops, and acknowledges with `{"type": "CANVAS_MERGED", "status": "success", "react_flow": {...}, "conflicts": [...]}`.

## 8. Client-Side Sync Resilience & REST Fallback (`canvasStore.ts`)
- **Transport Degradation Gracefulness**:
  - Web UI attempts WebSocket synchronization first for zero-latency streaming.
  - If the socket encounters connection drops or transport errors, `canvasStore.syncToObsidian` seamlessly degrades to REST endpoints via `canvasApiClient.exportToObsidianCanvas` and `canvasApiClient.importFromObsidianCanvas`.
  - UI state transitions remain non-blocking, ensuring zero freezing during agent handoffs.
- **Path Hygiene Standard**:
  - Never use absolute paths (e.g. `~/Documents/DNK_HUB My Notes/...` or `/Users/...`).
  - Always default to `./docs/notes` across components (`ObsidianSyncBar.tsx`), stores, and CLI scripts to guarantee cross-machine compatibility.

## 9. Telemetry & Accounting Log Retention Invariant
- **Bounded Disk Retention (`max_records: int = 5000`)**:
  - Long-running daemons, test runners, and telemetry collectors emitting events into persistent JSON files (`accounting_log.json`, `sentinel_alerts.json`) must maintain bounded FIFO records.
  - Truncation slice (`records = records[-max_records:]`) must be enforced before every atomic serialization to prevent memory leaks and disk exhaustion.
