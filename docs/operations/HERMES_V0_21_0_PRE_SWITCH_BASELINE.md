# --- DNK-MRH-HEADER ---
# mrh_id: "docs/operations/HERMES_V0_21_0_PRE_SWITCH_BASELINE.md"
# purpose: "Pre-Switch Baseline, Backup Verification, and Step-1 Intent Confirmation for Hermes v0.21.0 Promotion."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 📋 Hermes Agent v0.21.0 — Pre-Switch Baseline & Verification

## 1. Metadata & Execution Context

```yaml
promotion_context:
  task_id: DNK-HUB-ARCH-002
  protocol: two_stage_promotion_v1
  stage: step_1_pre_switch_baseline
  current_production:
    version: v0.20.5
    runtime_path: core/hermes_agent
    launcher_path: ~/.local/bin/hermes
    state_path: ~/.hermes/state.db
    config_path: ~/.hermes/config.yaml
  staging_candidate:
    version: v0.21.0
    tag: v2026.8.31
    runtime_path: core/hermes_agent_staging
    launcher_candidate: core/hermes_agent_staging/.venv/bin/hermes
    verification_status: STAGED_AND_VERIFIED
  safety:
    rollback_sla_seconds: 1.139
    monitoring_window_hours: 48
    monitoring_window:
      start: "2026-09-03T19:45:00+03:00"
      end: "2026-09-05T19:45:00+03:00"
    destructive_actions_blocked: true
    shopify_erp_strict_approval: true
```

---

## 2. Production Baseline & Checksums Target

| Component | Target Location | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **Runtime Version** | `~/.local/bin/hermes --version` | String match `v0.20.5` | Baseline Defined |
| **State Database** | `~/.hermes/state.db` | SHA-256 Checksum | Snapshot Scheduled |
| **Configuration** | `~/.hermes/config.yaml` | SHA-256 Checksum | Snapshot Scheduled |
| **Launcher Symlink** | `~/.local/bin/hermes` | SHA-256 Checksum / readlink | Target Identified |
| **Candidate Runtime**| `core/hermes_agent_staging/.venv/bin/hermes` | String match `Hermes Agent v0.21.0 (2026.8.31)` | Certified |

---

## 3. Atomic Backup Specification

Before the symlink swap occurs, the following backups are established:

1. **Production State Backup**:
   - `cp -r ~/.hermes ~/.hermes.backup.pre-0.21.0`
   - Verification: `ls -lh ~/.hermes.backup.pre-0.21.0/state.db`
2. **Production Runtime Directory Backup**:
   - `cp -r core/hermes_agent core/hermes_agent.backup.pre-0.21.0`
   - Secondary archival: `core/hermes_versions/v0.20.5`
3. **Launcher Executable Backup**:
   - `cp ~/.local/bin/hermes ~/.local/bin/hermes.backup.pre-0.21.0`

---

## 4. Rollback SLA & Procedures

- **Target SLA**: `< 30 seconds`
- **Rehearsed Execution Time**: **`1.139 seconds`** (Measured on 2026-09-03)
- **Rollback Steps**:
  1. `pkill -f "hermes_agent"`
  2. `cp ~/.local/bin/hermes.backup.pre-0.21.0 ~/.local/bin/hermes`
  3. `cp -r ~/.hermes.backup.pre-0.21.0 ~/.hermes` (if state rollback needed)
  4. Verify: `~/.local/bin/hermes --version` and `shasum -a 256 ~/.hermes/state.db`

---

## 5. 48-Hour Monitoring Window Policy

- **Start**: `2026-09-03T19:45:00+03:00`
- **End**: `2026-09-05T19:45:00+03:00`
- **Rules**:
  1. No destructive operations (file wipes, hard resets, DB purges) during the first 24h.
  2. Strict human operator approval required for all Shopify, ERP, and Financial tool executions.
  3. Immediate fail-closed rollback on security anomalies (TRG-01 through TRG-05).
