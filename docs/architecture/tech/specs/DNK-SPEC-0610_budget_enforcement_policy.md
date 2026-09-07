# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-SPEC-0610_budget_enforcement_policy.md"
# purpose: "Enforce canonical budget limit policy for DNK OS LLM Gateway execution"
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

# 💸 DNK OS LLM GATEWAY CANONICAL BUDGET ENFORCEMENT POLICY

This document defines the strict, multi-tiered monetary limits and emergency thresholds for live provider calls inside the **DNK OS Model Gateway** (effective starting Whitelisted Internal Rollout).

## 📊 Tiered Budget Limits (USD)

| Limit Type | Value (USD) | Scope / Context | Action on Breach |
|---|---|---|---|
| **Per-Request Limit** | `$0.05` | Single LLM Gateway execution | Fail-Closed / Throw `BudgetExceededException` |
| **Daily Workspace Limit** | `$1.00` | Single workspace execution over 24h | Safe Degradation to Shadow Mode |
| **Monthly Project Limit** | `$10.00` | Single Project boundary per month | Safe Degradation to Shadow Mode |
| **Global Emergency Limit** | `$50.00` | Entire system infrastructure per month | Safe Degradation (All Workspaces to Shadow) |

---

## 🛡️ Budget Enforcement Safeguards

1. **Pre-Call Verification**: Before any model call is initiated, the `BudgetManager` checks the current spent tokens and calculates the expected cost. If `current_spent + expected_call_cost > limit`, the call is immediately blocked.
2. **Fail-Closed Strategy**: Under no circumstances can a model call proceed with an unbound or unverified budget. 
3. **Emergency Disarm**: If the **Global Emergency Limit** of `$50.00` is breached, the model gateway switches `LLM_PROVIDER_MODE="shadow"` system-wide, bypassing live APIs and falling back to deterministic fixtures.

---
**Approved by:** Maksym (Lead Developer / CFO)  
**Enforced by:** DNK OS BudgetManager Layer  
