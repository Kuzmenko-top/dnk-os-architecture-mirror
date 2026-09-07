# --- DNK-MRH-HEADER ---
# mrh_id: "references/dag_canvas_cycle_prevention_and_ai_decomposition.md"
# purpose: "Reference architecture for ReactFlow Drag-to-Connect cycle prevention, dual schema mapping, and AI-driven Epic DAG decomposition."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "Hermes Agent (gerych_prime)"
# --- END DNK-MRH-HEADER ---

# DAG Canvas Drag-to-Connect Cycle Prevention & AI Epic Decomposition

## 1. Client-Side Drag-to-Connect Validation Pattern (ReactFlow / XYFlow)

### Self-Loop and Transitive Cycle Guard (`isValidConnection`)
When users drag an edge handle to connect nodes in a DAG (Directed Acyclic Graph) canvas, cycles must be intercepted BEFORE dispatching mutation requests:
1. **Self-Loop Check**: Reject if `connection.source === connection.target`.
2. **Duplicate Edge Check**: Reject if an edge between source and target already exists.
3. **Transitive Reachability Check (Cycle Detection)**:
   - Perform a BFS/DFS from `connection.target` following outgoing edges.
   - If `connection.source` is reachable from `connection.target`, adding the edge `source -> target` would create a cycle (`source -> target -> ... -> source`).
   - Immediately return `false` from `isValidConnection` to prevent the drop, and fire an interactive UI toast (`"Неможливо створити цикл у графі завдань"`).

```typescript
const isValidConnection = useCallback(
  (connection: Connection) => {
    if (!connection.source || !connection.target) return false;
    if (connection.source === connection.target) return false;

    // Check transitive reachability to prevent DAG cycles
    const hasPath = (start: string, goal: string): boolean => {
      const visited = new Set<string>();
      const queue = [start];
      while (queue.length > 0) {
        const curr = queue.shift()!;
        if (curr === goal) return true;
        visited.add(curr);
        const nextNodes = edges
          .filter((e) => e.source === curr)
          .map((e) => e.target)
          .filter((id) => !visited.has(id));
        queue.push(...nextNodes);
      }
      return false;
    };

    if (hasPath(connection.target, connection.source)) {
      setToast({
        message: 'Неможливо створити цикл у графі завдань',
        type: 'error',
      });
      return false;
    }
    return true;
  },
  [edges]
);
```

---

## 2. Dual Schema Normalization Invariant (`relation` vs `dependency_type`)

Different canvas modules and APIs might historically serialize edge relations under differing key names:
- ReactFlow edge custom data: `{ relation: 'depends_on' }`
- Backend graph engine / TaskDAG: `{ dependency_type: 'depends_on' }`

**Best Practice**: In FastAPI Pydantic schemas, accept either or both using a `@model_validator(mode="before")`:
```python
class CreateEdgeRequest(BaseModel):
    source: str
    target: str
    relation: str = "depends_on"
    dependency_type: Optional[str] = None

    @model_validator(mode="before")
    def normalize_fields(cls, data: Any):
        if isinstance(data, dict):
            rel = data.get("relation") or data.get("dependency_type") or "depends_on"
            data["relation"] = rel
            data["dependency_type"] = rel
        return data
```

---

## 3. Autonomous AI Epic Decomposition Pattern

When breaking down an Epic or complex node into actionable subtasks:
1. **Specialized Tri-Tier Slices**:
   - **Specification / Architecture Slice** (`antigravity_mentor`): contracts, schemas, architecture specs.
   - **Implementation / Builder Slice** (`gerych_builder` or domain agent like `dnk_shopify`, `dnk_video_ai_creator`): code, UI, logic.
   - **Audit / Quality Gate Slice** (`gerych_auditor`): adversarial security review, unit tests, regression verification.
2. **Sequential Dependency Linking**:
   - `subtask_1 (Spec)` depends on `parent_epic`.
   - `subtask_2 (Build)` depends on `subtask_1`.
   - `subtask_3 (Audit)` depends on `subtask_2`.
3. **Spatial Offset Calculation**:
   - Position subtasks cleanly to the right (`x = parent.x + 350`) and spaced vertically (`y = parent.y - 120 + i * 150`) to avoid node overlap on the canvas.
4. **Heuristic Fallback**:
   - Always implement an offline deterministic decomposition fallback in case LLM inference is disabled or throttled.
