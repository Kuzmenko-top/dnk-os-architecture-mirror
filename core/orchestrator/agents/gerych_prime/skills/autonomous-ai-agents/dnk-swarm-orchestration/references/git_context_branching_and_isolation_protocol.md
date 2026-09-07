# --- DNK-MRH-HEADER ---
# mrh_id: "references/git_context_branching_and_isolation_protocol.md"
# purpose: "Git-like Context Branching, Speculative Task Isolation & Discard Protocol (SLICE-16.5 / BRANCH-CTX-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🌿 Git-like Context Branching & Speculative Task Isolation Protocol (BRANCH-CTX-001)

## 1. Problem Statement & Motivation
During speculative prompt exploration, test debugging, or architectural trials, agents often produce 30,000–50,000 tokens of intermediate hypotheses, tool call payloads, and failed traces. If executed on the main context thread:
- Failed experiments permanently pollute the context window, triggering premature 64k compression.
- The remaining conversation context loses critical earlier instructions due to token budget compaction.
- The main agent incurs unnecessary latency and degradation.

## 2. Architecture: GitContextController & ContextBranch
`core/orchestrator/git_context_controller.py` provides Git-like operations for conversational context:

1. **`create_branch(name, from_branch="main", copy_parent_messages=False, checkout=True)`**:
   - Spawns an isolated `ContextBranch`.
   - By default (`copy_parent_messages=False`), isolates speculative execution with a clean slate (0 token overhead).
2. **`checkout(branch_id)`**:
   - Switches the active conversational context pointer.
3. **`add_message(message, branch_id=None)`**:
   - Appends message to the designated branch, updating `message_count` and estimated tokens (`char_length // 4`).
4. **`commit_branch(branch_id, message)`**:
   - Creates a deterministic `ContextCommit` snapshot.
5. **`merge_branch(branch_id, success=True)`**:
   - If `success=True`: Condenses the branch's commits and findings into a compact summary message (≤500 tokens) merged into `main`. The bloated scratchpad is discarded.
   - If `success=False`: Re-routes to `discard_branch(branch_id)`.
6. **`discard_branch(branch_id)`**:
   - Marks branch as `discarded` and drops all speculative messages.
   - **Guaranteed Result**: 0 tokens leaked into `main`.
7. **Persistence**:
   - Automatic atomic serialization to `cache/context_branches/branches.json` and `commits.json`.

## 3. Integration with Task Triage & MCPSlimGuard
- **`task_triage.py`**:
  - Automatically checks `should_isolate_task(prompt)`. If prompt contains keywords (`experiment`, `refactor`, `try`, `test`, `експеримент`), task triage flags `is_isolated=True`, creates an isolated branch, and tracks speculative work separately.
- **`mcp_slim_guard.py`**:
  - Accepts `context_controller: Optional[GitContextController]`.
  - When present, tool executions performed within isolated sub-routines log sidecar records and tool traces directly to the active branch rather than polluting global session state.

## 4. Verification Pattern & Acceptance Invariants
- **Failed Speculative Task Test**:
  1. Generate 40,000 speculative tokens on branch `failed-exp`.
  2. Invoke `gcc.discard_branch("failed-exp")`.
  3. Verify `len(gcc.branches["main"].messages) == 0` and `gcc.branches["main"].total_tokens == 0`.
- **Successful Merge Test**:
  1. Complete feature verification on `feat-branch`.
  2. Invoke `gcc.merge_branch("feat-branch", success=True)`.
  3. Verify `main` gains only 1 concise summary commit (~20 tokens), preserving 99.9% context capacity.
