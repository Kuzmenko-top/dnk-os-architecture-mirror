# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/software-development/sota-repository-assimilation/references/sota_context_management_and_compression_patterns.md"
# purpose: "SOTA Context Management, Compression & Token Tax Elimination Patterns from Global Open Source (Hermes LCM, Continuous Claude, MCP Slim Guard, Git Context Controller, CodeGraph-Rust)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧠 SOTA Context Management & Compression Patterns (Global Open-Source Analysis)

## 📌 Executive Summary
Context Window Tax (bloat caused by static system prompts, monolithic tool schema injection, and unbounded terminal/diff outputs) degrades reasoning fidelity and causes 64k/128k context exhaustion.
This reference codifies the 6 key architectural patterns identified across state-of-the-art open-source projects on GitHub in 2025–2026.

---

## 🏛️ 1. Six Architectural Patterns

### Pattern 1: Lossless Context Management via DAG & FTS5 (`hermes-lcm`)
* **Reference Repo**: `stephenschoettler/hermes-lcm` (Voltropy PBC / Ehrlich & Blackman).
* **Core Philosophy**: *"Bounded Context, Unbounded Memory."* Never destroy information via lossy summarization.
* **Mechanism**:
  - Turns and tool outputs are stored in a local SQLite database backed by FTS5 full-text search.
  - Active context maintains only recent turns and hierarchical DAG summary nodes across multiple depths ($D_0, D_1, D_2$).
  - When specific historical code, diffs, or stack traces are needed, the agent invokes on-demand retrieval tools:
    - `lcm_grep(query)`: FTS5 search across conversation lineage.
    - `lcm_expand(node_id)`: Hydrates full turn content for a specific compressed node.
    - `lcm_load_session(session_id)`: Reconstitutes parent session state without inflating current tokens.
* **DNK Swarm Applicability**: Native compatibility with Hermes Agent runtime; directly integrates into `session_search` and SCONES memory retrieval.

### Pattern 2: "Compound, Don't Compact" with Continuity Ledgers (`Continuous-Claude-v3`)
* **Reference Repo**: `parcadei/Continuous-Claude-v3`.
* **Core Philosophy**: Avoid recursive context compaction churn by storing state in persistent markdown ledgers outside the conversational window.
* **Mechanism**:
  - **Continuity Ledger (`CONTINUITY_*.md`)**: Self-contained state log tracking goals, current branch, executed steps, test verification, and blockers.
  - **YAML Handoff Protocol**: Subagents receive strictly scoped input manifests and return structured YAML completion summaries (`status: green`, `files_changed`, `tests_passed`).
  - **Subagent Context Firewall**: Worker tool outputs (heavy stdout, compiler errors) are sequestered within the worker process and never leak into the primary orchestrator context.
* **DNK Swarm Applicability**: Standardizes Gerych Swarm handoffs across `dnk_swarm_dispatch` and `dnk_swarm_parallel` to ensure Gerych Prime stays under 20k tokens.

### Pattern 3: JIT Tool Schema Virtualization (`mcp-slim-guard`)
* **Reference Repo**: `lennney/mcp-slim-guard`.
* **Core Philosophy**: Statically injecting 50–100 tool schemas consumes 15,000–30,000 tokens of dead weight before any user interaction.
* **Mechanism**:
  - Proxies MCP tool catalogs into 3 universal meta-tools:
    1. `find_tool(query)`: Vector/regex search returning only matching tool names and signatures.
    2. `call_tool(tool_name, arguments)`: Dynamically validates and routes the call to the underlying server.
    3. `read_result(result_ref, offset, limit)`: Paginates large payloads stored in a sidecar cache.
  - Reduces toolset context overhead to a constant ~150 tokens.
* **DNK Swarm Applicability**: Evolves DNK Slice 16.2 (`lazy_tool_loader.py` + `tool_aliases.py`) into an automated dynamic schema discovery layer.

### Pattern 4: Git-Like Context Branching & Merging (`git-context-controller`)
* **Reference Repo**: `faugustdev/git-context-controller` (GCC).
* **Core Philosophy**: Treat context window tokens as a transactional git repository.
* **Mechanism**:
  - `CONTEXT_BRANCH(branch_name)`: Forks the conversation state before executing risky or exploratory tool runs.
  - `CONTEXT_COMMIT(message)`: Creates a milestone snapshot of verified working code.
  - `CONTEXT_ABORT()`: Drops failed attempts, error tracebacks, and dead-end iterations without leaving trace tokens in the main context.
  - `CONTEXT_MERGE()`: Injects only the verified final diff and solution rationale back into the primary thread.
* **DNK Swarm Applicability**: Enhances `TaskForest` and subagent isolation so failed worker iterations never contaminate Gerych Prime.

### Pattern 5: In-Memory AST Dependency GraphRAG (`codegraph-rust`)
* **Reference Repo**: `Jakedismo/codegraph-rust`.
* **Core Philosophy**: Reading raw source files sequentially to understand architecture wastes 90% of token budget on syntax noise.
* **Mechanism**:
  - Fast Rust-based AST parser storing symbols, imports, calls, and type hierarchies in an in-memory graph database (SurrealDB).
  - Queries return targeted call hierarchies (`get_callers`, `get_dependencies`) in 15–20 lines of JSON instead of 5,000 lines across 10 files.
* **DNK Swarm Applicability**: Integrates with `dnk_resolve_symbol` and `repo_map.py` for sub-20ms instant symbol location.

### Pattern 6: Deterministic Observation Masking over LLM Summarization (NeurIPS 2025)
* **Academic Finding**: "The Complexity Trap" demonstrated that LLM-based recursive summarization hallucinates details and drops critical flags.
* **Mechanism**:
  - Keep human user prompts, tool command names, and exit codes intact.
  - Mask large outputs (>2,000 chars) after initial consumption with `[OUTPUT MASKED: 142 lines, exit_code: 0, preview: "..."]`.
  - Store full stdout in `cache/observations/<hash>.log` for on-demand inspection.

---

## 🚀 Practical Implementation Roadmap for DNK OS

1. **Slice 16.2 (Completed)**: `LazyToolLoader`, `ToolAliases`, `AdaptivePromptEngine` (88.8% token tax reduction, from 25k to 2.8k tokens).
2. **Slice 16.3 (Observation Sidecars)**: Implement deterministic payload masking on bash/read_file outputs with hash-addressed sidecar cache.
3. **Slice 16.4 (Hermes LCM Assimilation)**: Plug SQLite FTS5 multi-depth DAG storage into Gerych Prime's long-running agent harness.
4. **Slice 16.5 (Branching Task Forest)**: Isolate experimental worker branches within TaskForest execution to guarantee clean orchestrator state.
