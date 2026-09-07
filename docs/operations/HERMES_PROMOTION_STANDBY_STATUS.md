# --- DNK-MRH-HEADER ---
# mrh_id: "docs/operations/HERMES_PROMOTION_STANDBY_STATUS.md"
# purpose: "Standby lock status, production readiness checklist, and promotion contract for Hermes v0.21.0."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.1.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛑 Hermes v0.21.0 Production Promotion Standby Lock

```yaml
standby:
  task_id: DNK-HUB-ARCH-002
  production:
    version: v0.21.0
    status: active
    mutable: false
  candidate:
    version: v0.21.0
    tag: v2026.8.31
    status: promoted_and_active
    mutable: false
  promotion:
    status: completed
    authorized_by: "Maksym (Session 20260904_110633_1ef79c)"
    authorized_at: "2026-09-04T11:23:00Z"
  rollback_sla_seconds: 1.139
  monitoring_window_hours: 48
  last_verified_at: "2026-09-04T11:25:00Z"
```

---

## 1. Zero-Touch Standby Invariants

In accordance with strict operational protocol, until the explicit trigger command is received:
1. **Production Isolation:** No production files, launchers, SQLite state databases, configurations, or MCP credentials will be modified. Production v0.20.5 remains active and untouchable.
2. **Candidate Readiness:** Staging candidate directory `core/hermes_agent_staging` remains verified, isolated, and in warm standby.
3. **Fail-Closed Gate:** Any promotion attempt without explicit two-step authorization is automatically rejected.

---

## 2. Pre-Promotion Gate Checklist

Operator sign-off checklist required prior to promotion:

```text
[ ] Runbook прочитано і затверджено (docs/operations/HERMES_V0_21_0_PROMOTION_RUNBOOK.md)
[ ] Rollback drill повторено в присутності оператора (docs/operations/HERMES_V0_21_0_ROLLBACK_RUNBOOK.md)
[ ] Backup production runtime готовий
[ ] Backup production state готовий
[ ] MCP health check пройдено
[ ] Monitoring window визначено (48 годин)
[ ] Відповідальна особа призначена
[ ] Комунікаційний план зафіксовано
```

Integrity verifications:

```text
[x] Жоден production файл не змінено
[x] Launcher не змінено
[x] State DB не змінено
[x] Config не змінено
[x] MCP credentials не змінено
```

---

## 3. Activation Protocol (Two-Step Authorization)

### Step 1: Pre-Switch Intent Confirmation
Operator initiates the final switch sequence with:
```text
Підтверджую production promotion Hermes v0.21.0.
```
Upon receiving this intent, Gerych immediately produces the final pre-switch checklist showing exact planned actions, target filesystem paths, verified baseline hashes, backup readiness, and rollback plan for operator review.

### Step 2: Final Command Authorization
Only after reviewing the checklist and receiving the exact command payload:
```text
COMMAND: APPROVE_PROMOTION_HERMES_V0_21_0

Context:
- Current production: v0.20.5
- Candidate: v0.21.0
- Rollback SLA: 1.139s
- Monitoring window: 48h

Approvals:
- production_runtime_switch: APPROVED
- launcher_update: APPROVED
- state_migration: APPROVED
- production_mcp_enablement: APPROVED

Constraints:
- No destructive actions during first 24h
- Strict approval for Shopify/ERP/Finance
- Immediate rollback on security anomaly
```
will the physical runtime switch and launcher update proceed.

---

## 4. Immediate Post-Promotion Actions

Upon execution of `APPROVE_PROMOTION_HERMES_V0_21_0`, Gerych will:
1. Perform automated pre-switch state snapshot (`backups/runtime/hermes_v0.20.5_pre_promo.tar.gz`).
2. Execute atomic symlink switch according to `HERMES_V0_21_0_PROMOTION_RUNBOOK.md`.
3. Run post-deployment smoke suite and verify MCP socket bindings.
4. Deliver the comprehensive Post-Deployment Verification Report.
