# 🛡️ Session Sentinel Watchdog & Hardened Self-Healing Loop Protocol (SENTINEL-SOUP-001)

## 1. Executive Summary & Purpose
This protocol specifies the canonical architecture and operating invariants for **Session Sentinel v2.0**, the background autonomous observer guarding Gerych Prime and the DNK OS Swarm. It synthesizes native session telemetry (`~/.hermes/state.db`) with battle-tested patterns from **MakazhanAlpamys/Soup** (Loop-Hardening, False-Compliance Verification, Semantic Error Distillation, Orphaned Runs Reconciler, and Crash-Resilient Mitigation Logs).

---

## 2. Architectural Pillars (Soup v2.0 Patterns)

### 2.1 Dual-Phase Supervision (In-Flight + Post-Mortem)
- **Phase 1: In-Flight Sentinel Watchdog (`scripts/system/session_sentinel.py --watch $PID`)**:
  - Spawned as a background daemon process concurrently with `scripts/system/gerych.sh`.
  - Non-invasive heartbeat monitoring with POSIX `os.kill(pid, 0)` existence probes.
  - **In-flight trajectory polling**: monitors active SQLite message streams (`poll_in_flight_trajectory`) and writes live anomaly alerts directly to `data/sentinel_alerts.json` without waiting for process exit.
- **Phase 2: Post-Mortem Trajectory X-Ray (`scripts/system/session_sentinel.py --audit-latest` / `on_session_exit`)**:
  - Full trajectory scan upon agent process exit.
  - Anomaly classification, efficiency score computation, and canonical task synthesis.

### 2.2 Soup-Assimilated Hardening Primitives
1. **Loop-Hardening & Anti-Thrashing Detector (`TOOL_LOOP`)**:
   - Detects both lexical read loops (consecutive `read_file` on identical targets without mutations) and repetitive unmutated tool calls.
   - Triggers proactive circuit breaker before MASE 25-tool call limit exhaustion.
2. **False-Compliance & Unverified Completion Guard (`FALSE_COMPLIANCE`)**:
   - Compares assistant's final conversational assertions (e.g., claiming "All tests passed", "100% Green", "Fixed and verified", "всі тести пройшли") against actual tool execution breakdowns.
   - Flags `FALSE_COMPLIANCE` (Critical/High Severity) if narrative claims lack empirical verification artifacts (`pytest`, `verify_all.sh`, `terminal`).
3. **Semantic Error Repetition & Distillation Loop (`SEMANTIC_ERROR_LOOP`)**:
   - Tracks repeated exception types and stack traces across tool executions.
   - If 2+ identical errors occur without invoking self-healing error memory (`dnk_query_error_solutions`), flags a semantic error loop anomaly to prevent context and tool budget burnout.
4. **Orphaned Runs & Zombie Process Reconciler (`--reconcile-orphaned`)**:
   - Reconciles unclosed sessions (`ended_at IS NULL`) whose parent PID is dead (`os.kill(pid, 0)` raises `ProcessLookupError`).
   - Automatically closes state records, generates diagnostic incident specs, and preserves telemetry from dropped terminals or SIGKILLs.
5. **Crash-Resilient Mitigation Logging (MitigationLogWriter Pattern)**:
   - Atomic writes to disk using safe temporary file replacement (`atomic_write` via `.{name}.tmp.{pid}_{ts}` -> `os.replace`).
   - Guarantees zero corrupt JSON/Markdown state on unexpected process crashes or SIGKILLs.
6. **AST Fast-Path & Anti-Search-Loop Interceptor (`EXPLORATORY_NAV_WASTE`)**:
   - Intercepts exploratory `search_files` patterns matching code definitions (`class `, `def `, `interface `, `type `, `function `) and redirects to `dnk_resolve_symbol(symbol=...)` (<20ms AST cache lookup).
   - Blocks serial repetitive `search_files` (>= 4 calls) to prevent context bloat and 90/90 tool budget exhaustion.
7. **Unverified Rewrite Churn Guard & MASE Hard-Stop**:
   - Enforces Invariant 10: blocks consecutive rewrites of the same file (>= 2 modifications) without running verification tests (`pytest`, `verify_all.sh`, `npm test`).
   - Hard-stops tool calls at >= 30 actions per slice, blocking exploratory reads/writes and requiring test execution or slice commit.

