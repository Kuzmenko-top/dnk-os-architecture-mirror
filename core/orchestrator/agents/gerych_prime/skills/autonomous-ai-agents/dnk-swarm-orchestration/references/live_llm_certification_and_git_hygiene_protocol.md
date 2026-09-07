# --- DNK-MRH-HEADER ---
# mrh_id: "references/live_llm_certification_and_git_hygiene_protocol.md"
# purpose: "Standard Operating Procedure for Git Working Tree Hygiene, Tool CWD Resolution, and Live LLM Certification Gates."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ Live LLM Certification & Git Tree Hygiene Protocol

## 1. Context & Rationale
During phase certification and live LLM testing gates (such as `001E-F-LIVE`), declaring completion when production code is modified in memory or uncommitted leads to severe defects:
- Cache hit/miss tests and integration tests can pass against old cached builds or outdated module versions while production code does not match.
- Evidence JSON (`*-evidence.json`) and Handoff Markdown (`*_handoff.md`) record a commit hash that does not include the essential changes, rendering the audit trail invalid.
- File-mutation verifiers fail when tool calls fail silently due to nested working directory mismatches.

## 2. Invariants & Pre-Flight Gate

### Invariant A: Clean Working Tree Verification Before Evidence Generation
Before executing `generate_evidence.py` or declaring a phase "Completed":
```bash
# Verify working tree is completely committed
git status --short packages/<target_package>
# Must output empty string / 0 lines
```
If any files are modified (`M`) or untracked (`??`), you MUST stage, commit, and push them prior to generating evidence:
```bash
git add packages/<target_package>
git commit -m "feat(<scope>): <description of actual changes>"
git push origin <branch>
```

### Invariant B: Tool CWD & Relative Path Resolution
Hermes may run with an active process CWD set to a nested directory (e.g. `core/hermes_agent`), whereas monorepo scripts and tools expect paths relative to the monorepo root (`$HUB_ROOT`).
- When calling `patch` or `read_file`, always verify the effective CWD.
- If CWD is `core/hermes_agent`, paths targeting packages must be prefixed with `../../` (e.g. `../../packages/video-audit-core/package.json`).
- If a tool reports `Failed to read file`, immediately check `pwd` and verify path existence before assuming file mutation succeeded.

## 3. Real-World Troubleshooting & False Positive Diagnosis

### 5-Step Diagnostic Protocol for File-Mutation Verifier Warnings
When the verifier reports:
```text
⚠️ File-mutation verifier: 1 file(s) were NOT modified this turn despite any wording above
   • packages/video-audit-core/package.json — [patch] Failed to read file
```
Run this exact diagnostic sequence immediately:
```bash
# 1. Check file existence
ls -la packages/video-audit-core/package.json

# 2. Check directory symlinks
ls -la packages/ | grep video

# 3. Check git working tree status
git status

# 4. Verify file content for expected changes
cat packages/video-audit-core/package.json | grep "test:live"

# 5. Verify git commit history and diff stats
git log --oneline -5
git show HEAD --stat
```

### Decision Matrix: Scenario A vs Scenario B

| Condition | Verdict | Action |
|---|---|---|
| **Scenario A (False Positive)**:<br>• `git status` shows clean tree<br>• File exists and contains expected changes<br>• Git log confirms changes are committed & pushed | **False positive** due to tool process CWD mismatch (`core/hermes_agent` vs `$HUB_ROOT`) or session read state. | Ignore mutation verifier warning. Proceed with quality gate verification and declare production readiness. |
| **Scenario B (Real Issue)**:<br>• File is missing, or<br>• `git status` shows untracked/modified changes, or<br>• Commit does not include changes | **Real mutation defect**. | 1. Stage: `git add <file>`<br>2. Commit: `git commit -m "..."`<br>3. Push: `git push origin <branch>`<br>4. Re-run tests and re-generate Evidence. |

### Invariant C: Explicit Live Test Script in `package.json`
Every package with live LLM or external provider integrations must declare an explicit npm/pnpm script:
```json
{
  "scripts": {
    "test": "vitest run",
    "test:live": "vitest run tests/adaptation/adaptation-pipeline.test.ts"
  }
}
```
Run both offline and live suites under SpendGuard controls:
```bash
# 1. Standard offline unit/integration test suite
pnpm test

# 2. Live LLM suite with environment flag
RUN_LIVE_LLM_TESTS=1 pnpm test:live
```

### Invariant D: Evidence JSON Generation Gate
Generate signed Evidence JSON only AFTER:
1. Target files are fully committed to git (`git status` clean).
2. Offline test suite passes 100% Green (`pnpm test`).
3. Live test suite passes 100% Green (`RUN_LIVE_LLM_TESTS=1 pnpm test:live`).
4. Master verification script passes 100% Green (`bash scripts/verify_all.sh`).

Then run:
```bash
python3 scripts/system/generate_evidence.py --task <TASK_ID> --title "<TITLE>" --components <FILES...>
```
