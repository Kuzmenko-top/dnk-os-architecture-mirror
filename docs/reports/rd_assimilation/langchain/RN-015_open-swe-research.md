# --- DNK-MRH-HEADER ---
# mrh_id: "docs/reports/rd_assimilation/langchain/RN-015_open-swe-research.md"
# purpose: "SOTA Research and Pattern Extraction for langchain-ai/open-swe"
# author: "DNK-e.com Maksym"
# license: "MIT"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-14"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Research: open-swe Framework Assimilation (RN-015)

In-depth technical research and architectural analysis of `langchain-ai/open-swe` (10.5k+ stars, MIT license) for assimilation into DNK OS Core software engineering agents.

## 📋 Research Metadata
- **Donor Repository:** `langchain-ai/open-swe`
- **Task ID:** `DNK-ASSIM-015`
- **Domain:** `langchain`
- **License:** MIT
- **Key Modules Analyzed:**
  - `agent/graphs/*.py` — LangGraph state machines & execution graphs
  - `agent/dispatch.py` — Task routing & context packing
  - `agent/scheduler.py` — Async multi-step task scheduling
  - `agent/prompt.py` — Structured prompt primitives
  - `agent/runtime/` — Containerized sandboxed runtimes

---

## 🔍 Core Findings & Architectural Insights

### 1. LangGraph State Machines (`agent/graphs/*.py`)
`open-swe` uses specialized LangGraph state graphs representing closed software engineering loops:
- **Repo Analysis State:** Scans codebase, parses AST signatures, constructs context graphs.
- **Planner Node:** Formulates candidate edit plans and test scenarios.
- **Executor & Patch Node:** Generates file modifications using unified diffs or targeted block replacements.
- **Verifier Node:** Executes test suites in an isolated runtime and triggers self-healing retries upon failure.

### 2. Event-Driven Dispatcher (`agent/dispatch.py`)
- Dispatches user issues / GitHub PR tasks to target agent workflows.
- Packs repository context (relevant files, AST trees, git status) into compact context windows.
- Filters irrelevant files to optimize context consumption.

### 3. Async Task Scheduler (`agent/scheduler.py`)
- Handles background execution of long-running coding jobs.
- Implements concurrency throttles, queue prioritization, and job status event streaming.

### 4. Structured Prompts & Diff Engineering (`agent/prompt.py`)
- Standardized prompt schemas enforcing strict diff structures (`*** Begin Patch ... *** End Patch`).
- Error context feedback loops: feeds test execution traces directly back into the prompt for iterative fixing.

### 5. Sandboxed Runtime Execution (`agent/runtime/`)
- Isolates untrusted code execution inside containerized Docker runtimes.
- Prevents host filesystem pollution and enforces resource bounds (CPU, memory, timeout).

---

## 🛡️ Alignment with DNK OS Standards
- Directly aligns with DNK OS `DNKLangGraphAdapter` and `DNKLangChainAdapter`.
- Enforces Docker-only runtime execution matching DNK OS zero host pollution mandate.
