---
name: beads-task-forest-integration
description: "Use for task forest graphs. Manages agent task dependency."
mrh_id: "skills/autonomous-ai-agents/beads-task-forest-integration/SKILL.md"
purpose: "Implement, manage, and query hierarchical task forest graphs (Beads) in multi-agent environments."
canonical_source: true
status: "Active"
version: "1.0.0"
updated_at: "2026-09-03"
author: "Gerych Core"
---

# Beads & Task Forest Integration

## Trigger Conditions
Use when designing, implementing, or querying task dependency graphs, hierarchical task forests, or beads databases for task management and concurrent multi-agent coordination.

## 🎯 Architectural Principles

### 1. Zero-Binary Local Fallback (SSOT)
Always design beads adapters with a dual-engine architecture:
- **Primary Engine**: Use native `bd` or `dolt` CLI tools if they are available in the system `$PATH`.
- **Secondary Engine (Fallback)**: Seamlessly fall back to a local, zero-dependency SQLite backend (`.beads/beads.db`) if no external binary is found. This guarantees immediate out-of-the-box operability across development, staging, and containerized environments without breaking execution pipelines.

### 2. Hierarchical Task Forest Taxonomy
Tasks (Beads) follow a deterministic tree/forest naming convention to represent nested subtasks:
- **Level 1 (Milestone/Goal)**: `bd-xyz`
- **Level 2 (Feature/Component)**: `bd-xyz.1`
- **Level 3 (Task/Issue)**: `bd-xyz.1.1`
- **Level 4 (Subtask/PR)**: `bd-xyz.1.1.1`

### 3. Topological Dependency Resolution
To support concurrent multi-agent executions, always implement topological sorting:
- Only return tasks whose prerequisites (parent or prior sibling beads) are in a completed status (`closed` / `success`).
- This guarantees agents do not pick up dependent tasks prematurely.

### 4. Atomic Claming & Race-Condition Prevention
In multi-agent swarms, multiple workers might request tasks simultaneously:
- Use transaction-safe SQL or atomic lock flags to "claim" a task for a specific agent role before starting execution.
- Prevent double-allocation by enforcing unique constraints on the claim status.

---

## 🛠️ Step-by-Step Implementation Pattern

### 1. Dual-Engine SQLite Fallback Adapter Pattern
Implement adapters with automatic fallback handling as shown below:

```python
import os
import sqlite3
import subprocess
from typing import List, Optional, Dict, Any

class BeadsAdapter:
    def __init__(self, db_path: str = "./.beads/beads.db"):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.use_native_cli = self._detect_cli()
        if not self.use_native_cli:
            self._init_sqlite_db()

    def _detect_cli(self) -> bool:
        try:
            subprocess.run(["bd", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _init_sqlite_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS beads (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open',
                    priority INTEGER DEFAULT 1,
                    claimed_by TEXT,
                    parent_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bead_dependencies (
                    bead_id TEXT,
                    depends_on TEXT,
                    PRIMARY KEY (bead_id, depends_on),
                    FOREIGN KEY (bead_id) REFERENCES beads (id) ON DELETE CASCADE,
                    FOREIGN KEY (depends_on) REFERENCES beads (id) ON DELETE CASCADE
                )
            """)
            conn.commit()
```

### 2. Resolving Executable Tasks (Topological Sort)
Filter for tasks that are ready for execution:
```sql
-- Find open beads that do not depend on any open/failed beads
SELECT b.* FROM beads b
WHERE b.status = 'open'
  AND b.claimed_by IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM bead_dependencies d
      JOIN beads dep ON d.depends_on = dep.id
      WHERE d.bead_id = b.id AND dep.status != 'closed'
  );
```

---

## ⚠️ Pitfalls & Verification Steps

### 1. Absolute Path Violations & Path Traversal Risks
- **Pitfall**: Hardcoding `/Users/...` or home-relative `~/` paths in database files or configuration schemas breaks portable deployments. Accepting arbitrary client `target_dir` paths in sync handlers risks path traversal (`../`) attacks.
- **Fix**: Use `os.path.abspath()` dynamically with relative paths. For Obsidian Vault operations, always pass paths through `validate_vault_path()` to ensure targets strictly reside within `get_canonical_vault_root()`.

### 2. Non-Deterministic LWW Conflict Resolution
- **Pitfall**: Relying purely on floating-point timestamps (`updated_at`) for Last-Write-Wins leads to undefined behavior or silent data loss when updates occur within the same sub-second window.
- **Fix**: Employ a composite tie-breaker tuple: `(updated_at, revision, content_hash)`. If timestamps collide, higher `revision` wins; if revisions match, lexicographical SHA-256 `content_hash` breaks ties deterministically.

