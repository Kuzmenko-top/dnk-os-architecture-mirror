# --- DNK-MRH-HEADER ---
# mrh_id: "docs/operations/HERMES_V0_21_0_EXECUTION_GUIDE.md"
# purpose: "Operational Execution Guide & Automation Scripts Reference for Hermes v0.21.0 Promotion."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🚀 Hermes Agent v0.21.0 — Promotion Execution Guide

This guide provides the exact automated shell scripts and execution steps for transitioning Hermes Agent from **v0.20.5** to **v0.21.0** under the approved two-stage promotion protocol.

---

## 🛠️ Automated Scripts Inventory

All automation scripts are located in `scripts/system/` and follow strict fail-safe, zero-loss invariants:

1. **Pre-flight & Backup**:
   - Path: `scripts/system/hermes_v0_21_0_preflight_and_backup.sh`
   - Purpose: Validates production and candidate versions, calculates and writes SHA-256 baseline checksums to `docs/operations/HERMES_V0_21_0_BASELINE_HASHES.txt`, and creates non-destructive backups (`~/.hermes.backup.pre-0.21.0`, `core/hermes_agent.backup.pre-0.21.0`, `~/.local/bin/hermes.backup.pre-0.21.0`).

2. **Atomic Runtime Switch**:
   - Path: `scripts/system/hermes_v0_21_0_atomic_switch.sh`
   - Purpose: Gracefully stops background processes, performs atomic temporary symlink substitution for `~/.local/bin/hermes`, and asserts that the new active version contains `0.21.0`.

3. **Post-Deployment Health Check**:
   - Path: `scripts/system/hermes_v0_21_0_post_healthcheck.sh`
   - Purpose: Verifies active version, runs `hermes doctor`, lists sessions, and verifies database integrity against recorded baselines.

4. **Emergency Rollback**:
   - Path: `scripts/system/hermes_v0_21_0_rollback.sh`
   - Purpose: Restores launcher to v0.20.5 within SLA (< 30s, benchmarked at 1.139s). Run bare or pass `--with-state` to also restore the database backup.

---

## 📋 Step-by-Step Operator Runbook

To execute the deployment cleanly:

```bash
# 1. Run Pre-flight Checks and Create Backups
bash scripts/system/hermes_v0_21_0_preflight_and_backup.sh

# 2. Perform Atomic Runtime Switch
bash scripts/system/hermes_v0_21_0_atomic_switch.sh

# 3. Validate Health & State Integrity
bash scripts/system/hermes_v0_21_0_post_healthcheck.sh
```

### Emergency Rollback (if required):

```bash
# Instant launcher restore to v0.20.5:
bash scripts/system/hermes_v0_21_0_rollback.sh

# Instant launcher AND state database restore:
bash scripts/system/hermes_v0_21_0_rollback.sh --with-state
```

---

## ⏱️ 48-Hour Monitoring Window Invariants

- **Window**: 2026-09-03 19:45 EEST → 2026-09-05 19:45 EEST
- **Constraints**:
  - Zero destructive modifications (hard resets, DB purges) during the first 24 hours.
  - Strict human approval required for all Shopify, ERP, and Financial tool executions.
  - Immediate fail-closed rollback on security anomalies (TRG-01 to TRG-05).
