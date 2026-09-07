# Spatial Nodes, WebSocket Bridge & Visual Co-Working Architecture (DNK Studio Canvas)

## 1. Core Spatial Nodes
- **`SwarmAgentNode`**: Connects directly to `/api/v3/canvas/ws`. Streams real-time thoughts (`SWARM_THOUGHT`), logs (`SWARM_LOG`), and responses (`SWARM_RESPONSE`). Allows user command dispatch to swarm agents (`SWARM_COMMAND`).
- **`ShopifyBuilderNode`**: Interactive visual configuration of Shopify OS 2.0 sections, multi-device preview (Desktop/Tablet/Mobile), and Liquid compilation/deployment triggers (`/api/shopify/build`).
- **`VideoCreatorNode`**: Remotion/Diffusion video generation card with aspect ratio selector (9:16 vertical shorts, 16:9 cinematic, 1:1 square), prompt input, animation presets, and render pipeline (`/api/video`).
- **`SmartNoteNode`**: Markdown-capable notes, checklists, color-tagged badges, and 4-directional connection ports.

## 2. Interactive Node Lifecycle & Studio Dock
- **Studio Dock Spawning**: Bottom dock (`StudioDock.tsx`) provides quick-action buttons (`+ Swarm`, `+ Shopify`, `+ Video`, `+ Smart Note`) which trigger `handleSpawnNode(type)` in `DNKStudioWorkspace.tsx`.
- **Non-Overlapping Layout**: New nodes spawn at staggered viewport offsets (`x = 250 + (count % 4) * 80, y = 200 + (count % 4) * 80`) to ensure clean spatial visibility.
- **Node Deletion & Edge Cascading**: Nodes can be deleted via `InspectorPanel.tsx` (`onDeleteNode(id)`). Deleting a node automatically cascades and removes all associated `edges` (`source === id || target === id`).

## 3. Local Persistence Engine
- **Storage Keys**: `dnk_studio_canvas_nodes` and `dnk_studio_canvas_edges` in `localStorage`.
- **Debounced Auto-Save**: Any spatial displacement, node edit, or connection modification auto-saves to `localStorage` (1000ms debounce).
- **Reset Layout**: Clears `localStorage` and restores the canonical default 4-node topology.
- **Import / Export**: Full JSON export/import for spatial topology backup and sharing across workstations.

## 4. Real-Time Swarm WebSocket Bridge Protocol
- **Endpoint**: `/api/v3/canvas/ws` (with fallback to `/api/v3/ws/canvas/{canvas_id}`).
- **Event Types**:
  - `SWARM_COMMAND`: Payload `{ "command": str, "target_agent": str }` dispatched to swarm router.
  - `SWARM_THOUGHT`: Real-time streaming thoughts of the agent.
  - `SWARM_LOG`: Terminal output lines from build/test/execution steps.
  - `SWARM_RESPONSE`: Final structured answers and artifacts.
  - `PRESENCE_UPDATE`: Multi-agent presence across canvas nodes.

## 5. Excalidraw & Visual Canvas Co-Working Protocol
- **Visual Brainstorming & Planning**: Users sketch diagrams and ideas on Excalidraw / Spatial Canvas tabs.
- **Canvas-to-Code Pipeline**: Gerych Prime parses the canvas JSON/WebSocket state into TaskDNA dependency DAGs, mapping blocks to files (`apps/...`, `services/...`) and assigning sub-agents.
- **Bidirectional Telemetry**: Real-time status badges (🟡 In Progress, 🟢 Verified 100% Green, 🔴 Test Failure) and agent thought streams update directly on the canvas nodes.
- **Artifact Delivery Invariant**: For architectural briefings and system designs, always produce both a human-readable, structured `.md` file in `docs/architecture/` with DNK-MRH headers AND a native `.excalidraw` vector file for zero-friction drag-and-drop viewing. Never rely solely on ASCII/raw-markdown text pasting into Excalidraw.
