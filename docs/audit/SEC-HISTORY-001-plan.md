# --- DNK-MRH-HEADER ---
# mrh_id: "docs/audit/SEC-HISTORY-001-plan.md"
# purpose: "Controlled Git History Sanitation & Credential Scrubbing Plan with Safety Invariants."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Draft - Awaiting Owner Authorization"
# version: "1.1.0"
# updated_at: "2026-08-30"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ SEC-HISTORY-001: Comprehensive Git History Sanitation Plan

> **Status:** Pending Owner Authorization & Revocation Confirmation.  
> **Execution Rule:** DO NOT execute history rewrite, force push, branch deletion, or submodule ref rewrite without owner’s explicit approval.

---

## 1. Context & Scope
- **Target Leaked Credential:** GitHub Personal Access Token (Classic).
- **Exposure Target:** 3 historical commits (`0d1d71cc97`, `0e84bb4103`, `ed83177377`) in launch scripts (`gerych.sh`, `gerych_swarm.sh`, `preflight_sync.py`).
- **Tooling:** `git-filter-repo` (Python-based, official Git recommended tool).

---

## 2. Mandatory Pre-Flight Safeguards & Invariants

Before any `git-filter-repo` execution, the following verification checklist MUST be satisfied:

1. **Repository Visibility Confirmation:** Verify repository private/public status and collaborator access permissions.
2. **Branch & PR Mapping:** Identify all protected branches (`main`) and active feature/PR branches (`feature/dnk-studio-arch-001`, etc.).
3. **Submodule & Deployment Dependency Audit:** Identify linked submodule commits (specifically `DNK_HUB` sandbox/submodule) and deployment references to ensure no dangling SHA pointers break downstream builds.
4. **Maintenance Window & Write Freeze:** Announce write freeze; pause automated cron schedulers and active agent runners.
5. **Encrypted Off-Platform Backup:** Create an encrypted off-platform snapshot bundle of all repository refs prior to any mutation.
6. **Dry-Run on Mirror Clone:** Test the full rewrite procedure on an isolated mirror clone to verify commit tree integrity and clean diffs.
7. **Pre-Push Ref Review:** Inspect rewritten refs (`git log`, `git show`, `git fsck`) before requesting owner sign-off for force-push.
8. **Owner Explicit Authorization:** Require explicit sign-off from Maxim before executing any remote force-push (`git push --force`).
9. **CI Environment Reset:** Invalidate all CI build caches and perform fresh re-clones on production CI runners.
10. **Mandatory Credential Revocation:** Ensure old credential is fully revoked in GitHub console regardless of history cleaning status.

---

## 3. Step-by-Step Execution Procedure (Upon Authorization)

### Step 1: Encrypted Backup & Snapshot
```bash
# Create complete immutable bundle of current repository state
git bundle create dnk_hub_pre_history_rewrite.bundle --all
```

### Step 2: Expressions File Preparation
Create secure non-tracked replacement file `replace_expressions.txt`:
```text
# Exact pattern replacement (loaded via secure environment / isolated file)
regex:gho_[A-Za-z0-9_]{30,}==>[REDACTED_HISTORICAL_TOKEN]
```

### Step 3: Run `git-filter-repo` on Mirror Clone First
```bash
# Verify on isolated mirror clone before production repository
git filter-repo --replace-text replace_expressions.txt --force
```

### Step 4: Verification & Integrity Checks
```bash
git fsck --full
python3 scripts/system/secret_scanner.py --mode history --all-refs
git log --all -S 'gho_' --oneline  # Must return 0 lines
```

### Step 5: Submodule & Deployment SHA Reconciliation
```bash
# Re-align submodule commit pointers (e.g. DNK OS) to matching rewritten SHAs
git submodule update --init --recursive
```

### Step 6: Coordinated Remote Sync (Owner Supervised)
```bash
# Coordinated force-push across active branches (Requires Owner Approval)
git push origin main --force
git push origin --all --force
```

### Step 7: Post-Sanitation Actions
1. Invalidate CI build caches & artifacts on GitHub Actions.
2. Direct all collaborators / clones to re-clone or hard reset on new SHA tree.
3. Verify remote repository health via GitHub UI.
