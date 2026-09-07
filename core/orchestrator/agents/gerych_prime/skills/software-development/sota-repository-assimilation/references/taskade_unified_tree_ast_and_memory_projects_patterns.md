# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/taskade_unified_tree_ast_and_memory_projects_patterns.md"
# purpose: "SOTA assimilation patterns from Taskade: Unified Tree AST with Delta OT, Memory as Projects, Workspace DNA, and AI Elements."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# Taskade Architecture Patterns: Unified Tree AST, Delta OT & Memory-as-Projects

## 1. Unified Hierarchical Tree AST (Multi-View Projections)
Instead of maintaining separate schemas for lists, kanban boards, mind maps, calendars, and infinite canvases, Taskade uses a single canonical data structure:

```typescript
// Core Taskast Node structure (Quill Delta compatible)
interface Node {
  type: 'text';
  id: string;
  text: { ops: DeltaOp[] }; // Rich-text operations (insert, delete, retain)
  format: { node?: string; children?: string }; // Layout semantics
  collapsed?: boolean;
  completed?: boolean;
  attributes?: Record<string, any>; // Extensible metadata & custom fields
  children: Node[]; // Recursive AST tree
}
```

### Projection Invariant:
- **List View**: Depth-first preorder traversal with indentation.
- **Board (Kanban) View**: Level-1 nodes become columns; level-2+ nodes become cards.
- **Mind Map View**: Root at center, level-1 branches radiated outward, child sub-branches.
- **Table / Database View**: Flattened rows with `attributes` mapped to column definitions.
- **Infinite Canvas**: 2D coordinate positioning (`attributes.position = {x, y}`) with connective edges between node IDs.
Switching views requires **zero data migration or schema mutation** — it is purely a frontend projection lens over the same AST.

---

## 2. Mathematical Operational Transformation (Delta OT Engine)
The `taskade/delta` engine provides convergence for concurrent human and AI edits:
- Operations: `insert(text, attributes)`, `retain(length, attributes)`, `delete(length)`.
- Core functions: `compose(deltaA, deltaB)`, `diff(deltaA, deltaB)`, `transform(deltaA, deltaB, priority)`.
- Avoids distributed lock contention and merge conflicts when multiple swarm agents mutate project nodes simultaneously.

---

## 3. "Memory as Projects" Architectural Pattern
Most agent platforms hide long-term memory in opaque vector DB blobs (e.g. Chroma, Pinecone), preventing user inspection and manual corrections.

### Taskade Paradigm:
- Agent Long-Term Memory (LTM) **is a standard Project in the workspace**.
- Memory is structured as readable hierarchical nodes (facts, rules, preferences, completed workflows).
- **Benefits**:
  1. **100% Transparent**: User browses memory as a normal outline or kanban board.
  2. **User-Editable**: User can directly correct or delete hallucinated facts without DB resets.
  3. **API & Tool Addressable**: Agents query and mutate memory using the exact same CRUD tools used for user tasks.
- **DNK OS Dual-Layer Integration**:
  - *Layer A (Visual/User-Facing)*: Memory-as-Project tree on Canvas.
  - *Layer B (Vector/Retrieval)*: SCONES / LightRAG dual-level entity graph for sub-second retrieval.

---

## 4. Workspace DNA (`SpaceBundleData`)
Portability standard packaging entire living systems into a single JSON/archive:
- `agents`: Persona, tone, LLM parameters, toolboxes, and commands (`default`, `plan-and-execute-v1`, `plan-and-execute-v2`).
- `automations`: `FlowTemplateV2` DAGs (event triggers, conditions, automated actions).
- `projects`: Canonical `TaskastRoot` trees.
- `apps`: Sandboxed interactive micro-applications (React / Vite).

---

## 5. Cortex UI `ai-elements` Pattern
For AI-native interfaces, Taskade decouples chat into reusable atomic primitives:
- `chain-of-thought.tsx`: Collapsible reasoning blocks showing model thought processes.
- `tool.tsx`: Visual feedback of tool invocations, inputs, and execution statuses.
- `inline-citation.tsx` & `sources.tsx`: Direct references back to memory project nodes.
- `confirmation.tsx`: Human-in-the-Loop approval cards for high-stakes tool actions.
