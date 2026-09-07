# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/standards/DNK-SEC-005_langgraph-execution-sandbox.md"
# purpose: "Security Standards and Sandbox Egress Controls for Stateful Graph Execution"
# author: "Maxim"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

# 🛡️ Security Standards: Stateful Sandboxing (DNK-SEC-005)

This specification defines the security standards, sandbox boundaries, and egress guardrails for executing stateful graphs and MCP tool integrations inside the DNK OS Core.

## 1. Sandbox Boundaries

All execution of Graph Nodes occurs strictly within isolated subagent runtimes (e.g. docker-based containers for Rick, Yuriy, and Cas):
- **Local Workspace Locks:** No node execution can navigate outside the relative subagent workspace path. Hard checks prevent path traversal or raw host write access.
- **Volume Masking:** Temporary directories, dependencies (`node_modules`), or build artifacts are masked to prevent local host filesystem pollution.

## 2. Resource & Cycle Guardrails

To prevent run-away loops (e.g. self-referencing cyclic transitions) and excessive LLM API or token consumption, the runtime implements three hard gates:
1. **Loop Count Cap:** The maximum number of consecutive node transitions in a single thread execution is capped at `30`. If this is exceeded, the orchestrator raises a `CyclicOverflowError` and pauses for manual inspection.
2. **Context Compaction Gate:** When the token size of messages in the shared state exceeds 85% of the model's context window, a smart compaction reducer is triggered at a clean message boundary, shrinking historical steps while preserving the cumulative altered-files log.
3. **Execution Timeout:** Individual node execution is capped at `180s` (3 minutes) to prevent hanging system calls.

## 3. Network & Egress Constraints

- **No Unauthorized Network Connections:** Sandboxed node environments operate with full network-drop firewall policies.
- **MCP Whitelist:** Active nodes can only route to authenticated MCP servers registered in the `omni_router.py` database with matching cryptographic signatures.
- **State Modifications:** Any tool call altering code files, issuing payments, or changing system settings triggers a `Task Start Gate` / `Proof Contract` approval requirement, pausing execution until Maxim's terminal grants explicit authorization.
