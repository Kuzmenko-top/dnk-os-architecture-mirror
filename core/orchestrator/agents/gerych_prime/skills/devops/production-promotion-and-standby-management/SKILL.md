---
name: production-promotion-and-standby-management
description: Manage production standby locks and two-stage promotions.
version: 1.0.0
author: Gerych Core
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [devops, standby, promotion, release, deployment, runbook]
    category: devops
---

# Production Promotion & Standby Management

Enforce strict production standby locks, compile pre-promotion checklists, and execute reliable release promotion and rollback runbooks using a two-stage activation protocol.

## When to Use

Use this skill when:
- Preparing a production release or promotion candidate from a staged environment (e.g., v0.20.5 to v0.21.0).
- Establishing a "Standby Lock" or production freeze state where the active deployment remains untouched.
- Coordinating the transition from warm standby to full production switch with the operator.
- Managing pre-deployment and post-deployment validation checklists and rollback drills.

Do not use for simple development code changes or feature implementations that do not involve production-level promotions or structural runtime switches.

## Core Concepts

### 1. Standby Lock (Freeze State)
When a candidate is staged and verified but the switch is blocked, establish an explicit Standby Lock state:
- **Zero-Touch Invariant:** Absolutely no changes are made to production runtimes, launchers, state databases, active configs, or credentials.
- **Warm Standby:** Staging candidates remain isolated and in warm standby, ready for instant activation.
- **Verification Records:** Active verification and baseline hashes must be logged to a durable standby document (e.g., `docs/operations/HERMES_PROMOTION_STANDBY_STATUS.md`).

### 2. Two-Stage Promotion Protocol
To prevent accidental or half-cocked deployment switches, enforce a strict two-step verification dance with the operator:

```
┌──────────────────────────────────────────────┐
│                  Standby Lock                │
│ (Production frozen, Candidate warm staged)   │
└──────────────────────┬───────────────────────┘
                       │
                       │ Step 1: "Confirm Intent"
                       ▼
┌──────────────────────────────────────────────┐
│           Pre-Switch Checklist               │
│ (Verifies hashes, paths, backups, rollback)  │
└──────────────────────┬───────────────────────┘
                       │
                       │ Step 2: "Exact Command Approval"
                       ▼
┌──────────────────────────────────────────────┐
│           Execution of Promotion             │
│ (Automated backup -> symlink -> verification)│
└──────────────────────────────────────────────┘
```

#### Step 1: Intent Confirmation (The Alarm)
The operator signals the intent to promote, e.g., `"Підтверджую production promotion..."`.
The agent **must not** execute the promotion immediately. Instead, compile and present a comprehensive **Pre-Switch Checklist** displaying:
- Target and source filesystem paths (e.g., current production symlink, candidate staging path).
- Verified baseline hashes and status.
- Backup readiness of runtime files and state databases.
- Active rollback SLA and rollback runbook references.

#### Step 2: Exact Command Approval (The Key)
The operator reviews the checklist and provides the exact payload-guided structured approval command (e.g., `COMMAND: APPROVE_PROMOTION_...`).
Only upon receiving this exact parsed command is the physical promotion executed.

### 3. Beta Release Gate & Feature Moratorium
When preparing to transition from synthetic/local validation to a Beta release candidate:
- **Feature Moratorium:** Freeze all functional feature development. Prioritize stability, security boundaries, and operational limits.
- **7-Dimension Hardening Matrix:** Verify Real Adapters, Secrets Vault/Fail-Closed semantics, SSRF URL Ingestion Guard, Shopify Idempotency keys, End-to-End Observability (X-Correlation-ID), Operational Limits/DLQ, and Concurrency Stress (OCC).
- Detailed specifications and acceptance rules are documented in [`references/beta_release_gate_hardening.md`](references/beta_release_gate_hardening.md).

---

## Step-by-Step Procedure

### 1. Document the Standby State
When a release candidate is staging-ready but promotion is pending:
1. Create a `docs/operations/HERMES_PROMOTION_STANDBY_STATUS.md` file using `write_file`.
2. Include standard DNK-MRH-HEADER headers.
3. Add a structured YAML status block containing:
   - Task ID
   - Production version, status, and mutability.
   - Candidate version, tag, status, and mutability.
   - Promotion blocked status and the exact activation command required.
   - Rollback SLA and monitoring windows.
   - Timestamp of the last verification.
4. Stage and commit this file to the remote repository so the source of truth is tracked.

### 2. Prepare Runbooks
Ensure that two distinct, self-contained runbooks exist:
- **Promotion Runbook:** (`docs/operations/HERMES_<VERSION>_PROMOTION_RUNBOOK.md`) — documenting pre-promotion checks, automated backup targets, symlink switching steps, service restarts, and post-deployment validation.
- **Rollback Runbook:** (`docs/operations/HERMES_<VERSION>_ROLLBACK_RUNBOOK.md`) — documenting precise steps to restore production state within the designated SLA (e.g., restoring database state, resetting the symlink, restarting service, and confirming healthy recovery).

