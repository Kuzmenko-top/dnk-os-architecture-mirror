# Post-Assimilation Cleanup & Monorepo Bloat Audit Protocol

## 1. Context & Pitfall
During staged assimilation of large embedded runtimes (e.g. upgrading Hermes Agent or major upstream frameworks), intermediate staging directories (`*_staging`, `*.backup.*`, `*_versions`) are often created in tree. If left unpruned after canary promotion:
1. They balloon repository file counts by tens of thousands (e.g., >77,000 extra files, >1.3 GB).
2. AST scanners and preflight compile checks (`scripts/system/fast_compile_check.py`, `verify_all.sh`) traverse these backup trees, causing severe compilation timeouts (>180s).
3. Linters, IDE indexers, and git operations suffer massive latency.

## 2. Mandatory Post-Promotion Decommission Checklist
Immediately after promoting a staged runtime to production:
1. **Archive/Quarantine**: Move staging and pre-upgrade backup directories completely out of the repository workspace (or into an ignored archive outside `core/`).
2. **Exclude in Preflights**: Ensure any temporary directories are explicitly registered in `IGNORE_DIRS` in `scripts/system/fast_compile_check.py`.
3. **Verify Git Hygiene**: Run `git status -u` to confirm zero untracked staging or backup trees remain in `core/`.

## 3. Runtime State Isolation Invariant
Agent profile and personality definitions (`core/orchestrator/agents/<agent_name>/`) must strictly remain pure specification cards:
- Allowed files: `SOUL.md`, `agent_card.yaml`, `config.yaml`, `memories/MEMORY.md`, and skills.
- Strictly forbidden in agent directories: `state.db`, `*.sqlite*`, `checkpoints/`, `lsp/`, `bin/`, `cache/`, `*.log`.
- Runtime execution state must be directed to `~/.hermes/`, `artifacts/`, or isolated temporary workspace paths.

## 4. Accidental Recursion & Empty Directory Sanitation
- Check for accidental self-nested directories (e.g., `core/core/`) caused by incorrect relative `mkdir` commands during tool execution.
- Prune abandoned empty directory trees (e.g., placeholder `workers/` or `media/` directories with 0 files).

## 5. Optional Dependency Resilience in Core Tests
When adding accounting or telemetry engines to core:
- Never hard-import optional monitoring libraries (e.g. `from langfuse import Langfuse`) at the module root of core engines.
- Always guard with:
  ```python
  try:
      from langfuse import Langfuse
  except ImportError:
      Langfuse = None
  ```
- This prevents `ModuleNotFoundError` during test collection across the core test suite.
