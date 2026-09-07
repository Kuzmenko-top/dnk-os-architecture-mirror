# --- DNK-MRH-HEADER ---
# mrh_id: "skills/autonomous-ai-agents/dnk-swarm-orchestration/references/critical_security_guards_and_evidence_verification_protocol.md"
# purpose: "Security invariants, Shell-Injection-Free execution, Epistemic Evidence Validation, and Path-Traversal-Proof Risk Gate Snapshots."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ Critical Security Guards & Evidence Verification Protocol (SEC-GATE-001)

## 1. Zero Shell-Injection Invariant (`shell=False`)
- **Root Problem**: Calling `subprocess.run(cmd, shell=True)` exposes execution to command injection, arbitrary expansion, and unescaped payload execution.
- **Enforced Solution**:
  1. ALL execution calls MUST use `shell=False`.
  2. If commands originate from string representations, parse them strictly via `shlex.split(cmd)`.
  3. Commands must be passed as lists of arguments: `subprocess.run(["ls", "-la", path], ...)`.
  4. Path commands must resolve through dynamic fallbacks (e.g. `./.venv/bin/pytest` -> `shutil.which("pytest")` -> `["uv", "run", "pytest"]`).

## 2. Epistemic Evidence Validation Protocol (`verify_evidence`)
- **Root Problem**: Evidence validation returning `verified: True` merely because an execution ran, without evaluating process return codes or probe contracts.
- **Enforced Solution**:
  1. If `exit_code != 0`, `verified` MUST be `False` (unless probe explicitly expects failure).
  2. Validation rules against `expected` specs:
     - `exit_code_0` -> requires `exit_code == 0`.
     - `NON_EMPTY` -> requires output string to be non-empty after stripping whitespace.
     - `> N` / `>= N` / `< N` / `<= N` -> parse integer counts from output and evaluate comparison.
     - `contains:<str>` -> requires `<str>` in output.
     - `regex:<pattern>` -> matches regex against output.
  3. Discrepancy reporting: when `verified == False`, manifest must store explicit failure reasons in `error` or `failure_reason`.

## 3. Path Traversal & Symlink Exploit Defense (Risk Gate Snapshots)
- **Root Problem**: Restoring or backing up files using relative paths or following symlinks allows attackers or malicious scripts to overwrite files outside repository root or point to `/etc/passwd`.
- **Enforced Solution**:
  1. **Symlink Rejection**: Always check `src.is_symlink()`. Symlinks MUST NEVER be copied or traversed into backup archives; they must be skipped and logged in `skipped_symlinks`.
  2. **Path Traversal Guard**:
     - Normalize paths using `.resolve()`.
     - Ensure `resolved_path.relative_to(root_dir)`. Any path attempting `../` escape outside `root_dir` MUST raise `SecurityException` / `ValueError` and be refused.
  3. **Collision-Proof Backup Hashing**:
     - Do not save flat file names (e.g. two `main.py` in different folders colliding).
     - Compute `hash = hashlib.sha256(str(rel_path).encode()).hexdigest()[:8]`.
     - Store file as `{hash}_{filename}`.
     - Maintain an authoritative `snapshot_manifest.json` mapping original relative paths to stored hash filenames and file metadata.
  4. **Safe Automated Snapshot Cleanup**:
     - `cleanup_old_snapshots(snapshot_dir, max_age_days=7)` inspects manifest timestamp or directory `stat().st_mtime` and purges expired snapshots safely.

## 4. Honest Offline R&D Fallback (Zero Hallucination Metrics)
- **Root Problem**: External API failures (e.g. GitHub rate limiting 403 or missing `gh` CLI) falling back to hardcoded mock numbers (like 1000 stars or fake commit dates).
- **Enforced Solution**:
  1. Always verify binary presence via `shutil.which("gh")`.
  2. Detect HTTP 403 Rate Limits explicitly and flag `rate_limited: True`.
  3. On fallback, report honest zero-state: `stars: 0`, `last_commit: "UNKNOWN"`, `fallback_used: True`.
  4. License classification: unknown or unparsed licenses must default to `CLEAN_ROOM` (Track 2) until proven permissive.
