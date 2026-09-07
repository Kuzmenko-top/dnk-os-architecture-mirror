# GitHub MCP & CI/CD Fast-Path and Fail-Closed Pre-PR Gate Protocol (FAST-PR-001)

## Context & Objectives
During autonomous agent execution, attempts to create or update Pull Requests without verified quality gate status or with uncommitted/unverified mutations lead to broken builds, duplicate PR spam, 404/422 repository errors, and CI resource waste.
This protocol governs the **GitHub MCP & REST Fast-Path Engine**, the **Fail-Closed Pre-PR Hook Gate**, and **SessionSentinel CI/CD telemetry**.

## 1. Fast-Path Architecture & Idempotent Sync
The engine is implemented in `core/orchestrator/github_fast_path.py`:
- **Dynamic Repository Resolution (`resolve_repo_slug`)**:
  - Dynamically extracts owner/repo from git remotes (`origin`, `dnk-mvp`) or environment overrides (`GITHUB_REPOSITORY`).
  - Fallback to canonical repository slug (`Kuzmenko-top/DNK-OS` / `m-craft.top`).
  - Completely prevents 404 errors caused by hardcoded stale repository names.
- **Idempotent PR Sync (`fast_create_or_update_pr`)**:
  - Queries GitHub API in <1s for existing open PRs on the current branch (`fast_get_pull_request`).
  - If a PR already exists: updates its title, description, and Master Quality Gate badge via REST PATCH (`/pulls/{pr_number}`) without throwing duplication errors.
  - If no PR exists: creates the PR via REST POST (`/pulls`).
- **Master Quality Gate Badge**:
  - Auto-formats and injects a markdown badge containing: Task ID, Git commit SHA, Master Quality Gate status (100% Green Certified), MRH header compliance, and protocol version.

## 2. Fail-Closed Pre-PR Hook (`scripts/system/hermes_pre_tool_hook.py`)
- **Interception Scope**:
  - Native MCP tool calls: `mcp__github__create_pull_request` and `tool_call(name="mcp__github__create_pull_request")`.
  - Shell commands: `gh pr create`, `gh pr edit`, and raw `gh api .../pulls`.
- **Pre-PR Verification Invariants**:
  1. **Fresh Evidence Required**: Scans `docs/audit/*-evidence.json` for a report matching `status == "COMPLETED"`, `master_quality_gate == "PASSED"`, and created within the last 15 minutes (`file_age <= 900s`).
  2. **Zero Unverified Mutations**: Checks that `unverified_mutations` in the pre-tool tracker is empty (all modified files have passed tests).
  3. **Immediate Rejection**: If either condition fails, the tool call is blocked fail-closed with:
     ```json
     {"decision": "deny", "reason": "FAIL-CLOSED: Pull Request creation blocked. No fresh Master Quality Gate evidence found in docs/audit/ (or evidence is older than 15 minutes). You MUST run 'python3 scripts/system/generate_evidence.py --task <TASK_ID> --title \"...\" --components <FILES...>' first."}
     ```
  4. **Emergency Bypass**: Supported via `DNK_BYPASS_PR_GATE=1` environment variable.

## 3. SessionSentinel CI/CD Telemetry (`core/orchestrator/session_sentinel.py`)
- New anomaly category: `AnomalyCategory.CI_CD_VIOLATION`.
- Sentinel tracks `had_pr_creation_attempt`.
- If an agent attempted a PR creation or edit without running verification or while holding unverified mutations, Sentinel records an anomaly:
  - `code`: `CI_CD_GATE_BREACH`
  - `description`: `Unverified Pull Request Attempt (CI/CD Quality Gate Breach): Agent attempted to create/edit a PR without executing tests or while holding unverified file mutations.`
  - `severity`: `HIGH`

## 4. Hook Execution Testing Invariant
When writing integration tests that invoke `scripts/system/hermes_pre_tool_hook.py` via subprocess stdin:
- The hook expects `"hook_event_name": "pre_tool_call"` in the payload dictionary.
- If `hook_event_name != "pre_tool_call"`, the hook exits early returning `{}` without evaluating tool guards.
- Always include `"hook_event_name": "pre_tool_call"` in test fixtures and synthetic event payloads.
