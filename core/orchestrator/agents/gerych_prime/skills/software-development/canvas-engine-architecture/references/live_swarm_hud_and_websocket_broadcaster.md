# Live Swarm HUD & WebSocket Broadcaster Specification

## 1. Architectural Overview
The Live Swarm HUD visualizes swarm worker lifecycle states in real time on both Obsidian Canvas and React Flow without requiring full canvas file reloads or manual polling.

```
       [ Swarm Orchestrator / Worker ]
                      │
           (REST POST /events/swarm)
                      ▼
         [ CanvasBridge Router ]
         ┌─────────────────────┐
         │ - Agent Badge Lookup│
         │ - Palette Hex/Color │
         │ - Optional Disk Sync│
         └──────────┬──────────┘
                    │ broadcast_swarm_event()
                    ▼
     [ CanvasBridgeConnectionManager ]
        │                           │
        ▼ (WS: canvas_path)         ▼ (WS: global HUD)
  [ Active Canvas Client ]    [ Swarm Telemetry Monitor ]
```

## 2. Worker Identity & Color Tokens (`SWARM_WORKER_COLORS`)
Canonical mapping of swarm agents to canvas color codes (JSON Canvas 1-6) and UI Hex tokens:

| Agent Identifier | Role / Badge | Canvas Color | Hex Token | Stage Mapping |
| :--- | :--- | :---: | :---: | :--- |
| `gerych_prime` | 👑 Gerych Prime | `6` (Purple) | `#8B5CF6` | `plan` |
| `antigravity_mentor` | 🧠 Antigravity | `6` (Purple) | `#A78BFA` | `plan` |
| `gerych_builder` | 🛠️ Gerych Builder | `5` (Blue) | `#3B82F6` | `in_progress` |
| `dnk_dev_fullstack` | ⚡ DNK Dev Fullstack | `5` (Cyan) | `#06B6D4` | `in_progress` |
| `dnk_shopify` | 🛍️ DNK Shopify Engine | `4` (Green) | `#10B981` | `done` |
| `dnk_video_ai_creator` | 🎬 DNK Video AI Creator | `2` (Amber) | `#F59E0B` | `in_progress` |
| `gerych_auditor` | 🛡️ Gerych Auditor | `1` (Red) | `#EF4444` | `blocked` / `test` |
| `dnk_security_guard` | 🔒 DNK Security Guard | `1` (Dark Red) | `#DC2626` | `blocked` |
| `herich_librarian` | 📚 Herich Librarian | `3` (Yellow) | `#EAB308` | `backlog` / `archive` |

## 3. Event Protocol & Payload Formats
WebSocket message format delivered to frontend React Flow clients:
```json
{
  "type": "SWARM_HUD_EVENT",
  "canvas_path": "./docs/notes/014 Live Canvas.canvas",
  "task_id": "task-001",
  "event_type": "TASK_PROGRESS",
  "assigned_agent": "gerych_builder",
  "agent_badge": "🛠️ Gerych Builder",
  "canvas_color": "5",
  "hex_color": "#3B82F6",
  "stage": "in_progress",
  "progress_pct": 65,
  "progress_bar": "██████▒▒▒▒ 65%",
  "message": "Synthesizing UI components",
  "timestamp": "2026-09-06T12:00:00Z"
}
```

## 4. Endpoints & WebSocket Commands
- **REST**:
  - `POST /api/v1/canvas/bridge/events/swarm`
  - `POST /api/v1/canvas/bridge/swarm-hud` (alias)
  - Payload: `SwarmHudEventRequest(task_id, event_type, assigned_agent, progress_pct, message, canvas_path, update_canvas_disk)`
- **WebSocket Action**:
  - Send: `{"action": "swarm_event", "task_id": "...", "event_type": "TASK_STARTED", "assigned_agent": "gerych_builder"}`
  - Receives ack: `{"type": "SWARM_EVENT_ACK", "task_id": "...", "status": "broadcasted"}`
  - Broadcasts: `SWARM_HUD_EVENT` to all connected clients.
