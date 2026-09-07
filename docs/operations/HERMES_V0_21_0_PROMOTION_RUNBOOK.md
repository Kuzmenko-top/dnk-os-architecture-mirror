# --- DNK-MRH-HEADER ---
# mrh_id: "docs_operations_hermes_v0_21_0_promotion_runbook"
# purpose: "Official Production Promotion Runbook for Hermes Agent v0.21.0."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-04"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🚀 Hermes Agent v0.21.0 Production Promotion Runbook

This document details the authorized, staged, and audited promotion procedure from **Hermes Agent v0.20.5** to **Hermes Agent v0.21.0** (promoted to production).

> ✅ **PROMOTION STATUS**: Execution is **COMPLETED**. Formal approvals granted by Maxim (`APPROVED_BY_MAKSYM`). Production v0.21.0 runtime and health checks verified.

---

## 📊 1. Promotion Metadata

```yaml
promotion:
  candidate: hermes-agent-v0.21.0
  current_production: hermes-agent-v0.21.0
  execution: COMPLETED
  updated_at: "2026-09-04"
  steps:
    - name: backup_production_runtime
    - name: backup_production_state
    - name: backup_launcher
    - name: deploy_staging_as_production
    - name: update_launcher
    - name: run_post_deployment_health_check
    - name: enable_production_mcp
    - name: start_monitoring_window
  approvals:
    - name: production_runtime_switch
      required: true
      status: APPROVED_BY_MAKSYM
    - name: launcher_update
      required: true
      status: APPROVED_BY_MAKSYM
    - name: state_migration
      required: true
      status: APPROVED_BY_MAKSYM
    - name: production_mcp_enablement
      required: true
      status: APPROVED_BY_MAKSYM
  rollback:
    trigger_conditions:
      - security_bypass
      - state_corruption
      - mcp_failure
      - accounting_mismatch
    procedure:
      - stop_runtime
      - restore_launcher
      - restore_state
      - verify_health
      - report
```

---

## 🛠️ 2. Detailed Promotion Steps

### Step 1: Backup Production Runtime
Freeze and duplicate the existing active v0.20.5 runtime directory to protect against compilation or environment damage.
```bash
# Define paths
PROD_DIR="core/hermes_agent"
BACKUP_DIR="core/hermes_versions/v0.20.5"

# Ensure the versions target directory exists
mkdir -p core/hermes_versions

# Perform the backup
cp -R "${PROD_DIR}" "${BACKUP_DIR}"
```

### Step 2: Backup Production State & Configuration
Copy the production SQLite database, event logs, and active configuration to a timestamped backup directory.
```bash
# Define paths
PROD_HOME="${HOME}/.hermes"
BACKUP_STATE_DIR="${PROD_HOME}_backup_$(date +%Y%m%d_%H%M%S)"

# Execute copy
mkdir -p "${BACKUP_STATE_DIR}"
cp "${PROD_HOME}/state.db" "${BACKUP_STATE_DIR}/state.db"
cp "${PROD_HOME}/config.yaml" "${BACKUP_STATE_DIR}/config.yaml"
```

### Step 3: Backup Launcher
Backup the current production executable symlink.
```bash
# Define paths
LAUNCHER_BIN="${HOME}/.local/bin/hermes"
BACKUP_LAUNCHER="${HOME}/.local/bin/hermes.v0.20.5.backup"

# Execute backup
cp "${LAUNCHER_BIN}" "${BACKUP_LAUNCHER}"
```

### Step 4: Deploy Staging as Production (Code Promotion)
Promote the certified v0.21.0 code from staging to the main production directory.
```bash
# Define paths
STAGING_DIR="core/hermes_agent_staging"
PROD_DIR="core/hermes_agent"

# Sync staging to prod directory (atomic copy over empty or cleaned target)
rm -rf "${PROD_DIR}"
cp -R "${STAGING_DIR}" "${PROD_DIR}"
```

### Step 5: Update Launcher (Atomic Symlink Switch)
Perform an atomic swap of the symlink to direct the CLI command `hermes` to the newly promoted v0.21.0 environment.
```bash
# Atomic symlink replacement on macOS/Linux using temporary symlink
ln -sfn "core/hermes_agent/.venv/bin/hermes" "${LAUNCHER_BIN}.tmp"
mv -f "${LAUNCHER_BIN}.tmp" "${LAUNCHER_BIN}"
```

### Step 6: Post-Deployment State Migration & Health Check
Execute database schema migration scripts and perform dry-run integrity verifications.
```bash
# Execute schema migrations if required (v0.21.0 database helper)
# verify schema version, test session resume, test accounting
.venv/bin/python -m unittest tests/staging/test_hermes_v0210_canary_integration.py
```

### Step 7: Enable Production MCP
Initialize and verify the secure Multi-Connection Protocol profiles with production configurations.
```yaml
mcp:
  servers:
    - github
    - google_drive
    - notion
    - gcal
    - finance
  health_check: passed
  production_mode: true
```
Ensure that:
1. MCP profiles are completely isolated and distinct from staging profiles.
2. Credentials and tokens remain untouched and securely retrieved from the system vault.
3. Establish socket and process health checks prior to active use.

### Step 8: Start 48-Hour Monitoring Window
Begin the passive-observability and read-only restriction window.
- **Duration**: 48 Hours.
- **Constraints**:
  - Strictly Read-Only access for all newly initialized MCP servers.
  - Zero destructive modifications (deletions, state clears, repository rewrites).
  - Explicit multi-step approval gates for any Shopify, ERP, or Financial mutations.
  - Verification of continuous background cron-jobs without overlapping.
  - High-frequency automated logging with security anomaly detection enabled.

---

## 🔐 3. Required Gate Approvals

| Approval Gate | Role | Required Status | Current Status |
| :--- | :--- | :--- | :--- |
| **Production Runtime Switch** | System Architect (Maxim) | **APPROVED** | `APPROVED_BY_MAKSYM` |
| **Launcher Update** | System Architect (Maxim) | **APPROVED** | `APPROVED_BY_MAKSYM` |
| **State Migration** | System Architect (Maxim) | **APPROVED** | `APPROVED_BY_MAKSYM` |
| **Production MCP Enablement** | System Architect (Maxim) | **APPROVED** | `APPROVED_BY_MAKSYM` |

---

## 🚨 4. Immediate Rollback Thresholds

If any of the following occur during the **48-Hour Monitoring Window**, the rollback procedure must be triggered **immediately** without delay:
1. **Security Bypass**: Any detection of raw keys/secrets inside the public model context, CLI logs, or unmasked database tables.
2. **State Corruption**: SQL exceptions, lock contention on `state.db`, or integrity mismatch during automatic checks.
3. **MCP Failure**: Repeated connection timeouts or unauthorized handshake rejection from core integration servers.
4. **Accounting Mismatch**: Any deviation from the token budget formula parent cost invariant.