### 2.3 Active Pre-Tool Circuit Breaker & Escape Hatch Invariant (Rule 9)
- **Active Interruption Coupling**: While Sentinel records anomalies into `data/sentinel_alerts.json`, `scripts/system/hermes_pre_tool_hook.py` (Rule 9) functions as the active enforcement gate.
- **Alert TTL & Categories**: Checks `data/sentinel_alerts.json` with an mtime freshness window of < 900 seconds (15 minutes). Filters for active loop anomalies (`TOOL_LOOP`, `ERROR_LOOP`, `BUDGET_BREACH`) or `CRITICAL`/`HIGH` severity alerts with loop titles.
- **Mandatory Escape Hatches (Zero-Deadlock Invariant)**:
  1. **Self-Healing Diagnostics**: Tools `dnk_query_error_solutions`, `dnk_record_error_solution`, and `dnk_distiller_tool` are permanently whitelisted so the agent can discover solutions and record distilled fixes.
  2. **Verification Commands**: Terminal and execute_code commands containing verification targets (`verify_all.sh`, `pytest`, `npm test`, `vitest`) are permitted so the agent can test resolutions.
  3. **Emergency Bypass**: Supported via `DNK_BYPASS_SENTINEL=1`, `DNK_SWARM_WORKER=1`, or tool input flag `bypass_sentinel=True`.

### 2.4 Launcher Process Lifecycle & The Exec-Trap Invariant
- **Bash Trap Annihilation under `exec`**: In agent launcher scripts (such as `scripts/system/gerych.sh`), invoking `exec <command>` replaces the shell process at the OS kernel level. As a direct consequence, any bash signal handler (`trap ... EXIT INT TERM`) is erased and will never execute.
- **Graceful Lifecycle Invariant**: To guarantee that cleanup, single-instance lock release, and orphaned session reconciliation reliably execute upon shell exit or cancellation:
  1. Never use `exec` in launcher scripts with traps; invoke commands directly, capture `EXIT_CODE=$?`, execute `cleanup_on_exit`, and exit with `$EXIT_CODE`.
  2. Protect cleanup against re-entrancy via `_CLEANUP_CALLED=1` flag.
  3. Cleanly terminate background helper daemons (such as background Sentinel Observer `$SENTINEL_PID`) via `kill -TERM` before releasing locks.
  4. Run `auto_session_auditor.py --latest` and `session_sentinel.py --audit-latest` during teardown to guarantee closed session records.

### 2.5 Dual-Store Canvas Cache Invalidation (`mtime` check)
- **Problem**: When `SessionSentinel.enqueue_to_canvas()` injects a healing task node into `data/node_task_graph.json`, long-running API server instances (`apps/api`) holding `self._graph` in memory do not automatically observe external CLI disk modifications.
- **Mtime Staleness Check**: `NodeTaskPersistenceManager.load_graph()` must check `os.path.getmtime(self.data_file)` against `self._last_loaded_mtime`. When disk state is newer, an automatic in-memory cache refresh (`force_reload=True`) is performed, ensuring newly enqueued sentinel nodes are immediately visible on the Web Canvas without restarting the API service.

---

## 3. Anomaly Taxonomy & Severity Matrix

| Anomaly Code | Severity | Trigger Threshold | Auto-Healing Target Worker |
| :--- | :--- | :--- | :--- |
| `AUTH_ERROR` | CRITICAL | 401 Unauthorized / Token Expiry | `gerych_auditor` |
| `FALSE_COMPLIANCE` | CRITICAL | Completion claimed without test tool calls | `gerych_auditor` |
| `ORPHANED_SESSION` | HIGH | Terminated session with dead PID / unclosed state | `dnk_dev_fullstack` |
| `SEMANTIC_ERROR_LOOP` | HIGH | 2+ identical errors without `dnk_query_error_solutions` | `dnk_dev_fullstack` |
| `TOOL_LOOP` | HIGH | >= 3 repetitive reads without file edit | `dnk_dev_fullstack` |
| `EXPLORATORY_NAV_WASTE` | HIGH | >= 3 `search_files` without using `dnk_resolve_symbol` | `gerych_prime` |
| `UNVERIFIED_CHURN` | HIGH | >= 2 consecutive file modifications without testing | `gerych_auditor` |
| `PATH_VIOLATION` | HIGH | Hardcoded `/Users/...` or absolute paths | `dnk_dev_fullstack` |
| `BUDGET_BREACH` | HIGH | > 25 tool calls per single slice (hard stop at 30) | `gerych_prime` |
| `TEST_FAILURE` | HIGH | Exit code 1/2 or `AssertionError` | `gerych_auditor` |
| `CI_CD_VIOLATION` | HIGH | Pre-commit hook or build gate rejected | `gerych_auditor` |

