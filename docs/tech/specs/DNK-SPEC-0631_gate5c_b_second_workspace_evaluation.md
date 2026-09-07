# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-SPEC-0631_gate5c_b_second_workspace_evaluation.md"
# purpose: "Define specifications, multi-tenant safety contracts, and evaluation benchmarks for Gate 5C-B Second Workspace Evaluation."
# canonical_source: true
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-13"
# author: "DNK-e.com Maksym"
# license: "MIT"
# --- END DNK-MRH-HEADER ---

# 🛡️ GATE 5C-B: SECOND WORKSPACE EVALUATION CONTRACT

This specification defines the multi-tenant operational contracts, configuration policies, and security isolation requirements for evaluating and enabling a second whitelisted workspace under **Gate 5C-B (DNK OS LLM Gates)**.

## ⚙️ 1. Multi-Tenant Configuration Contract

To support multi-workspace evaluation while preventing hardcoding of sensitive workspace identifiers, configuration is strictly injected via comma-separated Environment variables:

```bash
# Activation mode
export LLM_PROVIDER_MODE=validated

# Dual Whitelisted Target UUIDs for Gate 5C-B (Workspace A & Workspace B)
export LLM_WHITELISTED_WORKSPACES="PRIMARY_WORKSPACE_UUID,SECONDARY_WORKSPACE_UUID"

# Target workspace under evaluation
export LLM_EVALUATION_WORKSPACE_ID="SECONDARY_WORKSPACE_UUID"

# Strict budget and rate-limit enforcement
export LLM_BUDGET_ENFORCED=true
export LLM_PER_WORKSPACE_BUDGET_LIMIT=500.00
```

## 🔒 2. Safety Guards & Run-Time Isolation Constraints

1. **Multi-Tenant Whitelisting Guard**: Execution requests from either `PRIMARY_WORKSPACE_UUID` or `SECONDARY_WORKSPACE_UUID` are granted live validated mode access. Requests from any non-whitelisted workspace ID instantly degrade to safe **shadow mode** with deterministic mock execution.
2. **Cross-Tenant Isolation Firewall**: Data, memory, state mutations, and canvas state trees must remain 100% isolated per tenant. Cross-workspace state leaks trigger an immediate `SecurityException` and terminate execution.
3. **Independent Budget Enforcement**: Each active workspace operates under its own isolated budget quota. Exhaustion of Workspace A's budget quota does not affect Workspace B, and vice versa.

## 🧪 3. Evaluation Benchmark Metrics

- **Tenant Routing Correctness**: 100% pass rate for dual whitelisted workspace validation.
- **Fail-Closed Fallback Rate**: 100% fallback to shadow mode for 3rd-party/unwhitelisted workspace requests.
- **Cross-Tenant Mutation Security**: 0 cross-workspace state leakage or unauthorized mutations.
- **Budget Isolation Verification**: Quota enforcement strictly isolated per workspace UUID.

---
**Approved by:** Maksym (Lead Developer / CTO)  
**Enforced by:** DNK OS Supervisor & LLM Gateway  