### 3. SQLite Write Locks under High Concurrency
- **Pitfall**: Multi-threaded or parallel subprocess execution on SQLite can trigger `database is locked` (`OperationalError`).
- **Fix**: Configure SQLite connection timeout limits (`sqlite3.connect(db, timeout=10.0)`) and use WAL mode (`PRAGMA journal_mode=WAL;`).

### 4. Graph Serialization Dict vs Array Shape
- **Pitfall**: Graph endpoints like `/api/v3/task_forest/graph` often serialize nodes as a dictionary mapping `{node_id: node_dict}` rather than a flat array. Assuming an array causes frontend crashes (`.map is not a function`) or test errors (`TypeError: string indices must be integers, not 'str'`).
- **Fix**: Always normalize defensively:
  `const rawNodes = Array.isArray(data.nodes) ? data.nodes : Object.values(data.nodes || {});`
  In Python tests: `nodes_list = list(data["nodes"].values()) if isinstance(data["nodes"], dict) else data["nodes"]`.

### 5. Cascading Bottom-Up Mutation Logging in Evolution History
- **Pitfall**: When a leaf node (Flower) mutates, bottom-up recalculation propagates updates through ancestors (Bush ➔ Tree ➔ Sector ➔ Field), generating multiple events in `evolution_history`. The top-level rollup (`field-...`) is logged last, causing naive `events[-1]["node_id"] == leaf_id` assertions to fail.
- **Fix**: Search the history stream for the specific target: `[e for e in history["events"] if e["node_id"] == target_id]`.

### 6. Verification Protocol
Always verify graph operations with test coverage simulating:
- Cyclic dependency detection.
- Complete task flow traversal (Red ➔ Green).
- Concurrent task claim safety.

### 7. Dataclass Subclassing & Keyword Argument Bleed (`TypeError: unexpected keyword argument`)
- **Pitfall**: In Python `@dataclass` hierarchies (`TaskNode` base with `IdeaNode`, `GoalNode`, `BugNode`, `DocumentationNode`), passing specialized arguments (`hypothesis`, `severity`, etc.) to subclasses that invoke `super().__init__(**kwargs)` raises `TypeError: TaskNode.__init__() got unexpected keyword argument`.
- **Fix**: Explicitly `.pop()` specialized attributes in subclass `__init__` (or forward unhandled keys into `self.metadata`), then pass only base fields to `super().__init__(**kwargs)`.

### 8. Obsidian Frontmatter & Enum Serialization
- **Pitfall**: Direct serialization of task node properties (`NodeType`, `ExecutionStage`, `Priority`) into Obsidian YAML frontmatter fails or produces raw Python enum representations (e.g., `<NodeType.TASK: 'task'>`), breaking Obsidian frontmatter parsers.
- **Fix**: Coerce all Enums to their scalar `.value` strings and convert date/datetime objects to ISO-8601 strings prior to YAML dumping.
- **Strict Frontmatter Placement on Line 1**: Obsidian's markdown parser strictly requires YAML frontmatter to start at line 1 (`---`). Any preceding text, blank lines, or comments causes Obsidian to treat frontmatter as regular body text and drop properties.
- **DNK-MRH Header Coexistence in Obsidian**: If the note requires a DNK-MRH header per repo standards, never place raw `# --- DNK-MRH-HEADER ---` before `---`. Instead, format the MRH header as an HTML comment block (`<!-- --- DNK-MRH-HEADER ---\n...\n--- -->`) immediately after the frontmatter, or embed `mrh_id` as a frontmatter property. This satisfies both precommit regex checks and Obsidian property parsing.
- **Graph & Dependency [[wikilinks]]**: Always render dependencies and parent nodes as `[[Node Title]]` in the note body. This populates Obsidian's native graph view edges and enables `ObsidianTaskForestSync` to map notes back into `ForestEdge` relationships.

### 9. Stage Transition Enforcement on Swarm Agent Dispatch (`Invalid stage transition`)
- **Pitfall**: When dispatching an agent to a task (`dispatch_agent`), state machines like `StageManager` enforce strict transition validity (`BACKLOG -> PLANNED -> IN_PROGRESS`). Jumping directly from `BACKLOG` to `IN_PROGRESS` triggers `ValueError: Invalid stage transition: ExecutionStage.BACKLOG -> ExecutionStage.IN_PROGRESS` or fails transition validation silently.
- **Fix**: Automatically step through required intermediate stages prior to dispatch:
  ```python
  if node.stage == ExecutionStage.BACKLOG:
      self.transition_stage(node_id, ExecutionStage.PLANNED)
  if node.stage == ExecutionStage.PLANNED:
      self.transition_stage(node_id, ExecutionStage.IN_PROGRESS)
  ```

