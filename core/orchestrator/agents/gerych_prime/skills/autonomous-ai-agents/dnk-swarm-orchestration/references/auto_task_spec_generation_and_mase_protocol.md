# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/auto_task_spec_generation_and_mase_protocol.md"
# purpose: "Operational reference for Natural Language Interception, Task Spec Generation v2.5, Evidence Planning, Risk Gates and GitHub SOTA Research under MASE."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🎯 Auto-Task-Spec Generation & Natural Language Interception Protocol

## 1. Problem & Context
When users provide unstructured or natural language requests (e.g., "Герич, зроби аудит архітектури та знайди кращі open-source рішення..."), autonomous execution without prior formalization leads to:
- Scope drift (modifying arbitrary or unexpected files)
- Budget exhaustion (hitting the 90/90 tool call hard limit)
- Ambiguous Definition of Done (DoD)
- Violation of Mandatory Atomic Slice Execution (MASE ≤ 25 tool calls per turn)
- Unverified empirical assumptions without ground-truth evidence
- Uncontrolled high-risk execution (destructive file deletions, unbacked secret overwrites)

## 2. Architecture & Execution Flow
```
User Natural Query ("Герич, зроби аудит... https://github.com/...")
            │
            ▼
`should_auto_spec(query)` (Regex heuristics: action verbs UA/EN, filters out pure chat & questions)
            │
            ├─► If False: proceed with normal conversation / tool execution
            ▼
`assess_risk(query)` ─────────────► Risk Gate (`core/orchestrator/risk_gate.py`)
            │                        ├─► HIGH / CRITICAL (score ≥ 70): Approval required, backup & rollback mandatory
            │                        ├─► MEDIUM (score 40-69): Backup & rollback recommended
            │                        └─► LOW (score < 40): Autonomous MASE execution
            ▼
`analyze_github_repo(url)` ───────► GitHub Research Module (`core/orchestrator/github_research.py`)
            │                        ├─► TRACK_1_DIRECT: MIT, Apache-2.0, BSD, ISC (direct template/code reuse)
            │                        └─► TRACK_2_CLEAN_ROOM: AGPL, GPL, SSPL, BSL (clean-room synthesis only)
            ▼
`dnk_triage_task(query)` ────────► Complexity formula: C = F + 2D + 3S
            │                        └─► Routing: SOLO vs SWARM_PARALLEL vs SWARM_SEQUENTIAL
            ▼
`generate_evidence_plan(spec)` ──► Evidence Planner (`core/orchestrator/evidence_planner.py`)
            │                        ├─► Epistemic matrix: OBSERVED vs INFERRED vs HYPOTHESIS
            │                        └─► Verification commands: du -sh, find, git log, pytest
            ▼
`get_next_slice_number()` ───────► Auto-increments micro-slice from recent git commits (e.g. 13.1 -> 13.2)
            ▼
`auto_generate_task_spec(...)` ──► Full GERYCH_TASK_TEMPLATE v2.5 Markdown with Risk, Evidence & SOTA blocks
            │
            ├─► `save_task_spec(...)` Multi-Tier Persistence Gateway:
            │     ├─► `.hermes/active_task_spec.md` (Active runtime context for Hermes Agent)
            │     ├─► `docs/plans/TASK_ACTIVE.md` (SSOT pointer in repo root plans)
            │     ├─► `docs/plans/my_task/task_YYYYMMDD_<slug>.md` (Versioned canonical plan)
            │     └─► `docs/notes/tasks_and_ideas/<slug>.md` (Obsidian Task Forest mirror)
            └─► Injected into `hermes_pre_tool_hook.py` session tracker
```

