# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/canvas-engine-architecture/references/task_forest_spatial_canvas_architecture.md"
# purpose: "Task Forest Multi-Tree Architecture, Event-Sourced Time-Travel, Cross-Tree Edges, and Visual Steering Protocol."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych Prime & Maxim Kuzmenko"
# --- END DNK-MRH-HEADER ---

# 🌲 Task Forest & Multi-Tree Spatial Agentic Orchestration

## 1. Context & Motivation
Conventional agent orchestrators operate inside a 1D linear chat stream or flat Kanban backlog (`Todo -> In Progress -> Done`). In complex multi-agent swarms (e.g. 14 domain workers across Shopify, Video AI, Backend, Memory, Security), this creates:
1. **Context Blindness**: Loss of global topology, bottlenecks, and dependency paths.
2. **Flat DAG Fallacy**: Development is heuristic tree search (`Tree-of-Thought`), not a linear assembly line.
3. **Loss of Causal Lineage**: Git records file diffs, but loses prompt, agent rationale, error distillation, and test telemetry.
4. **Steering Inflexibility**: No mechanism to branch, pause, or adjust a sub-tree without terminating the session.

The solution is the **Task Forest Spatial Canvas Architecture**.

---

## 2. Four Canonical Trees of the Task Forest

Rather than a single monolithic graph, the canvas maintains a **Forest of Decoupled, Interconnected Trees**:

```text
Task Forest
├── 🌲 Tree 1: Knowledge & Memory Tree (SCONES)
│   ├── Root: Workspace Brand Identity & Architecture Invariants
│   └── Leaves: Palette Tokens, Tone of Voice, DTO Contracts, Safe Boundaries
├── 🌲 Tree 2: Product Delivery Tree (TaskDNA)
│   ├── Root: Epic / Release Milestone
│   └── Leaves: Domain Subtasks (apps/web, services/dnk_shopify, packages/teleprompter-core)
├── 🌲 Tree 3: R&D & Hypothesis Tree (Spikes & Self-Healing)
│   ├── Root: Architectural Spikes & Error Solutions
│   └── Leaves: Parallel Worker Explorations (Failed branches become Negative Memory)
└── 🌲 Tree 4: Quality & Adversarial Gate Tree (Auditor vs Builder)
    ├── Root: Master Quality Gate (scripts/verify_all.sh)
    └── Leaves: Unit Tests, Contract Validations, Regression Tests, Evidence Certification
```

---

## 3. Data Model: Event-Sourced Node Capsules (`TaskForestNode`)

Every task node is an event-sourced time capsule preserving complete execution lineage:

```typescript
export type TaskTreeNodeType = 'memory' | 'product' | 'research' | 'quality_gate';

export type TaskStatus = 
  | 'draft'
  | 'queued'
  | 'leased'
  | 'running'
  | 'blocked'
  | 'succeeded'
  | 'failed'
  | 'degraded';

export interface NodeEventRecord {
  timestamp: string; // ISO-8601
  actor: 'human' | 'agent';
  actorId: string; // e.g. 'maxim' | 'gerych_builder' | 'dnk_shopify'
  action: 'spawn' | 'prompt_injected' | 'tool_call' | 'diff_applied' | 'test_run' | 'steer';
  payload: Record<string, unknown>;
}

export interface TaskForestNode {
  id: string; // e.g. "task_tree2_shopify_ast_001"
  treeId: string; // "tree_product"
  treeType: TaskTreeNodeType;
  parentId?: string;
  childIds: string[];
  title: string;
  status: TaskStatus;
  
  // Execution Context
  agentAssigned?: string;
  systemPrompt?: string;
  workingDirectory: string;
  targetFiles: string[];
  
  // Provenance & Lineage
  eventLog: NodeEventRecord[];
  gitDiffSnapshot?: string;
  testReport?: {
    passed: boolean;
    exitCode: number;
    command: string;
    summary: string;
  };
  
  // Visual Position on Infinite Canvas
  position: { x: number; y: number };
}
```

---

## 4. Reactive Cross-Tree Edges (`CrossTreeEdge`)

Nodes connect within their tree (parent-child hierarchical edges) and across different trees (reactive data-flow edges):

```typescript
export interface CrossTreeEdge {
  id: string;
  sourceNodeId: string;
  targetNodeId: string;
  edgeType: 'dependency' | 'data_flow' | 'healing_trigger' | 'verification_gate';
  status: 'active' | 'blocked' | 'satisfied';
}
```

- **Dependency Edge**: Blocks target node transition from `queued` to `running` until source reaches `succeeded`.
- **Data Flow Edge**: Transmits upstream outputs (e.g. DTO schema changes from Tree 1) directly to downstream inputs in Tree 2.
- **Healing Trigger Edge**: When a test fails in Tree 4, a healing node is dynamically spawned in Tree 2 with error distillation context.

---

## 5. Time-Travel & Evolutionary Visual Steering Protocol

1. **Timeline Scrubber**:
   - The user or agent slides the timeline cursor to inspect previous snapshots of the canvas.
   - Snapshots are computed via deterministic RFC 6902 reverse patch application over IndexedDB ring buffers.
2. **Visual Branching (Forking)**:
   - Right-click on any historical node state -> `[Fork Alternative Hypothesis]`.
   - The existing failed/stalled branch transitions to `degraded` (retained as negative memory), and a clean sibling node is spawned for the swarm.
3. **In-Flight Steering**:
   - Human updates inputs or constraints directly inside the node's visual inspector.
   - The node issues a high-priority `user_steer` event over the WebSocket bridge (`/api/v3/canvas/ws`), pausing execution safely between tool iterations.
