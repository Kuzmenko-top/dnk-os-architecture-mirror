# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/solo_agent_syndrome_cure_and_subagent_spawning_protocol.md"
# purpose: "Operational Protocol for Curing Solo Agent Syndrome via Physical Subagent Spawning, Artifact Boundaries, and Role-Based Tool Gating."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🐝 Solo Agent Syndrome Cure & Physical Subagent Spawning Protocol

## 1. Problem Definition (The Solo Agent Bottleneck)
In large multi-agent systems, the Orchestrator/Prime agent naturally gravitates toward "Path of Least Resistance": directly invoking code-editing tools (`read_file`, `patch`, `terminal`) in its own context session instead of spawning specialized domain workers (`gerych_builder`, `dnk_dev_fullstack`, `dnk_shopify`).

### Direct Consequences:
- **Context Window Bloat**: Prime exhausts its prompt budget on low-level file content and test logs.
- **25-Tool Turn Limit Exhaustion**: Single turn attempts to perform triage, implementation, unit tests, and validation sequentially.
- **Worker Starvation**: 13 specialized swarm agents remain idle registered descriptors in memory while Prime acts as a solo worker.

---

## 2. The 4 Pillars of the Architectural Cure

### Pillar 1: Physical Process & Context Isolation
Never execute multi-domain code tasks within Prime's direct conversation thread.
1. **Background Hermes Subagents**: Dispatch via `delegate_task(goal=..., tasks=[...])`.
2. **Dedicated CLI Subprocess**: Execute via `hermes -p <agent_role> --goal "<slice_goal>" --workdir <sandbox>` or `./scripts/system/gerych_swarm.sh --agent <agent_role> -q "<task>"`.
- **Result**: Subagent starts with a fresh 0-token conversation history, receives only the target slice specification, and has its own isolated 25-tool action budget.

### Pillar 2: Strict Artifact Boundary (Input Spec ➔ Output JSON)
The orchestrator must never inspect subagent conversational chatter or intermediate tool attempts.
- **Worker Mailbox Directory**: `data/swarm_artifacts/`
  - Input spec: `data/swarm_artifacts/{task_id}_input.json`
  - Output artifact: `data/swarm_artifacts/artifact_{agent}_{timestamp}.json`
- **Worker Output Contract**:
  ```json
  {
    "worker": "dnk_dev_fullstack",
    "task_id": "task_20260906_120000_abc123",
    "status": "completed",
    "target_files": ["apps/api/routers/auth.py", "tests/verification/test_auth.py"],
    "test_exit_code": 0,
    "diff_summary": "+58 lines, -4 lines",
    "artifact_path": "data/swarm_artifacts/artifact_dnk_dev_fullstack_20260906_120500.json"
  }
  ```
- Prime evaluates only the final JSON artifact and test status.

### Pillar 3: Role-Based Tool Gating (Enforced Separation of Concerns)
- **Prime (Mentor / Architect / Swarm Dispatcher)**:
  - Allowed: `dnk_triage_task`, `dnk_decompose_task_dna`, `delegate_task`, `dnk_swarm_parallel`, `read_file` (specs/manifests only), `scones_get_memories`, `obsidian`.
  - Prohibited: direct code editing (`patch`, `write_file`) on multi-domain production modules when Complexity $C > 3$.
- **Workers (`gerych_builder`, `dnk_dev_fullstack`, `dnk_shopify`)**:
  - Allowed: `patch`, `write_file`, `terminal`, `tsc`, `pytest`.

### Pillar 4: Autonomous Triage Gate (Step 0)
When complexity $C = F_{files} + 2 \times D_{domains} + 3 \times S_{stages} > 3$:
- Direct modification by Prime is halted.
- Immediate dispatch to parallel or sequential worker swarm is mandatory.

---

## 3. Verified Physical Headless Implementation

### A. Subprocess Bridge (`scripts/system/gerych_swarm.sh`)
When running a worker, environment variables and CLI parameters must be strictly preserved:
```bash
# Mandatory invocation pattern inside gerych_swarm.sh
export HERMES_AGENT_NAME="$TARGET_AGENT"
exec "$HUB_ROOT/scripts/system/gerych.sh" --agent "$TARGET_AGENT" "$@"
```

### B. Coordinator Integration (`core/orchestrator/swarm_coordinator.py`)
`SwarmCoordinator._execute_headless_subagent`:
1. Serializes `task.payload` and `input_artifacts` to `data/swarm_artifacts/{task_id}_input.json`.
2. Launches `./scripts/system/gerych_swarm.sh --agent {agent} -q "{task_description}"` with `timeout=120` seconds.
3. Checks for generated artifacts, captures stdout/stderr without flooding orchestrator logs, and builds the return payload.

### C. Tool Dispatch Surface (`core/hermes_agent/tools/dnk_swarm_tool.py`)
`dnk_swarm_dispatch` signature must expose:
- `mode: Literal["direct", "autonomous_subagent"] = "direct"`
- `parameters: Optional[Dict[str, Any]] = None`
- Payload must pass `mode`, `target_files`, and `timeout_seconds` to `SwarmCoordinator.dispatch_task()`.

---

## 4. Technical Pitfalls & Hardened Fixes

| Pitfall | Root Cause | Hardened Fix |
|---|---|---|
| **Identity Reset to Prime** | `gerych_swarm.sh` parsed `--agent <name>` but called `gerych.sh` without passing `--agent "$TARGET_AGENT"`. | Pass `--agent "$TARGET_AGENT"` and `export HERMES_AGENT_NAME="$TARGET_AGENT"` explicitly. |
| **Silent Direct Fallback** | `dnk_swarm_dispatch` ignored the `mode` parameter and hardcoded `"action": "execute"`. | Bind `mode` parameter directly into `coordinator.dispatch_task` payload. |
| **Pytest `sys.path` Shadowing** | Prepending `core/hermes_agent` to `sys.path` caused python to resolve `import core` from `core/hermes_agent/core` instead of workspace root `core/`. | Check if path already in `sys.path` before inserting, and preserve workspace root `$HUB_ROOT` as highest priority `sys.path[0]`. |
| **Subagent Timeout Hang** | 30-second default was insufficient for headless subprocess bootstrapping and LLM call. | Calibrated default timeout to 120 seconds (`timeout_seconds=120`). |
