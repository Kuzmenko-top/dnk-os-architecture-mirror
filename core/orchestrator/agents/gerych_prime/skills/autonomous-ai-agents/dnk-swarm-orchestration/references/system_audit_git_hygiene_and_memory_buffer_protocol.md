# --- DNK-MRH-HEADER ---
# mrh_id: "references/system_audit_git_hygiene_and_memory_buffer_protocol.md"
# purpose: "Operational Protocol for Workspace Audits, L1 Memory Buffer Management, and Git Tree Hygiene."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# Workspace Audit, L1 Memory Buffer Management & Git Tree Hygiene Protocol (SYS-AUDIT-001)

## 1. Cognitive Memory (L1 Buffer) Overflow & Atomic Compression
- **Problem**: In Hermes Agent, `MEMORY.md` has a hard budget cap of 2,200 characters. When it reaches 100%+ (e.g. 2,284 chars), any subsequent single `memory(action='add')` call is hard-rejected by runtime overflow checks.
- **Root Cause**: Agent tends to store procedural task details, repetitive swarm role definitions, or multi-paragraph notes in L1 memory, which duplicates invariants already established in `SOUL.md` and `AGENTS.md`.
- **Solution Protocol**:
  1. Never attempt sequential add/remove operations when full.
  2. Use a single atomic batch call via `memory(target='memory', operations=[...])`.
  3. Evict duplicate definitions that live in system prompts (`SOUL.md`).
  4. Consolidate into concise bullet points targeting 30–40% budget (<1,000 characters).
  5. Retain high-signal operational invariants: workspace root, relative paths, virtualenv paths (`.venv/bin/python3`), triage rules (SOLO vs SWARM_PARALLEL), and self-healing tools.

## 2. Large Untracked & Modified Git Tree Segmentation (Anti-Monolith Invariant)
- **Problem**: After complex multi-slice sessions or long runs, the git working tree accumulates dozens to hundreds of untracked and modified files (e.g. 138 files across Docker, CI/CD, Canvas, Adapters, Telemetry). Attempting a single monolithic commit (`git commit -am "update"`) obscures regression origins and violates completion gates.
- **Segmentation Strategy**:
  1. **Triage Untracked Files**: Check `.gitignore` for build caches (e.g. `tsconfig.tsbuildinfo`, `.hermes/`, `.runtime_cache/`). Unstage tracked build caches via `git rm --cached <file>`.
  2. **Classify by Domain**:
     - `infra`: Docker, Dockerfiles, Compose, GitHub Workflows, health routers, deployment tests.
     - `components`: Core domain modules (e.g. `packages/archify/`, `core/guards/`, `core/orchestrator/`).
     - `canvas/ui`: Spatial Canvas nodes, Obsidian sync engine, visual shell components.
     - `assimilation/skills`: SOTA assimilation scripts, new skill reference docs, templates.
     - `system/telemetry`: Session checkpoints, runtime configs, performance logs.
  3. **Mandatory Pre-Commit Verification**: Run domain-specific pytest suites before EACH slice commit.
  4. **Commit & Seal**: Commit each slice cleanly with Conventional Commits before proceeding to the next.

## 3. Background Daemon Process Drift Trap
- **Problem**: Git working tree shows files (e.g. `docs/performance/metrics_staging_*.csv`) continuously modified or restaged immediately after a commit.
- **Cause**: Background processes (e.g. `collect_metrics.py`, headless telemetry loops) running in daemon threads continuously flush logs to tracked files.
- **Remediation**:
  1. Inspect running background jobs: `ps aux | grep -E "collect_metrics|monitor|poller"`.
  2. Terminate background pollers before attempting git state finalization: `kill <PIDs>`.
  3. Finalize the staging metrics log in a single atomic commit.
  4. Verify `git status` reports `nothing to commit, working tree clean`.

## 4. Python Virtualenv & Toolchain Priority
- **Problem**: Calling bare `python3` or `pytest` executes system Python (which may lack dependencies or differ in major/minor version, e.g. Python 3.12 vs 3.14 venv), leading to `ModuleNotFoundError`.
- **Enforcement**:
  1. Always invoke `./.venv/bin/python3` or `./.venv/bin/pytest`.
  2. In launch scripts (`scripts/system/gerych.sh`), ensure `.venv/bin` is prepended to `PATH` and project root + services are exported in `PYTHONPATH`:
     ```bash
     export PATH="$HUB_ROOT/.venv/bin:$PATH"
     export PYTHONPATH="$HUB_ROOT:$HUB_ROOT/services"
     ```

## 5. Automated Git Hygiene Guard & Untracked Test/Router Detection (GIT-HYGIENE-001)
- **Problem**: In rapid multi-slice development, agents frequently author new test suites (e.g. `tests/core/test_*.py`, `tests/verification/test_*.py`) or API routers (`apps/api/routers/*.py`), but only stage a subset of files. This leaves newly created tests and routers orphaned as untracked (`??`) files in git, hiding regressions from CI and breaking downstream builds.
- **Root Cause**: Relying on manual file staging without checking for unindexed test artifacts or router registration drift.
- **Enforcement Tool**: `scripts/system/git_hygiene_guard.py`
  - Parses `git status --porcelain` to detect any untracked (`??`) files in `tests/**`, `core/tests/**`, and `apps/api/routers/**`.
  - Verifies that any modified or added routers in `apps/api/routers/` are cleanly registered in `apps/api/main.py` and `apps/api/routers/__init__.py`.
  - Returns exit code `1` on violations, halting pre-commit gates until all tests and dependencies are explicitly staged.
- **Execution**:
  ```bash
  ./.venv/bin/python3 scripts/system/git_hygiene_guard.py
  ```

## 6. Markdown Planning & Notes Absolute Path Sanitization Invariant (PATH-HYGIENE-002)
- **Problem**: `bash scripts/verify_all.sh` (Step 2/4: Path Hygiene via `core/playbooks/scripts/enforce_relative_paths.py`) fails on documentation and plan files under `docs/plans/` or `docs/notes/` with `[Absolute Path Violation]` when paths contain `/Users/...`.
- **Root Cause**: The AST/regex linter scans all tracked repository files (including markdown) for patterns matching `/Users/[a-zA-Z0-9_\\.]+/`. Quoting local folder structures, error outputs, or external Obsidian vault locations (e.g. `/Users/<user>/Documents/DNK_HUB My Notes/`) triggers a hard gate rejection.
- **Enforcement**:
  1. Never write raw `/Users/<username>/` paths in markdown plans, task specifications, or handoff reports.
  2. Always use relative anchors (`./docs/notes/`), repository virtual variables (`<HUB_ROOT>/`), or explicit redaction (`~/[REDACTED]/Documents/...`).


