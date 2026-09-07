# --- DNK-MRH-HEADER ---
# mrh_id: "references/ephemeral_cwd_drift_and_swarm_hygiene.md"
# purpose: "Standard Operating Procedure for Terminal Persistent CWD Drift and Swarm Worker Scaffold Orphanage."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ Ephemeral CWD Drift & Swarm Scaffold Hygiene Protocol

## 1. Terminal Persistent CWD Drift Trap

### Symptom
Subsequent `read_file`, `search_files`, or `terminal` commands fail with `File not found` or path resolution mismatches after running an in-tree subshell command (e.g. `cd apps/web && npm run type-check`).

### Cause
In Hermes Agent, `terminal` executions share a persistent shell environment. Calling `cd <dir>` mutates the working directory for the remainder of the session unless explicitly reverted or executed in a subshell.

### Remediation Protocol
1. **Subshell Encapsulation (Preferred)**:
   ```bash
   # Run directory-sensitive commands inside an isolated subshell
   (cd apps/web && npm run type-check)
   ```
2. **CLI Directory Flag (Alternative)**:
   ```bash
   # Use tool-native directory flags without changing shell CWD
   npm --prefix apps/web run type-check
   pytest apps/api/tests
   ```
3. **Explicit Terminal Parameter**:
   Use `terminal(command="npm run type-check", workdir="/Users/.../apps/web")` instead of embedding `cd` in the command string.

---

## 2. Swarm Worker Scaffold Orphanage & Git Hygiene Blockers

### Symptom
`bash scripts/verify_all.sh` or `scripts/system/git_hygiene_guard.py` fails with:
```text
❌ GIT HYGIENE ERROR: Found untracked test/router files! You must git add them:
  - apps/api/routers/rag.py
```

### Cause
Specialized swarm domain workers (e.g., `dnk_dev_fullstack`, `gerych_builder`) scaffold preliminary endpoint routers, schemas, or test files during exploratory or partial slice execution. When a worker finishes without staging or registering the router into `apps/api/main.py`, the file remains untracked and triggers fail-closed pre-commit hygiene gates.

### Remediation Protocol
Whenever swarm domain workers create or scaffold files:
1. **Register & Stage (Integration Path)**:
   - Wire the router into the main application entrypoint (`apps/api/main.py`).
   - Add matching schema and test definitions.
   - Stage the files immediately: `git add apps/api/routers/<module>.py apps/api/schemas/<module>.py`.
2. **Prune Stale Stubs (Discard Path)**:
   - If the slice is aborted or deemed out of scope, remove the untracked stubs before invoking quality gates:
     `rm -rf apps/api/routers/stub.py`.
3. **Pre-Verification Tree Inspection**:
   - Always run `python3 scripts/system/git_hygiene_guard.py` before executing `verify_all.sh` to catch untracked domain files early.
