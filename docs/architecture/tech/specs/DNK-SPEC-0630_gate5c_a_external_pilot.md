# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-SPEC-0630_gate5c_a_external_pilot.md"
# purpose: "Define specifications, safety contracts and configuration for Gate 5C-A External Pilot."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

# 🛡️ GATE 5C-A: CONTROLLED EXTERNAL PILOT CONTRACT

This specification defines the strict operational rules, configuration contracts, and security guards for the first phased external rollout tier of **DNK OS Canvas (Gate 5C-A)**.

## ⚙️ 1. Pilot Configuration Contract

To prevent hardcoding of sensitive client parameters, all configuration is strictly injected via Environment variables or Secret Managers. No hardcoded tenant UUIDs are allowed in source code.

```bash
# Activation flag
export LLM_PROVIDER_MODE=validated

# Single whitelisted target UUID for External Pilot Phase 1
export LLM_WHITELISTED_WORKSPACES="APPROVED_EXTERNAL_WORKSPACE_UUID"

# Primary tracking workspace for active pilot
export LLM_CANARY_WORKSPACE_ID="APPROVED_EXTERNAL_WORKSPACE_UUID"

# Budget limits and safety switches
export LLM_BUDGET_ENFORCED=true
```

## 🔒 2. Safety Guards & Run-Time Constraints

1. **Strict Whitelisting Guard**: Any execution run requested outside the single registered `APPROVED_EXTERNAL_WORKSPACE_UUID` MUST instantly degrade to **shadow mode**, bypassing live LLM provider calls and returning safe deterministic mock results.
2. **PostgreSQL & Redis Active Requirement**: The pilot runs exclusively on a production-like containerized stack with active PostgreSQL (Alembic migrated) and Redis (for real-time event tracking and pub/sub audits). Local SQLite fallbacks are explicitly blocked.
3. **Cross-Workspace Mutation Prevention**: Every document revision is hashed and validated against the tenant-owner scope. Attempting to write or read across different workspaces triggers a strict `SecurityException` and terminates execution immediately.

---
**Approved by:** Maksym (Lead Developer / CTO)  
**Enforced by:** DNK OS Supervisor & Sandbox Core  
