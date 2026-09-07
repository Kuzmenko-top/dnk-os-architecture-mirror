# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_sota_deepseek-harness"
# purpose: "Comprehensive Architectural Audit and SOTA Assimilation Blueprint for deepseek-ai/deepseek-harness into DNK OS / DNK_HUB"
# author: "Gerych (Hermes Prime) & Maksym"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-05"
# alters_files: ["docs/tech/sota_assimilation/SOTA_DEEPSEEK-HARNESS_ASSIMILATION.md"]
# triggers_tasks: ["TASK-DSH-ASSIMILATION-001"]
# --- END DNK-MRH-HEADER ---

# 🧬 Comprehensive Audit & SOTA Assimilation Blueprint: DeepSeek Harness (`dsh`)

- **Upstream Repository**: [deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)
- **Official Identity**: DeepSeek Harness (`dsh`) — *"Everything is a Plugin"*
- **Upstream Metrics**: ~212,700+ ⭐ Stars | 24,970+ 🍴 Forks | 50+ Domain Package Groups | Master Branch
- **License**: **MIT License** (Track 1 Permissive — Direct Template, Architecture & Pattern Assimilation)
- **Primary Technology Stack**: TypeScript / Node.js (Monorepo with pnpm workspaces), Python SDK (`deepseek-harness-sdk`), Rust/C++ Native Sidecars (Landlock sandboxing)
- **Core Framework Foundation**: Powered by **Cordis** (Inversion of Control & Spatiotemporal Composability microkernel)
- **DNK OS Assimilation Track**: **Track 1 (Permissive Component Adaptation & Hexagonal Core Porting)**
- **Target Bounded Context in DNK_HUB**:
  - `core/orchestrator/harness/` (Pluggable Microkernel & Reversible Lifecycle)
  - `core/security/sandbox/` (OS-Level Landlock / Seatbelt / bwrap Sandboxing)
  - `core/executors/ptc/` (Programmatic Tool Calling & Dynamic SDK Generation)
  - `core/contracts/dsh_event_contract.yaml` (Append-Only Event Store & Crash Reconstruction)

---

## 1. Executive Summary & Repository Anatomy

DeepSeek Harness (`dsh`) is DeepSeek AI's flagship open-source agent runtime framework. Unlike traditional monolithic or hardcoded agent loops (e.g. LangChain, AutoGen, or vanilla loop runners), `dsh` is built entirely on the principle of **radical modularity: everything is a plugin**.

There is no privileged core that cannot be replaced or bypassed. Every capability — from LLM provider adapters, session persistence backends, tool definitions, turn stepping, to the agent loop itself — is a Cordis plugin registering reversible effects and services into a shared, scoped context (`ctx`).

### Key Monorepo Architecture (262 Packages across 34 Groups)

```text
deepseek-harness/
├── packages/
│   ├── core/                  # Spine: agent, agent-loop, tools, session, system-prompt, scope
│   ├── api/                   # BFF gateway, Typert RPC, session/workspace controllers
│   ├── typert/                # Type graph generator, runtime schema registry
│   ├── bundle/                # Composable launch bundles (base, web-app, headless, sdk-app, acp-app)
│   ├── client/                # Modular Web Client UI (Vue/React cards, chat, layout, approvals)
│   ├── llm/                   # Abstract LLM capability & DeepSeek provider adapters
│   ├── tools/                 # Guarded pipeline, PTC runtime bridge, dynamic SDK generation
│   ├── sandbox/               # Landlock (Linux), Seatbelt (macOS), ACL (Windows) process confinement
│   ├── terminal/ & shell/     # Persistent PTY sessions, command executors
│   ├── subagent/ & workflow/  # Multi-agent delegation, worker-thread orchestration scripts, Ralph loops
│   ├── session/ & session-query/ # Append-only SQLite/JSONL event store, time-travel, crash repair
│   ├── compaction/            # Context window pressure compaction & tool-output trimming
│   ├── lsp/                   # Language Server Protocol code navigation seam
│   ├── skill/                 # Provider-based skill registry with LOD progressive disclosure
│   └── extensions/            # Self-modification: agent live plugin inspection & mounting
├── python/                    # Python SDK + bundled dsh runtime binary sidecar
├── native/                    # Landlock run native Node.js C++ addon
└── vendor/                    # Pinned upstream Cordis source
```

