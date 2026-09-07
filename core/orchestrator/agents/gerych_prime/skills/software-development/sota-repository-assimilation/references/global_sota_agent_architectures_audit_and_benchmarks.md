# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/global_sota_agent_architectures_audit_and_benchmarks.md"
# purpose: "Comprehensive Comparative Audit & SOTA Patterns: LangGraph, Letta, Agno, Aider, MetaGPT vs Gerych Swarm."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🌐 Global SOTA Agent Architectures Audit & Ingestion Blueprint

## 1. Overview & Objective
This reference captures the comparative architectural audit of Gerych Prime and DNK OS against top-tier open-source autonomous agent architectures on GitHub. It defines the foundational mechanics, operational trade-offs, and concrete assimilation pathways for elevating swarm orchestration, memory engines, and repository navigation.

---

## 2. Global SOTA Architectural Matrix

| Repository | GitHub Slug | Primary Architectural Invariant | Key Capability to Assimilate |
| :--- | :--- | :--- | :--- |
| **LangGraph** | `langchain-ai/langgraph` | **Cyclic StateGraph + Checkpointing** | Durable state machines, transactional Postgres checkpoints, Time-Travel debugging, and first-class Human-in-the-Loop (HITL) breakpoints. |
| **Letta (MemGPT)** | `letta-ai/letta` | **OS-Style Hierarchical Memory** | Split memory model: Working Context (Core), Recall Memory (FTS/Sessions), and Archival Memory (pgvector/embeddings), with autonomous agent self-editing tools. |
| **Agno (Phidata)** | `agno-agi/agno` | **Ultra-Low Latency Core** | Minimalist pure-Python runtime, sub-50ms execution overhead, session storage in pgvector, lightweight sub-agent teaming. |
| **Aider** | `paul-gauthier/aider` | **Tree-Sitter RepoMap & Git Hygiene** | Syntax-tree powered graph compression (1–2k tokens), Pagerank symbol prioritization, and atomic single-slice git commits. |
| **MetaGPT** | `geekan/MetaGPT` | **SOP-Driven Multi-Agent Company** | Formal Standard Operating Procedures (SOPs) exchanging structured typed artifacts (PRD -> Architecture -> Spec -> Code -> Review) rather than free-form chat. |
| **CrewAI** | `crewAIInc/crewAI` | **Hierarchical Delegation & Tool Cache** | Supervisor/worker delegation trees, shared memory caches, and heavy tool output caching to avoid redundant executions. |

---

## 3. Detailed Architectural Breakdown

### 3.1. LangGraph: Cyclic StateGraph & Durable Checkpoints
- **Core Mechanism**: Represents agent workflows as directed cyclic graphs where nodes are pure functions and edges are conditional state transitions.
- **State Reducers**: Typed dictionaries with reducer functions (e.g., `operator.add` for message appending) prevent state corruption during concurrent node execution.
- **Durable Checkpoints**: State is persisted at every superstep to PostgreSQL. If a network blip or API error occurs, execution resumes from the exact failed step without repeating prior steps.
- **DNK OS Assimilation**: Replace heterogeneous orchestration scripts (`swarm_engine.py`, `swarm_orchestrator.py`) with a centralized `SwarmControlPlane` adopting LangGraph's deterministic state machine model.

### 3.2. Letta (MemGPT): OS-Style Memory Management
- **Core Mechanism**: Models LLM context limits as RAM in an operating system.
  - *Core / Working Memory*: Fixed-size memory block always present in prompt (user persona, system guidelines).
  - *Recall Memory*: Full conversational log searchable via FTS5 or timestamp window.
  - *Archival Memory*: Out-of-context long-term storage stored in vector databases for deep conceptual search.
- **Self-Editing Memory**: The agent explicitly calls memory editing tools (`core_memory_append`, `core_memory_replace`, `archival_memory_insert`) as proactive cognitive actions.
- **DNK OS Assimilation**: Unify SCONES L1/L2/L3 memory into an integrated Memory Broker with autonomous self-editing capabilities.

### 3.3. Aider: Tree-Sitter AST RepoMap
- **Core Mechanism**: Parses repository source code using `tree-sitter` to extract tags (class definitions, function declarations, call sites).
- **PageRank Dependency Graph**: Runs PageRank on the AST graph to score symbol importance relative to the current working set, building an ultra-dense repository map (~1024 tokens).
- **Zero-Waste Impact**: Replaces repetitive multi-turn `read_file` and `search_files` probes with instant, high-precision code navigation.
- **DNK OS Assimilation**: Upgrade `scripts/system/repo_map.py` and `dnk_resolve_symbol` with call site graphs (`find_callers`, `resolve_symbol_graph`, `--calls`, `--graph`, `include_calls=True`) to resolve definition + caller references in <50ms without reading full files.

### 3.4. MetaGPT: SOP-Driven Multi-Agent Artifact Pipeline
- **Core Mechanism**: Enforces Standard Operating Procedures (SOPs) based on software engineering best practices. Agents communicate through typed documents rather than conversational chatter.
- **Artifact Contract**: Every role (Product Manager, Architect, Engineer, QA) consumes an upstream artifact and produces a downstream validated artifact.
- **DNK OS Assimilation**: Bridge `GERYCH_TASK_TEMPLATE.md` and `generate_evidence.py` into a strict artifact pipeline across the 14 swarm agents.

---

## 4. Key Monorepo Pitfalls & Remediation Rules

1. **State Leakage into Agent Codebases**:
   - *Rule*: Never store runtime SQLite files (`state.db`), checkpoints, or LSP caches inside `core/orchestrator/agents/*/`. Keep agent folders strictly declarative (YAML/MRH Markdown).
2. **Zombie Staging Directories**:
   - *Rule*: Decommission staging directories immediately post-migration (`core/hermes_agent_staging/`, `core/hermes_versions/`).
3. **Context Window Tax**:
   - *Rule*: Employ dynamic tool pruning based on task triage classification to prevent feeding unneeded tool schemas (video, shopify, smart home) into unrelated tasks.
4. **Skill Directory Hygiene & Cache Pruning**:
   - *Rule*: Never let `__pycache__` or `.DS_Store` files linger inside `skills/` subtrees. Skills must remain strictly declarative (MRH markdown, YAML, references, templates, scripts) to avoid bloat and ensure fast indexing.
