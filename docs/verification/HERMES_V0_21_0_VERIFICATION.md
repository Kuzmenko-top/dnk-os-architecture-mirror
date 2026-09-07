# --- DNK-MRH-HEADER ---
# mrh_id: "docs_verification_hermes_v0_21_0_verification"
# purpose: "Verification test suite and criteria for Hermes Agent v0.21.0 Staged Assimilation into DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

# 🧪 Hermes Agent v0.21.0 Staged Verification Specification

This document defines the automated and manual verification checks that must pass before any consideration of runtime promotion to production.

---

## 1. Automated Smoke & Unit Verification Matrix

| Test ID | Target Capability | Verification Procedure | Expected Outcome | Status |
|---|---|---|---|---|
| `VERIF-01` | **Version & Doctor** | Execute `hermes --version` and `hermes doctor` on staging binary | Version `v0.21.0` reported, all runtime subsystems green | 🟡 Pending Staging |
| `VERIF-02` | **Bot Mode Roster** | Initialize `core/hermes_agent_staging` with default profile | Roster loads without schema errors; handles resolved | 🟡 Pending Staging |
| `VERIF-03` | **Peer Event Ingestion**| Send peer message between two test profiles; inspect event log | Message delivered and captured by DNK event adapter | 🟡 Pending Staging |
| `VERIF-04` | **Cron Memory Scope** | Run recurring job with `continuity=true` across 2 synthetic ticks | Tick 2 receives Tick 1 delta; zero writes to L3 SCONES | 🟡 Pending Staging |
| `VERIF-05` | **Live Child Steering** | Spawn child task via `delegate_task`; issue `action='steer'` | Child receives redirected directive mid-run | 🟡 Pending Staging |
| `VERIF-06` | **Structured Output** | Invoke child task requiring strict JSON Schema output | Output strictly validates against schema; errors trigger retry | 🟡 Pending Staging |
| `VERIF-07` | **Security Approval Gate**| Attempt write to `AGENTS.md` without bypass flag | Write is halted; user approval prompt generated | 🟡 Pending Staging |
| `VERIF-08` | **Browser Dev Preview** | Launch browser automation against local preview server | Navigation lands on preview; zero production network calls | 🟡 Pending Staging |
| `VERIF-09` | **State DB Integrity** | Execute test session on clone of `~/.hermes/state.db` | Schema migration succeeds with zero data corruption | 🟡 Pending Staging |
| `VERIF-10` | **Rollback Drill** | Execute Phase F rollback commands in staging environment | System returns to pristine v0.20.5 state within 30 seconds | 🟡 Pending Staging |

---

## 2. Definition of Done Checklist

```text
[x] Upstream v0.21.0 confirmed via GitHub tag (v2026.8.31) and release notes
[x] Local runtime confirmed as embedded unmanaged fork with custom DNK modifications
[x] Blind rsync strictly prohibited and documented
[x] Staged upgrade runbook authored and reviewed (Phase A - F)
[x] DNK-Hermes architectural boundaries and permission matrix established
[x] Hermes event contract defined
[ ] Staging environment (core/hermes_agent_staging) created
[ ] Local patches cleanly ported to staging
[ ] All 10 verification test cases executed and passed
[ ] Rollback drill successfully verified
[ ] Formal verification report signed off by Maxim
```
