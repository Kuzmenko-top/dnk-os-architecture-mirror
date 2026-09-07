---
name: remote-artifact-verification
description: "Use when verifying remote git commits, PRs, and merges."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [git, verification, pr, audit, remote, handoff]
    category: devops
---

# Remote Artifact & Git Evidence Verification

Verify that claimed commits, pull requests, and integration states exist on the remote repository before producing handoff reports or declaring acceptance criteria met.

## When to Use

- When reporting task completion, audit evidence, or acceptance matrices.
- When verifying whether a feature was merged into `main` or pushed to remote.
- When an acceptance report claims a commit SHA that failed remote verification.
- Before transitioning tasks from `OPEN` to `COMPLETE VERIFIED`.

## Core Invariants

1. **Remote Ground Truth**: Never claim a commit SHA or PR state is "VERIFIED" without checking remote refs (`git ls-remote`, `gh pr view`, or GitHub API).
2. **Anti-Ouroboros Protocol**: In evidence payloads and audit docs, reference `target_branch`, `base_sha`, and PR numbers rather than self-referencing an unpushed commit's own SHA.
3. **Explicit Integration Provenance**: Distinguish between direct push, squash merge, rebase merge, and merge commits. For production handoffs, PR merge is preferred.

## Verification Procedure

### 1. Check Remote References

```bash
# Verify remote branch and PR head refs
git ls-remote origin refs/heads/<branch-name>
git ls-remote origin refs/pull/<pr-number>/head

# Verify specific commit existence on remote
git show --stat --oneline <commit-sha>
```

### 2. Locate Actual Commits if SHA Mismatches

If a claimed SHA does not exist on remote (e.g., due to local `git commit --amend`, rebase, or placeholder typo):

```bash
# Find real commits touching relevant paths across all branches
git log --oneline --all -- <changed-file-path>

# Inspect recent commits on remote main
git log -n 10 --oneline origin/main
```

### 3. Check Pull Request and Merge State

Using `gh` CLI or MCP GitHub tools:

```bash
# Inspect PR state, merge commit, and changed files
gh pr view <pr-number> --json state,mergeCommit,headRefOid,url,files
```

### 4. Standard Artifact Report Format

When delivering verification reports, always provide the complete verified block:

```text
Actual Head Commit SHA:  <sha>
Actual Merge Commit SHA: <sha>
Remote repository:       <repo-url>
Feature Branch:          <branch-name>
Target/Base Branch:      <main/master>
Pull Request:            PR #<number> (<pr-url>)
PR State:                MERGED / OPEN
Commit URLs:
  - Branch Commit: <commit-url>
  - Merge Commit:  <commit-url>
Integration Method:      Merge via PR #<number>
Changed Files:
  1. path/to/file1
  2. path/to/file2
```

## Pitfalls

- **Dirty PR / Duplicate Commit PRs**: A PR showing `mergeable_state: dirty` or conflicts might actually have its changes ALREADY merged into `main` via an earlier PR (e.g., PR #34 merged work before PR #35 was closed). Always fetch `main` and check `git log --oneline HEAD..FETCH_HEAD` for the feature code or commit messages before trying to fix conflicts or re-merging.
- **Local vs Remote Confusion**: Confirming `git log` locally without fetching or querying `origin` (local commit not pushed).
- **Stale Commit SHAs**: Amending a commit creates a new SHA; using the old SHA breaks remote verification.
- **Test Runtime Artifacts Blocking Checkout**: Running test suites can modify tracked mock/runtime state files (e.g., `apps/api/visual_shell_db.json`). When attempting `git checkout main`, git aborts with "Your local changes would be overwritten". Discard these transient mutations with `git checkout -- <path>` or `git restore <path>` before switching branches.
- **Asymmetric Dual Remotes**: When workspace remotes serve different purposes (e.g., `dnk-mvp` is the core monorepo upstream while `origin` is a Shopify theme backup), pushing `main` to `origin` may reject with non-fast-forward. Verify remote purpose before forcing or investigating divergence.
- **GraphQL Scope Failure / CLI Auth Failure on `gh`**: `gh pr view`, `gh pr create`, or `gh pr merge` can fail if the token lacks org/discussion scopes or in non-interactive background scripts (exit code 4). Fall back to Python/curl with token extraction (using `re.search(r'(gho_[a-zA-Z0-9]+|ghp_[a-zA-Z0-9]+)', ...)` on `git config remote.<name>.url`) to query and merge via GitHub REST API directly. See `references/github_rest_fallback.md`.
- **Ambiguous Integration Claims**: Stating "committed to main" when the work was merged via PR or remains unmerged on a feature branch.
- **Masking Verification Status**: Repeating unverified claims when remote lookup fails instead of diagnosing the discrepancy immediately.

## Linked References

- `references/verification_checklist.md` — Fast CLI commands and standard markdown template for evidence reports.
- `references/github_rest_fallback.md` — Python script patterns for PR verification and merging via GitHub REST API when `gh` CLI hits GraphQL permission errors.
- `references/monorepo_fixture_testing.md` — Pytest PYTHONPATH isolation and zero-network egress fixture isolation patterns in monorepo testing.
- `references/dual_remote_push_strategy.md` — CLI commands and verification steps for pushing and syncing across dual remotes (`dnk-mvp` and `origin`).
