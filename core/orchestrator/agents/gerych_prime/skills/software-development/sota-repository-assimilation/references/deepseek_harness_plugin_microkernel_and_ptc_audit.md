# --- DNK-MRH-HEADER ---
# mrh_id: "skills_sota_deepseek_harness_reference"
# purpose: "Reference patterns for DeepSeek Harness (dsh) Cordis Microkernel, 5-Stage Tool Waterfall, PTC Engine, and Prefix Cache Engineering"
# author: "Gerych Prime & Maksym"
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

# DeepSeek Harness (`dsh`) SOTA Audit & Reference Patterns

## 1. Upstream Anatomy & Monorepo Scale
- **Repo**: `deepseek-ai/deepseek-harness` (`dsh`)
- **License**: MIT License (Track 1 Permissive — Direct Template, Architecture & Pattern Assimilation)
- **Scale**: ~212,700+ ⭐ Stars, 24,970+ Forks, 15,000+ Commits, 50+ Domain Package Groups (`packages/*`).
- **Foundational Paper**: *"A Programming Paradigm for Spatiotemporal Composability"* (`arXiv:2608.25512`).

### Fast Inspection Patterns
When auditing massive multi-package monorepos (50+ domains, 10k+ files):
- **Fast Tree Discovery**: Use GitHub REST API recursive tree lookup:
  `GET https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1`
  This returns the full hierarchy in <1s without cloning or burning git credentials.
- **Selective Raw Extraction**: Fetch targeted `package.json` and `README.md` files directly from `raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}` via standard HTTP.

## 2. Core Architectural Patterns

### A. Cordis Microkernel & Reversible Effects (`ctx`)
- Everything in the agent runtime is a plugin mounted onto `ctx`. There is no hardcoded, immutable core loop.
- Plugins register services via `ctx.service('name', implementation)` and reversible effects via `ctx.effect(() => { ... return cleanup; })`.
- Unmounting or reloading a plugin atomically tears down listeners, schema contributions, and tool registrations without side-effects or memory leaks.
- Profiles (`web`, `headless`, `sdk`, `sdk-minimal`, `acp`) are composed via bundle layers and patchable via `cordis.patch.yml`.

### B. Guarded Tool Execution Pipeline (The Strict Lifecycle)
All tool calls are evaluated through a strict guarded waterfall:
1. `tool/call` event: Pre-flight event logged to the immutable append-only session store before any side effects occur ("Model-visible means logged" invariant).
2. `tools/pre-execute` waterfall: Returns `allow`, `deny`, or `ask` (human confirmation trigger via `ctx.approval`).
3. `ctx.tools.guard()`: Synchronous monotonic guard barrier. Any single denial immediately and irreversibly aborts execution.
4. `tools/execute` waterfall: Lifecycle wrapper managing timeouts, automatic circuit-breakers, retries, and intent gates (`fs/write-intent`, `fs/edit-intent`).
5. `tools/post-execute` waterfall: Content sanitization, context metadata injection, and token budget formatting.
6. `ToolDefinition.finalizeContent`: Synchronous invariant protection ensuring clean output boundaries.
7. `tools/result`: Frozen immutable audit outcome broadcast to subscribers and session projections.

### C. Programmatic Tool Calling (PTC) Engine (`ctx.codeRuntime`)
- Instead of requiring N sequential round-trips for N tool calls (burning tokens and hitting tool call budgets), PTC provides a single meta-tool `run_code(code)`.
- An in-memory typed SDK is generated dynamically (`await tools.read_file(...)`, `tools.search(...)`).
- The LLM writes a self-contained script executing loops, parallel queries (`Promise.all`), and filtering directly inside a worker thread, returning consolidated results in 1 step.
- Backends supported:
  - `dsh-code-runtime-worker-thread` (isolated Node.js worker threads for TypeScript).
  - `dsh-experimental-code-runtime-python` (CPython subprocess for Python).

### D. Zero-Trust Hardware Sandboxing (`packages/sandbox/`)
- Sandboxing operates on 3 strict tiers (`sandbox-policy`):
  - `read-only`: Read-only filesystem and network isolation.
  - `workspace-write`: Write access strictly restricted to the bounded workspace root directory.
  - `danger-full-access`: Host execution requiring explicit approval escalation.
- Enforced at OS level:
  - Linux: Landlock LSM (`node-addon-landlock-run`) & bubblewrap (`bwrap`).
  - macOS: Seatbelt (`sandbox-exec` with dynamically generated Scheme policies).
  - Windows: Restricted token ACLs (`sandbox-windows-acl`).
  - Cloud: Remote container sandboxing via E2B integration (`packages/e2b`).

### E. Prefix Cache Engineering (DeepSeek-V3 / R1)
To achieve up to 99.93% KV-cache hit rate on reasoning models:
- Maintain complete immutability of system prompt prefixes across multi-turn sessions.
- Enforce deterministic serialization and key-ordering of tool schemas.
- Apply head+tail output trimming on large tool results before session compaction to preserve cache anchor boundaries.

### F. Twin Documentation Standard for Assimilation
Every SOTA assimilation must produce:
1. An in-repo technical specification at `docs/tech/sota_assimilation/SOTA_<NAME>_ASSIMILATION.md`.
2. An ADR note in the Obsidian Vault at `02_Architecture/ADR_<NUM>_<NAME>.md` with YAML frontmatter, MRH header, and rich `[[wikilinks]]`.

## 3. Implementation Pitfalls & Runtime Quirks
- **Python 3.14+ Coroutine Inspection (`inspect.iscoroutinefunction`)**: In Python 3.14 and above, calling `asyncio.iscoroutinefunction(fn)` raises a `DeprecationWarning` and is slated for removal in Python 3.16. All dynamic tool invocation wrappers (such as `around_execute` in `ToolGuardPipeline`) must use `inspect.iscoroutinefunction(fn)` from the standard `inspect` module.
- **Negative Guard Assertion Boundaries in Tests**: When writing test cases asserting security denial or pre-execution failure, always verify `output.error is not None` prior to `in output.error` checks to avoid `TypeError` when a stage returns a structured error object.
- **Symmetric Head-Tail Output Truncation**: When tool outputs exceed character limits, truncate symmetrically from head and tail with an explicit omission marker rather than hard truncating at the end, allowing the agent to observe both initial output context and final status/error summaries.