### 3. Handle the Activation Sequence
Upon receiving the Step 1 intent confirmation:
1. **Generate Pre-Switch Baseline Document:** Create a durable Markdown artifact (`docs/operations/HERMES_<VERSION>_PRE_SWITCH_BASELINE.md`) containing:
   - Metadata block: task ID, production version, candidate version and tag, runtime/launcher/state paths.
   - Production baseline checksum targets (version, state DB, config YAML, launcher binary, git commit).
   - Atomic backup specifications and target directory mappings.
   - Rollback SLA (< 30s target, rehearsed time) and step-by-step restoration commands.
   - 48-Hour monitoring window with concrete start and end timestamps (`Start: YYYY-MM-DDTHH:MM:SS`, `End: +48h`) and policy constraints (no destructive actions in first 24h, strict human approval on Shopify/ERP/Finance, immediate rollback on security/state anomaly).
2. **Respond with Pre-Switch Verification:** Address the operator's checkpoint questions (readiness, baseline/backup status, monitoring window confirmation).
3. **Present Structured Approval Command:** Provide the exact `COMMAND: APPROVE_PROMOTION_<VERSION>` payload block so the operator can review and issue the Step 2 authorization without syntax ambiguity.

Upon receiving the Step 2 approval payload:
Enforce the **3-Sequence Staged Execution with Checkpoint Reporting**:
1. **Sequence 1/3 (Pre-flight & Backup):**
   - Execute `scripts/system/<service>_<version>_preflight_and_backup.sh`.
   - Validate version strings, record SHA-256 baselines to `docs/operations/<SERVICE>_<VERSION>_BASELINE_HASHES.txt`, and generate state/runtime backups (`~/.hermes.backup.pre-<version>`, etc.).
   - Report the FULL output (stdout + stderr), backup locations, and checksums to the operator.
   - Pause for checkpoint confirmation before triggering Sequence 2.
2. **Sequence 2/3 (Atomic Runtime Switch):**
   - Execute `scripts/system/<service>_<version>_atomic_switch.sh`.
   - **Process Ancestor & Interactive TTY Protection:** When switching runtimes, ensure scripts do NOT kill the active agent session or other interactive user terminals. Filter process lists to exclude the active PID (`$$`), its parent shell (`$PPID`), its grandparent trees (all ancestors up to the terminal/IDE), and any interactive TTY-attached sessions. Only target headless background daemon processes (where `tty` is `?` or `??`).
   - Perform atomic temporary symlink substitution, and assert the active version matches the candidate string.
   - Report full output and confirm clean symlink state.
3. **Sequence 3/3 (Post-Deployment Health Check):**
   - Execute `scripts/system/<service>_<version>_post_healthcheck.sh`.
   - Run diagnostics (`doctor`, session listing), assert database integrity against pre-recorded baseline hashes, and verify test passes (`pnpm test`, `bash scripts/verify_all.sh`).
   - Compile and deliver the final Post-Deployment Verification Report.

---

## Pitfalls

- **Lumping Multi-Sequence Executions Into a Single Blind Step:** Running pre-flight, atomic switch, and post-healthcheck together without pausing for verification between Sequence 1/3 (backup validation) and Sequence 2/3 (runtime swap). The operator requires verifiable evidence of clean pre-flight and backup creation before authorizing the physical switch.
- **Single-Text Triggers:** Accepting a simple "Go ahead" or "Do it" for production promotion. Always require the full structured approval payload to prevent accidental switches.
- **CWD and Hub Root Disconnect:** Searching or writing files using local paths relative to a sub-service CWD instead of the global HUB_ROOT. When executing in a sub-service subdirectory (e.g. `core/hermes_agent`), global operational runbooks (`docs/operations/`) and orchestration scripts (`scripts/system/`) must be addressed using correct relative paths (e.g., `../../docs/operations/` and `../../scripts/system/`). Never assume the repository root is the current working directory.
- **Missing Backups:** Skipping the creation of a pre-switch state snapshot because "it's a simple symlink swap." Symlink swaps are fast, but state migrations can be irreversible without backups.
- **Ephemeral Responses for Baselines:** Emitting pre-switch baselines, checksum targets, and monitoring timestamps only in chat messages without saving a structured Markdown artifact (`docs/operations/HERMES_<VERSION>_PRE_SWITCH_BASELINE.md`). Always persist the baseline to disk for operational traceability.
- **Untracked Documentation:** Leaving the runbooks or standby status files uncommitted. Always push status documents to GitHub so the current deployment posture is visible to all agents and human co-workers.
- **No Test Validation:** Swapping the runtime without immediate automated socket-binding and integration checks.
- **Blind Process Termination / Active Session Suicide:** Blindly running `pkill -f "<name>"` or `pgrep | kill` in automatic switches or rollback scripts can immediately kill your own interactive agent session process or parallel developer terminals. Always implement TTY-based and process ancestor filtering inside your scripts.
- **CLI Subcommand Syntax Drift:** Older scripts may call deprecated or removed CLI subcommands (such as `list-sessions` which becomes `sessions list` in newer versions). Always review the target version's updated CLI contract during post-deployment health check planning.

---

## Verification Checklist

Before locking into standby, confirm:
- [ ] Standby status document exists at `docs/operations/HERMES_PROMOTION_STANDBY_STATUS.md`.
- [ ] Status document contains the correct YAML state definition.
- [ ] Both promotion and rollback runbooks exist and are committed.
- [ ] All production elements are verified untouched and isolated.
