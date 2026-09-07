# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/beads-task-forest-integration/references/task-forest-swarm-autonomy-taskdna.md"
# purpose: "Reference architecture and implementation recipe for Swarm Agent dispatch and TaskDNA DAG import in Task Forest."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-06"
# author: "Gerych Core"
# --- END DNK-MRH-HEADER ---

# Task Forest Swarm Autonomy & TaskDNA DAG Integration

## 1. Swarm Agent Task Forest Schema Extension
To allow autonomous agents to operate directly on Task Forest nodes, `TaskNode` is extended with first-class fields:
```python
@dataclass
class TaskNode:
    # Core attributes
    id: str
    title: str
    node_type: NodeType
    stage: ExecutionStage = ExecutionStage.BACKLOG
    priority: Priority = Priority.MEDIUM
    ...
    # Swarm Agent attributes
    assigned_agent: Optional[str] = None       # e.g., 'gerych_builder', 'dnk_dev_fullstack'
    agent_status: Optional[str] = None         # 'idle', 'running', 'completed', 'failed'
    agent_run_id: Optional[str] = None         # execution run/telemetry id
```

## 2. Multi-Stage Transition Rule for Agent Dispatch
When triggering agent execution, state machines enforce valid transition sequences (`BACKLOG -> PLANNED -> IN_PROGRESS`). Direct jumps from `BACKLOG` to `IN_PROGRESS` are disallowed by default.
```python
def dispatch_agent(self, node_id: str, mode: str = "direct") -> Dict[str, Any]:
    node = self.nodes.get(node_id)
    if not node:
        raise ValueError(f"Node {node_id} not found")
    if not node.assigned_agent:
        raise ValueError(f"Node {node_id} has no agent assigned")

    # Step sequentially through stages to preserve state machine validation invariants
    if node.stage == ExecutionStage.BACKLOG:
        self.transition_stage(node_id, ExecutionStage.PLANNED)
    if node.stage == ExecutionStage.PLANNED:
        self.transition_stage(node_id, ExecutionStage.IN_PROGRESS)

    node.agent_status = "running"
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    node.agent_run_id = run_id
    return {"node_id": node_id, "agent": node.assigned_agent, "stage": node.stage.value, "run_id": run_id}
```

## 3. TaskDNA DAG Import Algorithm
`TaskDNA` yields structured plans with dependencies (`depends_on`). To render this cleanly without node collisions on a spatial canvas:
1. Build a dependency tree to determine each step's topological depth.
2. Group nodes by depth level (`depth = max([depth(p) + 1 for p in parents], default=0)`).
3. Compute spatial coordinates:
   - `x = base_x + (depth * 320)`
   - `y = base_y + (slot_within_depth * 140)`
4. Map `risk_level` to `Priority`:
   - `critical` -> `Priority.CRITICAL`
   - `high` -> `Priority.HIGH`
   - `medium` -> `Priority.MEDIUM`
   - `low` -> `Priority.LOW`

## 4. Agentic OS Interaction Pattern: Natural Language to Swarm Execution
In the DNK OS Agentic Operating System, TaskForest serves as the shared cognitive DAG ("nervous system") connecting human intent to swarm execution across 4 distinct layers:

### A. Perception Layer (Human Natural Language & Inception)
- **Natural Language SSOT**: The human user interacts via natural voice or chat (`/chat_intake`, Web UI, Telegram), never by manually populating DAG forms or setting coordinates.
- **Prime Agent Cognitive Prefrontal Cortex**: The Prime Agent intercepts user input, disambiguates requests via light Socratic inception, and separates conversational inquiries (Q&A, status inspections) from DAG task generation. Inquiries must NEVER pollute the datastore with ghost nodes.

### B. Translation Layer (Language ➔ TaskForest DAG)
- **Automatic Decomposition**: Formulates structured trees: `Epic` ➔ `Task` ➔ `Quality Gate` with topological dependency edges (`depends_on`).
- **Role Assignment**: Automatically assigns specialized swarm workers based on domain (`dnk_shopify`, `dnk_dev_fullstack`, `gerych_builder`, `gerych_auditor`).
- **Knowledge Mirror**: Synchronizes branches with the Obsidian Vault (`./docs/notes/`) for human transparency and durable recall.

### C. Execution Layer (Autonomous Swarm Workers)
- **Topological Event Dispatch**: When parent nodes complete, child nodes transition to `ready`. Swarm workers claim tasks atomically and execute isolated slices.
- **Telemetry & Artifact Recording**: Execution telemetry, test outputs, and generated files are recorded directly onto the TaskNode payload.
- **Self-Healing Loop**: Failures trigger `SessionSentinel` / `dnk_distiller` to search error distillation tables and auto-generate recovery sub-nodes.

### D. Synthesis Layer (Human-Facing Conversational Reporting)
- **Conversational Milestone Handoff**: Instead of exposing raw telemetry dumps or exit codes, the Prime Agent synthesizes execution milestones into clear, natural language summaries with actionable next steps.
