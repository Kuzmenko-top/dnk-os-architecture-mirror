# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-SEC-043_deepseek-harness-execution-sandbox.md"
# purpose: "Security Specification: Monotonic Invariants, Sandbox Sanding, and Leaks Guard in DNK OS"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ Security Specification DNK-SEC-043: Tool Guard Pipeline & Execution Sandbox

## 1. Monotonic Synchronous Invariants
- **Path Sanitization**: Immediate rejection of any path starting with `/Users`, `/home`, `/etc`, or absolute root `/` when `enforce_relative_paths=True`.
- **Secret Isolation**: Interception of modifications or reads targeting `.env`, credential files, or auth keys.
- **SpendGuard Boundary**: Tool calls subject to SpendGuard token limits and financial caps.

## 2. Dynamic Execution Sandbox
- Scripts executed via `DNKPTCEngine` cannot mutate the host globals, read unsanctioned system modules, or spawn runaway background loops without hitting timeout barriers.
