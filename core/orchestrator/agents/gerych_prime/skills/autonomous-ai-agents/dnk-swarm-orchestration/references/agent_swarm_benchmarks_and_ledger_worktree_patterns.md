# --- DNK-MRH-HEADER ---
# mrh_id: "references/agent_swarm_benchmarks_and_ledger_worktree_patterns.md"
# purpose: "Architectural benchmark of SOTA Swarm Repositories (ruflo, ccswarm, swarms, devswarm, agentswarms) and adoption patterns for DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "Gerych Prime & Maksym Kuzmenko"
# --- END DNK-MRH-HEADER ---

# SOTA Agent Swarm Benchmarks & Architectural Adoption Patterns

## 1. Architectural Taxonomy of the 5 Evaluated Swarm Systems (2026)

### A. ruvnet/ruflo (Meta-Harness & Swarm Coordination Ledger)
- **Repo**: `ruvnet/ruflo` (раніше `claude-flow`, 70.9k+ ⭐, MIT, TypeScript + Rust `RuVector`).
- **Core Pattern**: **Ledger vs Executor Separation**.
  - **Ledger**: Orchestrates swarm topology (`hierarchical`, `mesh`, `star`), manages shared HNSW vector memory (`agentdb.rvf`), enforces access control policies, and surfaces tools via Model Context Protocol (MCP).
  - **Executors**: CLI coding agents (Claude Code, OpenAI Codex, Hermes Agent) that physically execute instructions, write code, and run tests.
- **DNK OS Adoption**: Serve as the canonical model for Gerych Prime's coordination layer and cross-agent MCP event streaming.

### B. nwiizo/ccswarm (Deterministic Git DevOps & Workflow Engine)
- **Repo**: `nwiizo/ccswarm` (151 ⭐, MIT, Rust edition 2024, Tokio).
- **Core Patterns**:
  1. **Git Worktree Isolation**: Each parallel agent executes in a dedicated git worktree branch. Prevents file locking and collision races during simultaneous writes.
  2. **Sangha Consensus**: Formal mathematical voting gate between agents before moving from Plan to Code mutation.
  3. **NDJSON Audit Stream**: Deterministic recording of all agent interactions enabling complete replay and rollback.
- **DNK OS Adoption**: Integrate Git Worktree isolation into parallel swarm execution (`dnk_swarm_parallel`) to prevent multi-worker file overwrite races.

### C. kyegomez/swarms (Algorithmic Prompt Topology Library)
- **Repo**: `kyegomez/swarms` (7.1k ⭐, Apache-2.0, Python v15).
- **Core Patterns**: High-level multi-agent prompt chaining topologies:
  - Mixture-of-Agents (MoA), Council as Judge, Majority Voting, Hierarchical Swarm.
- **Evaluation**: Excellent theoretical catalog of prompt topologies, but lacks system isolation, git awareness, and terminal sandboxing.
- **DNK OS Adoption**: Borrow prompt topology algorithms for reasoning-heavy planning phases; avoid using as execution runtime.

### D. justrach/devswarm (MCP Code Graph Engine)
- **Repo**: `justrach/devswarm` (67 ⭐, AGPL-3.0, Zig 0.15).
- **Core Patterns**: High-performance blast radius analysis and code navigation via MCP.
- **License Warning**: AGPL-3.0 is a restrictive copyleft license. Re-implement algorithms cleanly in-house (Two-Track SOTA Track 2 Clean-Room) if needed.

### E. AgentSwarms-fyi/agentswarms (Lakehouse & BI Web Application)
- **Repo**: `AgentSwarms-fyi/agentswarms` (232 ⭐, Elastic License 2.0, React 19 / Supabase).
- **Evaluation**: Fullstack web application for data lakehouse and BI dashboards. Not an agent CLI harness or developer swarm orchestrator.

## 2. Invariants for DNK OS Swarm Architecture
1. **Never combine Ledger and Executor in one monolithic process**: Keep the coordination ledger lightweight and decoupled from file-mutating workers.
2. **Isolate parallel coding workers via Git Worktrees**: When dispatching 2+ code-writing workers in parallel, ensure they operate in separate worktrees or distinct directory boundaries.
3. **Audit Trails must be Replayable**: Store state transitions as append-only event logs (NDJSON) to allow deterministic rollbacks.
