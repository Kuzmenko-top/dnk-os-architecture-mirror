# --- DNK-MRH-HEADER ---
# mrh_id: "docs/architecture/GASTOWNHALL_ECOSYSTEM_AUDIT_AND_ASSIMILATION.md"
# purpose: "Comprehensive Architectural Audit of gastownhall Ecosystem (Beads, Gas Town, Gas City) & Assimilation Roadmap for DNK OS"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-GASTOWN-AUDIT-001"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 🏙️ Deep Architectural Audit: `gastownhall` Ecosystem & Assimilation Blueprint for DNK OS

## 1. Executive Summary

The `gastownhall` organization (spearheaded by Steve Yegge and community) represents the state-of-the-art in **multi-agent orchestration infrastructure**, totaling over **45,000+ GitHub stars** across its primary pillars:
1. **`beads` (`bd`)** (26.8k ⭐): Dolt-backed distributed graph issue tracker & memory layer.
2. **`gastown`** (17.9k ⭐): Multi-agent workspace manager with git-backed worktree isolation.
3. **`gascity`** (1.2k ⭐): Composable SDK for multi-agent workflows, formulas/molecules, and gates.
4. **`wasteland` & `gascity-otel`**: Peer-to-peer workspace federation and OpenTelemetry observability.

This audit evaluates the entire repository portfolio and the official configuration specification (`beads.gascity.com/reference/configuration`) to extract actionable architectural patterns for DNK OS Task Forest, Swarm Engine, and Spatial Canvas HQ.

---

## 2. Organization Repository Inventory & Taxonomy

| Repository | Stars | Category | Core Role & Architectural Pattern | Relevance to DNK OS |
| :--- | :--- | :--- | :--- | :--- |
| **`beads`** | 26,840 | Storage & DAG | Dolt-backed graph issue tracker, atomic `--claim`, topological `bd ready`, memory `bd remember`. | **CRITICAL (Tier-1)**: Replaces flat markdown TODOs with transactional Dolt DAG. |
| **`gastown`** | 17,917 | Workspace Mgr | Mayor coordinator, Rigs (project repos), Polecats (ephemeral workers), Hooks (git worktrees). | **CRITICAL (Tier-1)**: Git worktree sandbox isolation for swarm agents. |
| **`gascity`** | 1,218 | Orchestration SDK | Declarative `city.toml`, Controller loop, Formulas & Molecules, Async Gates, Mailbox. | **CRITICAL (Tier-1)**: Template-to-graph compilation (TaskDNA $\leftrightarrow$ Molecules). |
| **`wasteland`** | 87 | Federation | P2P sync protocol across independent workspaces/towns with Dolt remotes. | **HIGH (Tier-2)**: Cross-workspace synchronization (`ws-alpha-001` to client distros). |
| **`gascity-packs`** | 84 | Agent Templates | Reusable agent packs, recipes, and specialized tool configurations. | **HIGH (Tier-2)**: Standardized skills/roles for our 14 swarm workers. |
| **`gascity-otel`** | 5 | Observability | VictoriaMetrics + VictoriaLogs + Grafana OTLP tracing for agent executions. | **MEDIUM (Tier-3)**: Telemetry and token spending visualization in Studio. |
| **`tmux-adapter`** | 2 | Runtime | Headless terminal multiplexer session manager for background CLI agents. | **HIGH (Tier-2)**: Background execution harness for CLI agents. |
| **`overwatch`** | 1 | Supervision | Watchdog process detecting agent stalls, infinite loops, and token burn. | **HIGH (Tier-2)**: Stall detection for `dnk_swarm_engine`. |
| **`dolt` / `go-mysql-server`** | Forks | Data Engine | Relational SQL database with Git semantics (commits, branches, diffs, merges). | **CORE DEP**: Underlying storage layer for Beads. |

---

## 3. Deep Dive: Beads Configuration Architecture (`beads.gascity.com`)

The Beads configuration specification separates **Tool-level preferences** from **Project-level database state**:

### 3.1 Two-Tier Configuration Split
1. **Tool-Level (`config.yaml`)**:
   - Managed via Viper; stores user CLI ergonomics, auto-commit flags, validation policies, and federation rules.
   - Hierarchical precedence: CLI flags $\to$ Env Vars (`BD_*`) $\to$ `.beads/config.yaml` $\to$ `~/.config/bd/config.yaml`.
2. **Project-Level (Dolt Database)**:
   - Stored directly inside the Dolt database (`.beads/embeddeddolt/` or `.beads/dolt/`).
   - Synced across machines via `bd dolt push` without exposing plaintext secrets.
   - Holds tracker integrations (Jira, Linear, GitHub, status maps).

### 3.2 Mission-Critical Configuration Invariants
- **Validation Gates (`validation.on-create`, `validation.on-close`, `validation.on-sync`)**:
  Allows enforcing strict template and quality checks before an issue can be closed or synced.
- **Sovereignty Tiers (`federation.sovereignty`)**:
  - `T1` (Strict Local: data never leaves infrastructure)
  - `T2` (Regional jurisdiction)
  - `T3` (Trusted Cloud)
  - `T4` (Unrestricted)
  *Matches DNK OS Patent Shield & Privacy-First Policy (`T1`).*
- **Directory-Aware Monorepo Scoping (`directory.labels`)**:
  Automatically scopes labels based on path prefix (e.g. `apps/web/` $\to$ `web`, `core/` $\to$ `core`).