---

## 4. Closed-Loop Self-Healing Lifecycle

```
[Agent Execution in gerych.sh]
           │
           ▼
[Session Sentinel Observer] ──(Detects Defect)──► [v2.5 Task Spec Synthesis]
                                                          │
                                                          ▼
                                            [Canvas Task Node Injection]
                                            (Project: dnk_core / Doctor)
                                                          │
                                                          ▼
                                            [dnk_dev_fullstack Dispatched]
                                                          │
                                                          ▼
                                            [SCONES Lesson Distilled]
```

1. **Synthesis**: Writes canonical `docs/plans/self_heal/TASK-DNK-SELFHEAL-*.md` formatted strictly to `GERYCH_TASK_TEMPLATE.md (v2.5)`.
2. **Visual Canvas Enqueue**: Directly registers the healing task in `services/dnk_node_tasks/persistence.py` assigned to `dnk_dev_fullstack` (System Doctor).
3. **Cognitive Distillation**: Saves behavioral boundaries to `.scones/session_lessons.json` and Obsidian Vault for long-term memory retrieval.

### 4.1 Auto-Dispatch Anti-Cascade Guard & Phase 3 Closed-Loop Engine
- When background observers autonomously trigger self-healing subagents (`--auto-dispatch`), they must enforce strict recursion limits:
  1. **Lineage Persistence (`data/self_heal_lineage.json`)**: Every auto-dispatched task records `parent_session_id`, `child_session_id`, `task_id`, `recursion_depth`, `agent`, and `timestamp`. This provides multi-turn lineage independent of transient memory.
  2. **Depth Detection**: Evaluates `get_session_recursion_depth()` by inspecting `data/self_heal_lineage.json` and session messages for markers (`[Self-Heal Autopilot Depth X/Y]` or `Recursion Depth: X`). Standard human sessions evaluate to depth `0`.
  3. **Recursion Circuit Breaker**: If `current_depth >= max_recursion_depth` (default: 2, configurable via `--max-recursion-depth` or `DNK_SENTINEL_MAX_RECURSION_DEPTH`):
     - Auto-dispatch is physically halted (`dispatch_status: "recursion_depth_exceeded"`).
     - A `CRITICAL` anomaly `AnomalyCategory.ERROR_LOOP` is emitted into `data/sentinel_alerts.json`.
     - Escalates to human intervention without spawning further subagents.
  4. Swarm Dispatch Integration: Dispatches healing tasks via `dnk_swarm_dispatch(agent="dnk_dev_fullstack", ...)` targeting the synthesized specification in `docs/plans/self_heal/TASK-DNK-SELFHEAL-*.md`.
  5. Evidence Path Sanitization Invariant: Raw stack traces and error logs embedded in `raw_evidence` must be sanitized via regex (`re.sub(r'/Users/[^/\s]+', '$HOME', raw_evidence)`) before writing task specs, preventing generated plans from failing pre-commit absolute path hygiene audits.

### 4.2 Multi-Profile Database Resolution & Environment Precedence
- **Workspace State DB Discovery**: Under Hermes multi-profile execution, the active SQLite database is dictated by the environment variable `$HERMES_HOME` (e.g. `core/orchestrator/agents/gerych_prime/state.db`). Defaulting blindly to `~/.hermes/profiles/<agent>/state.db` results in `FileNotFoundError` or examining empty default databases, completely blinding Sentinel to live workspace operations.
- **Precedence Hierarchy**:
  1. `Path(os.environ["HERMES_HOME"]) / "state.db"` (if `$HERMES_HOME` is set).
  2. Local agent directory: `Path("core/orchestrator/agents") / agent_name / "state.db"`.
  3. Default user home: `Path.home() / ".hermes/profiles" / agent_name / "state.db"`.