---

## 2. Deep Architectural Audit: 7 Killer Paradigms

### Paradigm 1: Cordis Microkernel & Reversible Context (`ctx`)
- **Mechanism**: Every module registers its capabilities as `ctx.service()` or `ctx.effect()`. When a plugin is unmounted or disposed, all its listeners, tools, routes, and prompt contributions are cleanly and atomically rolled back without restarting the host process.
- **Value for DNK OS**: DNK OS has 14 specialized Swarm Workers. Implementing reversible context allows dynamic hot-reloading of swarm skills and tools on the fly without state corruption or memory leaks.

### Paradigm 2: The 5-Stage Guarded Tool Execution Pipeline
The tool registry (`dsh-tools`) executes every model-facing tool call through an uncompromising waterfall pipeline:
1. `tools/pre-execute` (Extensible waterfall): Plugins can return `allow`, `deny`, or `ask` (human-in-the-loop approval).
2. `ctx.tools.guard()` (Monotonic Synchronous Guard): Invariant checks where any denial is permanently binding and cannot be overridden by later listeners.
3. `tools/execute` (Around-Dispatch Wrapper): Wraps invocation for execution timeouts, circuit breakers, and retry logic.
4. `tools/post-execute` (Output Transformation): Result interception, sanitization, and context metadata injection.
5. `tools/result` (Frozen Observability): Read-only event broadcast with immutable result payloads.

### Paradigm 3: PTC (Programmatic Tool Calling) Mode & On-the-Fly SDK
- **Problem**: When an agent needs to perform 10 tool calls (e.g. checking 10 files or running 5 queries), standard tool calling requires 10 round-trips to the LLM, burning 50k+ tokens and wasting 60+ seconds.
- **`dsh` Solution**: In PTC mode, `dsh` presents a single meta-tool `run_code(code: string)` to the LLM and dynamically synthesizes an in-memory typed SDK in TypeScript or Python (e.g. `await tools.read_file({...})`).
- The LLM writes a 5-line script with `Promise.all` or `for` loops. The code executes in an isolated worker thread or sandbox, batching calls in 1 step!
- **Value for DNK OS**: Directly aligns with DNK OS Zero-Waste protocol and eliminating 90/90 tool budget exhaustion!

### Paradigm 4: Append-Only `SessionEvent` Log & Crash-Safe Resumption
- All session state is represented as an immutable append-only event stream stored in SQLite or JSONL.
- If a process crashes mid-turn, the restart routine automatically synthesizes `interruptedTurnClosers`, preventing log corruption.
- Forking a session at any historical turn boundary is deterministic: `ctx.agents.create({ seed, parentSession })`.

### Paradigm 5: Zero-Trust Triple-Tier OS Sandboxing
- Subprocess execution (`dsh-sandbox`) enforces 3 strict security rungs:
  - `read-only`: Absolute read-only filesystem access.
  - `workspace-write`: Write permissions restricted exclusively to the task's workspace directory (`ws-alpha-001`).
  - `danger-full-access`: Unrestricted host execution (requires human approval).
- Enforced natively via Linux **Landlock / bwrap**, macOS **Seatbelt (`sandbox-exec`)**, and Windows ACL tokens.

### Paradigm 6: Worker-Thread Workflow Orchestration (`ralph` & `workflow`)
- Models can author orchestration scripts that fan out tasks across subagents in worker threads without blocking the Node/Python event loop.
- The `ralph` tool implements iterative fresh-agent loops with feedback barriers.

### Paradigm 7: Context-Pressure Compaction & Head+Tail Tool Trimming
- Dynamic token counting monitors KV-cache consumption.
- Before LLM-based summarization occurs, oversized tool outputs are trimmed with head+tail truncation, saving substantial tokens before triggering full compaction.

---

## 3. Comparative Matrix: `dsh` vs Hermes Agent v0.21.0 vs DNK OS

