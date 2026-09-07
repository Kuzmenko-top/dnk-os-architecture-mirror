# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/subagent_sandbox_and_zero_loss_handshake_protocol.md"
# purpose: "Reference architecture for SubagentSandbox environment scoping, zero-loss JSON artifact handshakes, and SessionSentinel trajectory reconciliation."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧪 Subagent Sandbox Isolation & Zero-Loss Handshake Protocol (SANDBOX-001)

## 1. Problem Statement
When orchestrating autonomous swarm workers (`autonomous_subagent`), relying on unbounded environment variables, in-memory function returns, or unbuffered CLI stdio creates three critical failure modes:
1. **Environment Contamination**: Workers inherit parent process credentials, unscrubbed tokens, or polluted Python paths.
2. **Payload Truncation & Stdio Desync**: Large task specifications, canvas schemas, or AST trees passed via CLI flags overflow buffer limits or trigger argument splitting.
3. **Orphaned Subagents & Zombie Sessions**: When a worker crashes or exceeds time bounds without structured artifact signaling, the coordinator hangs or leaks state.

## 2. Core Architecture (`SubagentSandbox` in `core/orchestrator/subagent_sandbox.py`)

### A. Environment Scoping (`prepare_subagent_environment`)
Every dispatched subagent process receives an isolated, scrubbed environment inheriting safe runtime variables (`PATH`, `VIRTUAL_ENV`, `HOME`, `PYTHONPATH`) while injecting explicit execution telemetry:
```python
env = {
    **safe_base_env,
    "DNK_SWARM_WORKER": "1",
    "DNK_AGENT_ID": agent_name,
    "DNK_TASK_ID": task_id,
    "DNK_WORKSPACE_ID": workspace_id,
    "DNK_TRACE_ID": trace_id,
    "DNK_ARTIFACT_DIR": str(sandbox.artifacts_dir),
    "DNK_INPUT_ARTIFACT": str(input_path),
    "DNK_OUTPUT_ARTIFACT": str(output_path),
}
```

### B. Structured Handshake Protocol (Zero Loss)
1. **Input Artifact Packaging (`create_task_handshake`)**:
   - The coordinator writes `{task_id}_input.json` containing `task_id`, `agent`, `task_description`, `parameters`, `target_files`, `trace_id`, and `created_at`.
   - The worker executes inside its designated worktree or scoped directory and reads the contract via `get_subagent_context()`.
2. **Output Artifact Emission (`emit_subagent_output`)**:
   - The worker persists its execution payload to `{task_id}_output.json`:
     - `status`: `"completed"` | `"failed"` | `"interrupted"`
     - `result`: Execution return values, synthesized schemas, or summaries.
     - `modified_files`: List of touched repository relative paths.
     - `metrics`: Tokens, wall time, tool counts.
     - `error`: Formatted error message if failed.
3. **Harvesting & Reconciliation (`harvest_subagent_output`)**:
   - The coordinator reads `{task_id}_output.json`, validates schema conformity, checks modified files against blast radius boundaries, and cleans ephemeral tokens while preserving trace logs.
4. **Coordinator Mailbox & Ledger Sync**:
   - On completion or caught failure, the output manifest is delivered to `SwarmLedger._deliver_to_mailbox("gerych_prime")`.
   - Even when a subprocess exits abnormally or times out, the coordinator wraps execution in a try/finally block that ensures an artifact is harvested or synthesized, preventing coordinator deadlock.

### C. SessionSentinel Integration (`scripts/system/session_sentinel.py`)
- **Orphan Reconciliation**: Detects background subagents left in `running` state past the session timeout and automatically updates their status to `interrupted`.
- **Trajectory Audit**: Inspects tool loop frequencies, token burn rates, and duplicate read/write cycles, auto-generating self-healing task specs (`TASK-DNK-SELFHEAL-*.md`) when anomalies are detected.

## 3. Verification & Testing Invariants
- Unit tests for sandbox isolation live in `tests/verification/test_subagent_sandbox.py` and `tests/verification/test_subagent_sandbox_handshake.py`.
- Zero absolute paths allowed in serialized input/output JSON payloads (strict relative path invariant).
- Local verification command:
  ```bash
  ./.venv/bin/pytest tests/verification/test_subagent_sandbox_handshake.py tests/verification/test_subagent_sandbox.py -v
  ```
