# Archify Spatial Node & A2A Live Mesh Telemetry Integration

## 🗺️ Spatial Architecture Overview
Archify spatial diagrams (`ArchifySpatialNode.tsx`) integrate directly into the DNK OS Infinite Canvas as first-class React Flow custom nodes under category `'architecture'`.

### 1. Canvas Node Contract & Registration
- **Node Component**: `apps/web/components/canvas/nodes/ArchifySpatialNode.tsx`
- **Registry**: `apps/web/components/canvas/NodeRegistry.ts` (category: `'architecture'`, icon: `Layers`, 4-way handles)
- **Canvas Binding**: `apps/web/components/canvas/DNKCanvas.tsx` registered in `nodeTypes` map:
  ```tsx
  const nodeTypes = {
    // ...
    ArchifySpatialNode,
    archifySpatial: ArchifySpatialNode,
    archifyNode: ArchifySpatialNode,
  };
  ```

### 2. Node Capabilities & Interaction Modes
- **4-Way Connection Handles**: Top, Bottom, Left, and Right connection points supporting typed data edges to `SwarmAgentNode`, `GoalNode`, and `TaskForestSpatialNode`.
- **Live Metrics Ribbon**: Instant visibility of codebase complexity (Routers, Endpoints, Adapters, Swarm Workers).
- **Dual Focus Lenses**: Interactive toggle between `Primary Flow` (operational runtime path) and `State & Memory` (persistence, SCONES, and cache boundaries).
- **Spatial Presentation Modal**: In-canvas modal expanding the interactive SVG diagram into a full-screen iframe viewer with pan, zoom, and node inspection.

### 3. Live A2A Mesh Telemetry Bridge
- **Asset**: `packages/archify/assets/archify_telemetry_bridge.js`
- **Protocol**: Connects to `/ws/a2a` WebSocket stream.
- **Visual Feedback**: Matches incoming agent dispatch/routing packets with diagram SVG element IDs (`#node-<id>`, `#conn-<id>`), rendering real-time animated glowing pulses along active communication edges.
- **Resilience**: Features automatic heartbeat simulation fallback when disconnected or operating in offline demonstration mode.

### 4. Zero-Disk AST Generation
The node reflects diagrams compiled on the fly by `DNKArchifyAdapter`:
```python
from core.adapters.dnk_archify_adapter import DNKArchifyAdapter

adapter = DNKArchifyAdapter()
result = adapter.generate_live_repo_architecture(output_path="docs/diagrams/dnk_hub_architecture.html")
# Zero-disk I/O pipeline compiles AST metrics into self-contained HTML in memory
```