## 2.1 Multi-Tier Persistence & Obsidian MRH Hygiene Invariant
When `save_task_spec(...)` persists generated specifications to the Obsidian Vault (`docs/notes/tasks_and_ideas/`), it strictly enforces `[OBSIDIAN_MRH_HYGIENE]`:
- **Line 1 Frontmatter**: Line 1 MUST be standard YAML frontmatter opening (`---`) with Obsidian metadata (`tags`, `status`, `created_at`, `type: task_spec`).
- **Muted HTML Comment Block**: The Machine-Readable Header (`DNK-STD-0075`) MUST be enclosed in an HTML comment (`<!-- --- DNK-MRH-HEADER --- ... --- END DNK-MRH-HEADER -->`). Never start the markdown with `# --- DNK-MRH-HEADER ---` as it renders as an oversized H1 header in Obsidian.
- **Bi-directional Wikilinks**: Rich `[[wikilinks]]` linking the task to `[[Task Forest]]`, `[[MASE Protocol]]`, and related architectural concepts.

## 3. Core Subsystems

### A. Evidence Planner & Epistemic Taxonomy (`core/orchestrator/evidence_planner.py`)
- **Epistemic Classification**:
  - `OBSERVED`: Empirical facts verified by commands, file sizes, or test outputs (e.g., file exists, tests pass).
  - `INFERRED`: Derived conclusions from multiple observations and static analysis.
  - `HYPOTHESIS`: Unverified assumptions requiring explicit probing before micro-slice mutation.
- **Probe Commands**: Deterministic shell probes (`du -sh`, `find`, `git log`, `stat`) with expected thresholds.
- **Automated Verification**: `execute_evidence_plan()` runs probes safely and records pass/fail metrics.

### B. Risk Gate & Snapshot Engine (`core/orchestrator/risk_gate.py`)
- **Risk Indicators**: Scans query and diff for destructive commands (`rm -rf`, `drop database`, `delete`, `reset --hard`) and security-critical files (`.env`, `vault`, `SOUL.md`).
- **Safety Invariants**:
  - `requires_approval = True` when risk is HIGH or CRITICAL.
  - `backup_required = True`: Automatic file snapshots stored in `.hermes/backups/`.
  - `rollback_required = True`: Automated rollback script or git checkout recovery instructions.

### C. GitHub SOTA Research & License Auditor (`core/orchestrator/github_research.py`)
- **URL Extraction**: Automatically parses GitHub URLs from query prompts.
- **Two-Track Legal Routing**:
  - `TRACK_1_DIRECT` for permissive licenses.
  - `TRACK_2_CLEAN_ROOM` for copyleft/proprietary licenses.
- **Architectural Extraction**: Detects state graphs, DAGs, event buses, canvas sync, and RLM patterns.

## 4. Mandatory Invariants for Generated Task Specs
- **Budget & MASE Circuit Breaker**: Standard 25 tool calls per atomic slice (`reads ≤ 8`, `writes ≤ 8`, `verifications ≤ 4`). The `hermes_pre_tool_hook.py` Section 7 emits an explicit warning to stderr at turn 25 and physically blocks read/search calls at turn ≥ 28 with exit code 2, forcing immediate verification and slice commitment.
- **Git Hygiene Guard Invariant**: All untracked test/router files must be detected recursively via `git status --porcelain -u` before slice closure.
- **Target Files**: Explicit relative paths extracted from triage domains (`core/`, `scripts/`, `tests/`, etc.).
- **Definition of Done (DoD)**:
  1. All target files modified/created with MRH headers.
  2. 100% test pass rate (`bash scripts/verify_all.sh` or targeted pytest).
  3. Clean git tree (`git diff --check` and clean `git status`).
- **Verification Command**: Explicit commands (e.g. `./.venv/bin/pytest tests/...`).

## 5. CLI Usage & Verification
```bash
# Check if query needs spec generation
./scripts/system/auto_task_spec.py "Герич, створи модуль..." --check

# Generate JSON payload with Risk Gate & Evidence Plan
./scripts/system/auto_task_spec.py "Герич, зроби аудит..." --json

# Override slice number and output destination
./scripts/system/auto_task_spec.py "Герич, зроби..." --slice 13.2 --output .hermes/custom_spec.md
```
