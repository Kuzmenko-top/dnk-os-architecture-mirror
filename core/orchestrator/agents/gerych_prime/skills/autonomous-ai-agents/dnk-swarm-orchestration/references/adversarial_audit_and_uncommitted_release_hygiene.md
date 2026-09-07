# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/adversarial_audit_and_uncommitted_release_hygiene.md"
# purpose: "Reference guide for Adversarial Security Reviews, in-memory module caching avoidance, and zero-uncommitted release gates."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ Adversarial Security Audits, In-Memory Caching & Clean Release Hygiene

## 1. The In-Memory Module Caching Trap (`sys.modules`)
When an agent or harness executes Python tools in a persistent environment, editing a file on disk (e.g. `core/security/adversarial_review.py`) does **not** update previously imported functions in `sys.modules`.
- **Symptom**: Calling `dnk_run_adversarial_review()` repeatedly raises the same `TypeError` or outdated logic even after the file on disk was successfully patched.
- **Root Cause**: The Python runtime reused the cached module instance from initial startup.
- **Fix**:
  1. Always run subprocess-isolated tools (`python3 -c "from ... import ...; ..."`) when running verifications.
  2. If running inside a persistent Python REPL/daemon, explicitly force reload:
     ```python
     import importlib, sys
     if "core.security.adversarial_review" in sys.modules:
         importlib.reload(sys.modules["core.security.adversarial_review"])
     ```

## 2. Scoped AST Scanning vs Vendor Monorepo Code Pollution
When running adversarial security scanners (`review_target()`):
- **Pitfall**: Passing broad top-level directories like `core/` causes AST scanners to parse vendor code, third-party submodules, or embedded agents (e.g. `core/hermes_agent`), generating tens of thousands of false positive warnings (`Unpinned dependency`, `Missing type annotations`, `Missing MRH`).
- **Resolution**:
  - Always pass an explicit, targeted list of modified feature components (e.g. `apps/api/routers/canvas_ws.py`, `core/runtime_events.py`).
  - Configure scanner exclusion rules to omit `core/hermes_agent`, `.venv`, and `node_modules`.

## 3. Uncommitted Working Tree PR Deadlock
- **Symptom**: `generate_evidence.py` reports `Warning: N uncommitted changes` and GitHub CLI fails with `GraphQL: No commits between main and feature/<branch> (createPullRequest)`.
- **Root Cause**: Developers or agents implement complete features in the working tree but fail to stage and commit them. The remote tracking branch has zero git diff against `main`, causing GitHub API to reject PR creation.
- **Protocol**:
  1. Run `git status -s` before evidence generation.
  2. Categorize files: update `.gitignore` for transient cache/telemetry artifacts (`accounting_log.json`, `*.rdb`, checkpoints).
  3. Commit domain changes atomically using Conventional Commits.
  4. Push to remote (`git push origin <branch>`).
  5. Run `python3 scripts/system/generate_evidence.py` on a 100% clean working tree.