### 10. TaskDNA DAG Import & Topological Layering
- **Pitfall**: Naive rendering of imported `TaskDNA` task decomposition trees onto spatial canvas nodes places all nodes at default coordinates `(0, 0)` or creates overlapping visual clutter.
- **Fix**: Calculate dependency depth level for each node (`depth = max(depth(dep) + 1 for dep in dependencies) if dependencies else 0`). Offset coordinates topologically: `x = base_x + (depth * 320)`, with vertical slot index spacing `y = base_y + (slot_in_depth * 140)`. Map risk levels (`critical`, `high`, `medium`, `low`) directly to task priority enums.

### 11. Production Datastore Pollution by Test Suites & Chat Intake Bloat
- **Pitfall**: Running test suites (`test_node_tasks_router.py`, decomposition integration tests) directly against live storage (`./data/node_task_graph.json`) repeatedly generates ghost nodes (duplicate tasks, test conversions, decomposition subtasks), accumulating hundreds of redundant nodes. Unconstrained conversational chat endpoints also inadvertently convert conversational inquiries into task nodes.
- **Fix**:
  1. *Test Fixture Isolation*: Always isolate integration tests to a temporary database (`tmp_path / "test_graph.json"` or explicit mock persistence instances) and restore baseline or cleanup after test execution.
  2. *Conversational Chat vs Task Intent Filter & Punctuation Tolerance*: Ensure conversational chat endpoints classify user intent (conversational Q&A vs task generation) before automatically minting DAG nodes.
     - *Normalization*: Strip arbitrary punctuation and delimiters following agent address prefixes (e.g. `r"^(?:герич|herych)[\s,:—–.!?*-]+"`), so prefixes like `Герич . ` don't leak into intent regexes.
     - *Intent Detection*: Do not rely solely on ending question marks (`?`). Match status/inquiry queries (e.g., `що за ноди`, `які є`, `покажи`, `список`, `стан`) and return structured graph metadata directly in the conversational chat response without creating new nodes. Require explicit action verbs (`створи`, `ідея:`, `задача:`) for task generation.
  3. *Baseline Recovery*: Provide deterministic reset endpoints (`POST /api/v3/node_tasks/reset_baseline` or `NodeTaskPersistenceManager.get_instance().reset_to_baseline()`) that restore canonical roadmap nodes when pollution occurs.
  4. *Docker Backend Process Caching during Live Verification*: If the API server runs inside a Docker container (`dnk_backend`) without uvicorn `--reload`, changes to bind-mounted Python files are not loaded into memory automatically. Always execute `docker restart dnk_backend` before verifying live chat intake from the browser or UI.

### 12. Living LLM Agent Bridge Integration & Dual-Channel Response (Conversational vs TaskDAG)
- **Pitfall**: Replacing heuristic regex parsers with live LLM calls (`GerychAgentBridge`) risks flaky tests, database pollution, sycophantic conversation loops, and context amnesia:
  1. Brittle test assertions expecting exact words (e.g. `assert "вузлів" in reply`) fail when LLMs use natural synonyms like `"нод"` or `"задач"`.
  2. If the LLM omits the agent's name in its greeting, assertions like `assert "Герич" in reply` fail.
  3. LLM API downtime or missing tokens can crash the intake endpoint if no graceful fallback is configured.
  4. Token Expiration (HTTP 401) & Containerized Watchdogs: Google Vertex bearer tokens expire in 60 minutes. In Docker setups where gcloud lives on the host, an unrefreshed token triggers 401s, silently falling back to heuristics.
  5. Fallback Imperative Bleed: Casual user queries like "напиши дату" can match heuristic imperative verbs (`^напиши\b`), minting bogus nodes into the DAG.
  6. Lack of Temporal Grounding: Without explicit local timezone timestamps injected into system prompts, live LLMs hallucinate inaccurate dates and times.
  7. Stateless Conversation Amnesia: When frontend clients only send the latest prompt string without previous chat history (`history`), the agent cannot interpret follow-up approvals or context-dependent instructions like "Ну давай, реалізовувай" or "Так, давай реалізуйте так, як ви бачите". Without context, the model fails to recognize the user's intent and either asks pointless clarifying questions or falls back into generic loops.
  8. Sycophancy Trap & Verbose "Water" in Agent Chat Intake: If system prompts rely on overly deferential phrasing ("твій творець", "завжди тепло з повагою"), LLMs default to verbose, obsequious pleasantries ("мій дорогий друже і творець! Дякую за довіру...") instead of concise technical execution, driving founder frustration.
  9. Passive Re-questioning on Mandates ("Action-First" Protocol Violation): When the founder grants an open mandate ("реалізовувай", "роби так, як бачиш", "зроби зручніше"), a passive assistant asks for direction instead of taking initiative.