| Feature / Dimension | DeepSeek Harness (`dsh`) | Hermes Agent v0.21.0 | DNK OS / DNK_HUB (Current) | Target Unified Architecture |
|---|---|---|---|---|
| **Architecture** | Microkernel / All-Plugin (Cordis) | Monolithic CLI / Agent Loop | Unified Hub & Swarm Orchestrator | Hybrid Hub with Microkernel Adapters |
| **Language** | TypeScript + Python SDK | Python (asyncio) | Python (FastAPI, Pytest) + TS (Web) | Native Python Core + TS Web/Workers |
| **Tool Execution** | 5-stage Guarded Waterfall + PTC | Single Dispatcher + Approvals | Native Tool Registry + Pre-Tool Hook | Port 5-Stage Guard Pipeline + PTC |
| **Tool Calling Mode** | Native, PTC (`run_code`), or Dual | Native function calling only | Native function calling | Add PTC Mode for batch tool calls |
| **Sandboxing** | Landlock (Linux) + Seatbelt (macOS) | Basic workdir checks | Relative path invariant & Pre-Tool Hook | Add Native OS Sandboxing engine |
| **Event Sourcing** | Immutable `SessionEvent` Log (SQLite) | Local SQLite session store | SQLite + SCONES Cognitive Memory | SCONES L1/L2/L3 + Append-Only Log |
| **Multi-Agent** | In-process + ACP + Subagent providers | `delegate_task` (Background subagents) | TaskDNA DAG + 14 Swarm Profiles | TaskDNA DAG with DSH Worker Threads |
| **Self-Modification**| Live plugin mount/unmount | Skill creation/edit | Evolutionary TaskDNA + SCONES | Reversible Runtime Plugin Registry |

---

## 4. Assimilation Blueprint & Engineering Roadmap (DNK_HUB)

We execute assimilation under **Track 1 (Permissive Component Adaptation & Clean Architecture Porting)** across 4 discrete phases:

### 🚀 Phase 1: Core Event Contract & 5-Stage Tool Waterfall (`core/security/`)
1. Port the 5-stage tool guard pipeline into Python (`core/security/tool_guard_pipeline.py`):
   - `pre_execute`: Policy check & human approval gating.
   - `guard`: Monotonic synchronous safety invariants (e.g. banning absolute paths, preventing accidental `.env` leak).
   - `around_execute`: Execution timeout & circuit-breaker protection.
   - `post_execute`: Output truncation & context engineering.
   - `observe`: Broadcast to SCONES L1 memory and local telemetry.

### ⚡ Phase 2: Python Programmatic Tool Calling (PTC Engine) (`core/executors/ptc/`)
1. Implement `DNK_PTC_Engine`:
   - Expose `execute_code` with an auto-generated, type-safe Python SDK binding all DNK OS tools (`from dnk_tools import read_file, search_files, terminal, ...`).
   - Enable Gerych Prime and Swarm workers to execute multi-tool investigative queries in a single turn.

### 🛡️ Phase 3: OS-Level Subprocess Sandboxing (`core/security/sandbox/`)
1. Port `dsh-sandbox` logic to Python:
   - macOS: Generate dynamic Seatbelt profiles (`sandbox-exec -p '(version 1)...'`).
   - Linux: Integrate Landlock and bubblewrap (`bwrap`) confinement for workspace directories.
   - Enforce `workspace-write` policy on all shell/terminal execution tools.

### 🔄 Phase 4: Hexagonal Bridge to DeepSeek Harness (`adapters/dsh_bridge.py`)
1. Provide a dual-runtime bridge:
   - Allow DNK_HUB to spin up `dsh --profile headless` or `dsh --profile sdk` via JSON-RPC stdio.
   - Route DeepSeek models (DeepSeek-V3, DeepSeek-R1) through native `dsh` runtime when optimal.

---

## 5. Risk Assessment & Legal Compliance

1. **License Safety**: MIT License allows commercial use, modification, distribution, and private use. No copyleft contamination.
2. **Trademark Notice**: "DeepSeek Harness" is a registered trademark of DeepSeek AI. In DNK OS, all internal adapters and modules will be prefixed with `dnk_dsh_` or `dnk_harness_` to respect brand guidelines.
3. **Zero-Rsync Invariant**: We DO NOT blindly rsync upstream code into DNK_HUB. We extract architectural patterns, build clean-room Python implementations, and link external packages via package managers.

---

*Authored by Gerych Prime for Maxim. Certified for integration under TaskDNA standard.*
