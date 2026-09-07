# --- DNK-MRH-HEADER ---
# mrh_id: "skills_software_dev_canvas_engine_references_mind_map_spec"
# purpose: "Technical Specification and Invariants for Mind Map Nodes, Semantic Edges, PostgreSQL Storage, and WebSocket Sync (Phase 11)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# --- END DNK-MRH-HEADER ---

# Mind Map Spatial Nodes & Semantic Edges Specification (Phase 11)

## 1. Five Core Mind Map Node Types

| Node Type | Component | Visual Aesthetic | State Attributes & Data Schema |
|---|---|---|---|
| **Idea** | `MindMapIdeaNode.tsx` | Yellow Sticky Note 💡 (`#FEF08A`, border `#FACC15`) | `title: string`, `description: string`, `tags: string[]`, `confidence_score: number` (0.0 - 1.0) |
| **Goal** | `MindMapGoalNode.tsx` | Green Card 🎯 (`#DCFCE7`, border `#4ADE80`) | `title: string`, `deadline: string` (ISO), `metrics: Array<{name, target, current}>`, `status: 'not_started' \| 'in_progress' \| 'achieved'` |
| **Task** | `MindMapTaskNode.tsx` | Blue Card ✅ (`#DBEAFE`, border `#60A5FA`) | `title: string`, `assignee: string`, `priority: 'low' \| 'medium' \| 'high' \| 'urgent'`, `status: 'todo' \| 'doing' \| 'done'` |
| **Agent** | `MindMapAgentNode.tsx` | Orange Robot 🤖 (`#FFEDD5`, border `#FB923C`) | `agent_type: string`, `status: 'idle' \| 'thinking' \| 'running' \| 'completed'`, `last_execution: string`, `result: any` |
| **Evidence** | `MindMapEvidenceNode.tsx` | Purple Folder 📎 (`#F3E8FF`, border `#C084FC`) | `type: 'file' \| 'link' \| 'code'`, `url: string`, `preview: string` |

---

## 2. Four Semantic Mind Map Edge Types

| Edge Type | Component | Visual Style & Marker | Semantic Purpose & Behavior |
|---|---|---|---|
| **Dependency** | `DependencyEdge.tsx` | Red Arrow 🔒 (`stroke: #EF4444`, markerEnd: ArrowClosed, animated if blocking) | Strict blocking flow: Task A blocks Task B (`target` cannot execute until `source` status is `done`). |
| **Relation** | `RelationEdge.tsx` | Blue Wavy/Dashed 🔗 (`stroke: #3B82F6`, `strokeDasharray: '4 4'`) | Associative link between related ideas or goals (non-blocking knowledge connection). |
| **Cluster** | `ClusterEdge.tsx` | Gray Translucent Hull / Grouping 🌫️ (`stroke: #9CA3AF`, dashed) | Connects nodes belonging to the same auto-clustered semantic domain or topic group. |
| **Milestone** | `MilestoneEdge.tsx` | Purple Arrow 🚩 (`stroke: #A855F7`, markerEnd: Arrow, strokeWidth: 2.5) | Projects milestone path from an overarching Goal to critical deliverable nodes. |

---

## 3. Database Schema (PostgreSQL 16)

```sql
-- Mind Map Nodes Table
CREATE TABLE IF NOT EXISTS mind_map_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  canvas_id UUID NOT NULL,
  type VARCHAR(64) NOT NULL, -- idea, goal, task, agent, evidence
  position_x FLOAT NOT NULL DEFAULT 0.0,
  position_y FLOAT NOT NULL DEFAULT 0.0,
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mind_map_nodes_canvas_id ON mind_map_nodes(canvas_id);

-- Mind Map Edges Table
CREATE TABLE IF NOT EXISTS mind_map_edges (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  canvas_id UUID NOT NULL,
  source_node_id UUID NOT NULL REFERENCES mind_map_nodes(id) ON DELETE CASCADE,
  target_node_id UUID NOT NULL REFERENCES mind_map_nodes(id) ON DELETE CASCADE,
  type VARCHAR(64) NOT NULL, -- dependency, relation, cluster, milestone
  data JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mind_map_edges_canvas_id ON mind_map_edges(canvas_id);
```

---

## 4. WebSocket Synchronization Protocol

Client-to-Server and Server-to-Client payloads:
```typescript
// Node Creation
{
  type: 'MINDMAP_NODE_CREATE',
  nodeId: 'idea-001',
  data: {
    type: 'idea',
    title: 'ReBurn Founder Strategy',
    description: 'Email automation campaign...',
    tags: ['marketing', 'reburn'],
    confidence_score: 0.85
  },
  position: { x: 250, y: 180 }
}

// Edge Creation
{
  type: 'MINDMAP_EDGE_CREATE',
  edgeId: 'edge-dep-001',
  source: 'task-001',
  target: 'task-002',
  edgeType: 'dependency',
  data: { label: 'Blocks deploy' }
}
```

---

## 5. Definition of Done (DoD) Verification Checklist

- [ ] All 5 node components rendered via `@xyflow/react` `nodeTypes` map in `CanvasEngine.tsx`.
- [ ] All 4 edge types registered in `edgeTypes` map with corresponding custom SVG markers and path styling.
- [ ] Side palette drag-and-drop spawning correctly passes `application/reactflow` metadata and coordinates.
- [ ] Context menu on nodes triggers edit modal, deletion, or new edge creation.
- [ ] PostgreSQL serialization round-trip: nodes and edges persisted via FastAPI REST / WebSocket endpoints with 100% test coverage.