- **Fix**:
  1. *Dual-Channel Response*: Enforce JSON structure separating human conversational `reply` from TaskDAG `nodes`/`edges`. Set `nodes: []` on conversational inquiries.
  2. *Graceful Offline Fallback*: Wrap LLM calls in a fail-safe block that falls back to the deterministic regex parser without raising HTTP 500.
  3. *Consistent Signature Normalization*: Prepend/append agent identification (`🤖 Герич:`) if not already present in the LLM output.
  4. *Flexible Vocabulary Assertions*: In integration tests, assert against synonym lists: `assert any(w in reply for w in ["вузлів", "нод", "задач", "граф"])`.
  5. *Continuous Token Synchronization*: Run a background daemon on the host (`gcp_token_daemon.py`) refreshing `.vertex_token` mounted directly into the container.
  6. *Whitelist Temporal Inquiries*: Preemptively classify queries containing "час", "година", "дата", "день" as inquiries before checking task creation regexes.
  7. *Live Local Timezone Injection*: Dynamically inject formatted Kyiv time/date (`Europe/Kyiv`, UTC+3) into LLM system prompts on every intake call.
  8. *Multi-Turn History & Selection Injection*: Ensure the frontend store collects and sends the recent conversation turns (e.g. last 6–10 user/assistant turns) along with the active spatial context (`selected_node_id`). The backend bridge injects the dialogue transcript (`### ІСТОРІЯ ПОТОЧНОГО ДІАЛОГУ`) and selected node details into the LLM prompt.
  9. *Anti-Sycophancy Guard & Chief Architect Persona Invariants*: Explicitly forbid sycophantic greetings, praise, and deferential fluff in the system prompt. Require a sharp, confident, and professional tone (2–4 concise sentences) focused on technical status, blockers, and concrete action steps.
  10. *Autonomous Action-First Synthesis on User Approval*: If the user approves an initiative or says "реалізовуй", the agent MUST NOT ask clarifying questions. It must synthesize 2–4 concrete engineering tasks (e.g. UX enhancements, node actions, API extensions), create them directly in the Task Forest graph, assign them to specialized swarm workers (`gerych_builder`, `dnk_dev_fullstack`), and report concisely.
  11. *4-Intent Classification vs Task Creation Spam*: User inquiries about UI bugs or layout issues (e.g. "Чому ноди налазять одна на одну?") must be classified as `inquiry` or `auto_layout` with zero new nodes generated. Execution commands ("запускай її виконання") must be classified as `execute_task` with zero new nodes generated to prevent duplicate task spam.
  12. *Real Autonomous Worker Triggering vs Simulated Chat Invariant*: When user commands execution ("запускай", "виконуй"), the system must NEVER simulate progress with text-only assurances while leaving progress at 0% and logs empty. The chat intake must return `action: "execute"`, resolve `target_node_id`, and immediately dispatch real background agent workers (`execute_agent_for_node` / frontend `executeAgent()`) with live WebSocket log streaming.
  13. *Deterministic Topological Auto-Layout vs Diagonal Overlap Stacking*: Avoid naive incremental coordinate offsets (e.g. `+260px, +40px`) which cause 360x240px node cards to stack diagonally like stairs. Compute dependency ranks via `NodeTaskGraphEngine.compute_auto_layout()` with discrete column levels (X: +440px) and row spacing (Y: +280px), automatically triggering auto-layout on node creation and chat intake.

---

## 🔗 Related References & Extensions
- [Obsidian Canvas & Task Forest Bidirectional Sync Protocol](references/obsidian-canvas-sync.md): Details JSON Canvas mapping, YAML frontmatter note decomposition, in-repo ADR canonicalization (SSOT), and bidirectional vault sync.
- [Visual Canvas Control Panel & TaskDNA Sync Protocol](references/visual_canvas_control_panel_and_taskdna_sync.md): Real-time Visual Control Panel in Obsidian Canvas with topological columnar layout, color palette mapping (1-6), live Master HUD telemetry node, and CLI runner (`scripts/system/visual_canvas_control_runner.py`).
- [Task Forest Spatial LOD & Time-Travel Architecture](references/task-forest-spatial-lod-timetravel.md): 5-tier taxonomy (Field/Sector/Tree/Bush/Flower), Canvas LOD zoom mapping (0.2x/1.0x/2.5x), and Time-Travel mutation scrubber.
- [Task Forest Swarm Autonomy & TaskDNA DAG Integration](references/task-forest-swarm-autonomy-taskdna.md): Schema extensions for agent dispatch, multi-stage state transitions, topological layout algorithms, and the 4-tier Agentic OS Natural Language ➔ TaskForest ➔ Swarm execution pattern.
- [Living LLM Agent Bridge & TaskForest Nervous System Protocol](references/living_llm_agent_bridge_and_taskforest_nervous_system.md): Dual-channel response contract (`reply` + `nodes`), intent disambiguation, Vertex AI / Gemini integration with `SOUL.md`, and resilient offline fallback patterns.