- **Memory Caps (`prime.max-memories`, `prime.max-memory-chars`)**:
  Enforces bounded context injection when `bd prime` injects historical insights, preventing agent context overflow.

---

## 4. Key Architectural Patterns to Assimilate into DNK OS

### 🧬 Pattern 1: Formulas & Molecules $\longleftrightarrow$ TaskDNA Compilation
* **Gas City Concept**: A **Formula** is a static template (TOML/JSON) describing a workflow; a **Molecule** is an instantiated, dependency-linked graph of Beads executed by agents.
* **DNK OS Assimilation**:
  - Our `dnk_decompose_task_dna` currently generates in-memory DAGs.
  - We can assimilate the Formula pattern: define pre-compiled workflow templates (`Shopify_PDP_Migration.formula.toml`, `Video_Storyboard_Pipeline.formula.toml`).
  - When instantiated, it generates a **Task Forest Molecule**:
    $$\text{Formula (DNA)} \xrightarrow{\text{compile}} \text{Molecule (Tree)} \xrightarrow{\text{spawn}} \text{Bushes \& Flowers (Beads)}$$

### 🪝 Pattern 2: Git Worktree Isolation ("Hooks" Pattern from Gas Town)
* **Gas Town Concept**: In Gas Town, "Polecats" (ephemeral worker agents) do not work directly in the main branch or dirty working directory. Each agent operates inside an isolated Git Worktree (`Hooks`), surviving crashes and preventing simultaneous file edit collisions.
* **DNK OS Assimilation**:
  - Our root already contains `.worktrees/`.
  - When `dnk_swarm_parallel` dispatches tasks to `gerych_builder` and `dnk_dev_fullstack`, each worker spawns in its own worktree:
    - Worker 1: `.worktrees/agent-builder-bd-101/`
    - Worker 2: `.worktrees/agent-fullstack-bd-102/`
  - When the subtask passes `scripts/verify_all.sh`, the branch is merged back to the feature branch cleanly via OCC (`dnk_workspace_occ_merge`).

### 🚦 Pattern 3: Async Coordination Gates
* **Gas City Concept**: Gates pause graph execution until external conditions are met:
  - `HumanGate`: Requires human sign-off.
  - `GitHubGate`: Waits for PR review/approval or CI completion.
  - `TimerGate`: Bounded wait periods.
* **DNK OS Assimilation**:
  - Map DNK OS **Master Quality Gate** and **Adversarial Gate** as native Beads/GasCity Gates.
  - A `Flower` (subtask) cannot transition from `in_progress` to `completed` in the Task Forest unless the `Gate_Adversarial_ASR_Zero` and `Gate_Tests_100_Green` pass.

### 📬 Pattern 4: Asynchronous Agent Mailbox (`bd mail`)
* **Gas Town Concept**: Agents communicate across boundaries via structured mailboxes instead of bloating shared prompt contexts.
* **DNK OS Assimilation**:
  - Enables `gerych_builder` (UI) to message `dnk_shopify` (Ecom): *"Liquid AST component ready at ./snippets/product-card.liquid; please run auto-audit."*
  - Keeps conversation context compact and prevents multi-agent chat contamination.

---

## 5. Synthesis Architecture: The Unified DNK OS "Gas Forest" Stack

```
=============================================================================
                           DNK OS SPATIAL CANVAS HQ
    [React Flow 5-Plant Scale]   [Whiteboard Overlay]   [Stitch Prompt Dock]
=============================================================================
                                     |
                                     v
=============================================================================
                   TASK FOREST & DUAL-SYNC CONTROLLER
    - Bottom-Up Progress Rollup (Mathematical Cascade)
    - SCONES Cognitive Memory Federation (L1/L2/L3)
    - Level-of-Detail (LOD) Spatial Virtualizer
=============================================================================
                                     |
             +-----------------------+-----------------------+
             v                                               v
+-----------------------------+               +-----------------------------+
|    BEADS ENGINE (bd/Dolt)   |               |   GAS TOWN WORKSPACE MGR    |
| - Transactional SQL/Dolt DB |               | - The Mayor (Gerych Prime)  |
| - Atomic Claims (`--claim`) |               | - Isolated Git Worktrees    |
| - Topological `bd ready`    |               | - Swarm Health Patrol       |
| - Validation Gates          |               | - Convoys & Mailboxes       |
+-----------------------------+               +-----------------------------+
             ^                                               ^
             +-----------------------+-----------------------+
                                     |
=============================================================================
                     14 SPECIALIZED SWARM AGENTS
   [gerych_builder]    [dnk_shopify]    [dnk_dev_fullstack]    [gerych_auditor]
=============================================================================
```

---

## 6. Implementation Action Plan

1. **Step 1: Install & Evaluate `bd` CLI**:
   - Verify `bd` tool availability and compatibility with our macOS environment.
   - Configure `.beads/config.yaml` with `json: true`, `validation.on-create: warn`, and local T1 sovereignty.
2. **Step 2: Core Adapter `core/adapters/beads_adapter.py`**:
   - Expose Python methods: `beads_create()`, `beads_ready()`, `beads_claim()`, `beads_close()`.
   - Map 5-Plant Scale entity hierarchy to Beads parent-child dependency IDs.
3. **Step 3: Swarm Parallel Integration**:
   - Integrate `beads_claim` into `dnk_swarm_engine.py` to ensure conflict-free parallel agent execution.
4. **Step 4: Spatial Canvas Stitch Dock Integration**:
   - Connect the Stitch Prompt Dock directly to the Beads engine for instant node generation and live progress reflection.
