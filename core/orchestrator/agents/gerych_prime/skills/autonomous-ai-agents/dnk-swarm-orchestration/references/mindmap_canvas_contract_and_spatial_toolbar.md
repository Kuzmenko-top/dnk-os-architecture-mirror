# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/mindmap_canvas_contract_and_spatial_toolbar.md"
# purpose: "Architecture contract, spatial toolbar spawn, and verification matrix for Mind Map nodes and custom edges in DNK OS Canvas."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧠 Mind Map Nodes, Custom Edges & Spatial Toolbar Contract Protocol

## 1. Context & Architecture Overview
In DNK OS Canvas (`apps/web/components/canvas/`), Mind Mapping forms the spatial foundation for ideation, swarm agent assignment, task tracking, and evidence synthesis. To prevent runtime React Flow blank nodes or broken edge connections, all nodes and edges adhere to a strict structural contract.

## 2. Canonical Node & Edge Primitives

### Mind Map Nodes (`apps/web/components/canvas/nodes/`)
1. **`BaseMindMapNode.tsx`**: Abstract foundation providing standard obsidian glass styling (`#060913`), top-left icon badges, title/description editable inputs, and 4-directional connection handles (`source` / `target` on all 4 quadrants).
2. **`MindMapIdeaNode.tsx`** (💡 `mindmap_idea`): Brainstorming, insight tags, and confidence scores.
3. **`MindMapGoalNode.tsx`** (🎯 `mindmap_goal`): Strategic milestones, target deadlines, KPI metrics, and progress percentages.
4. **`MindMapTaskNode.tsx`** (✅ `mindmap_task`): Atomic tasks with status (`todo`, `in_progress`, `completed`), priority (`low`, `medium`, `high`, `urgent`), and swarm assignee.
5. **`MindMapAgentNode.tsx`** (🤖 `mindmap_agent`): Swarm worker mapping (`gerych_prime`, `gerych_builder`, `dnk_shopify`, etc.) with real-time status.
6. **`MindMapEvidenceNode.tsx`** (📎 `mindmap_evidence`): Verifiable artifacts, documents, logs, and audit reports with target URIs.

### Custom Edges (`apps/web/components/canvas/edges/`)
1. **`DependencyEdge.tsx`**: Directional execution blocking (`A -> B`).
2. **`RelationEdge.tsx`**: Conceptual / semantic associations (`A <-> B`).
3. **`MilestoneEdge.tsx`**: High-level timeline / sprint progress flow.

## 3. Dual-Casing Registration Invariant
React Flow instances and serialised canvas schemas may reference node and edge types using either PascalCase or camelCase.
- **`apps/web/components/canvas/NodeRegistry.ts`**:
  Must register all types in `NODE_REGISTRY_MAP`.
- **`apps/web/components/canvas/CanvasEngine.tsx`**:
  Must register both casings in `nodeTypes`:
  ```tsx
  const nodeTypes = {
    // ...
    MindMapIdeaNode,
    mindMapIdea: MindMapIdeaNode,
    MindMapGoalNode,
    mindMapGoal: MindMapGoalNode,
    MindMapTaskNode,
    mindMapTask: MindMapTaskNode,
    MindMapAgentNode,
    mindMapAgent: MindMapAgentNode,
    MindMapEvidenceNode,
    mindMapEvidence: MindMapEvidenceNode,
  };
  ```
  And similarly in `edgeTypes` (`DependencyEdge`, `dependency`, `RelationEdge`, `relation`, etc.).

## 4. Spatial Toolbar Quick Spawn Invariant
In `apps/web/components/canvas/StitchSpatialToolbar.tsx`:
- Provide a dedicated **Mind Map subgroup** with distinct icons (`Lightbulb`, `Target`, `CheckSquare`, `Bot`, `Paperclip`), localized labels, and tooltips.
- **Dual-Mode Spawning**:
  1. **Click-to-Spawn**: Calls `useCanvasStore.getState().addNode(nodeType, { x: 350 + offset, y: 250 + offset }, defaultData)`. Applying a random spatial offset ($\pm 40\text{px}$) prevents consecutive spawned nodes from stacking directly on top of each other.
  2. **Drag-and-Drop**: Elements specify `draggable` with `e.dataTransfer.setData('application/reactflow', nodeType)` and `setData('application/reactflow-data', JSON.stringify(defaultData))` for spatial drop positioning.

## 5. Contract Test Verification Pattern
Always provide an automated Python contract test (`tests/canvas/test_mindmap_nodes_edges_contract.py`) verifying:
- All 6 node files and 3 edge files exist at expected relative paths.
- Default exports and TypeScript interfaces are declared.
- Mandatory `DNK-MRH-HEADER` headers exist.
- Node and edge registrations exist in `NodeRegistry.ts` and `CanvasEngine.tsx`.
- Toolbar contains quick-spawn buttons for all 5 Mind Map primitives.
- Execute via `.venv/bin/pytest tests/canvas/test_mindmap_nodes_edges_contract.py -v`.