### 4.3 SQLite Tuple Message Schema Defensive Parsing Invariant
- **Schema Format Heterogeneity**: When querying the SQLite `messages` table directly or via raw cursor (`SELECT * FROM messages`), the table structure in Hermes `state.db` is:
  - `col 0`: `id` (int)
  - `col 1`: `role` (str, e.g. `'user'`, `'assistant'`)
  - `col 2`: `content` (str)
  - `col 3`: `tool_calls` (str/JSON or None)
  - `col 4`: `tool_call_id` (str or None)
  - `col 5`: `timestamp` (str)
  - `col 6`: `session_id` (str)
- **Defensive Extraction**:
  - Role: `str(msg[1]) if isinstance(msg, (tuple, list)) and len(msg) >= 2 else msg.get("role", "")`.
  - Content: `str(msg[2]) if isinstance(msg, (tuple, list)) and len(msg) >= 3 else str(msg.get("content", ""))`.
  - Tool Calls: `msg[3] if isinstance(msg, (tuple, list)) and len(msg) >= 4 else msg.get("tool_calls")`.
  - Calling `.get("content")` directly on a raw SQLite row crashes with `AttributeError: 'tuple' object has no attribute 'get'`, while indexing `msg[4]` returns `tool_call_id` instead of the `tool_calls` JSON payload.
  - For safe parsing, use `SessionSentinel.audit_session(session_id)` or `SessionSentinel.fetch_session_data(session_id)` rather than hand-crafting unverified SQL index slices.

### 4.4 Cross-Session Sentinel Audit & High-Velocity MASE Benchmarks
- **The Solo Marathon Trap**: Empirical audit across 182 workspace sessions reveals a sharp drop in agent efficiency (100% -> 10%) on marathon single-agent runs exceeding 300+ tool calls (e.g. `20260906_201203_fab5b6`: 2,873 msgs, 1,378 tools; `20260905_223135_1b90db`: 2,131 msgs, 800+ tools).
- **Core Drivers of Marathon Degradation**:
  1. Repeated read loops on unmutated files (up to 35 repeated reads per session).
  2. Exploratory file search churn (`search_files` executed 160+ times instead of `dnk_resolve_symbol` <20ms AST lookup).
  3. Repetitive error loops without querying `dnk_query_error_solutions`.
- **Enforcement Rules**:
  - Always enforce **MASE (≤ 25 tool calls per slice)**.
  - Step 0 `dnk_triage_task` is mandatory: if complexity > 3 across multiple domains, immediately dispatch via `dnk_swarm_parallel` instead of running solo.

### 4.5 Self-Healing Task Spec Resolution & Archive Lifecycle Protocol
- **Lifecycle Progression**: Self-healing plans generated under `docs/plans/self_heal/TASK-DNK-SELFHEAL-*.md` follow a strict state machine: `Active` -> `Completed` -> Archived in `docs/plans/self_heal/archive/`.
- **Resolution Invariant**: A self-healing task cannot be archived until:
  1. Root cause is resolved and verified by passing unit tests (`pytest`).
  2. Recurring exceptions are distilled into `docs/scones/error_distillations.json` via `dnk_record_error_solution`.
  3. DoD checklist items are checked off (`[x]`) and Status header is marked `Completed`.
  4. File is moved to `docs/plans/self_heal/archive/` preserving historical audit trail.

### 4.6 Headless Driver Fallback & Unverified Churn Elimination
- **Headless Browser Execution Invariant**: External scrapers or stealth browsers (Playwright/Patchright) frequently lack OS-level browser binaries in CI/sandboxed developer containers (`RuntimeError: Executable doesn't exist`).
- **Defensive Design**:
  1. Tool adapters (`core/adapters/dnk_patchright_adapter.py`) must provide a fallback (`mock_mode=True` or HTTP client fallback) to prevent breaking agent loops.
  2. Never iteratively patch tool files (e.g. `stealth_browser_tool.py`) without running unit tests between patches; consecutive unverified edits trigger `UNVERIFIED_CHURN` and lock the agent.
