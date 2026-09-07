# --- DNK-MRH-HEADER ---
# mrh_id: "docs_architecture_dnk_hermes_boundaries"
# purpose: "Policy and architectural boundaries governing upstream Hermes Agent features inside DNK OS."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-HUB-ARCH-002"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "Gerych (Hermes Prime) & Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ DNK OS & Hermes Agent Capability Boundaries

## 1. Upstream Capabilities vs. DNK OS Policies

Upstream runtime enhancements in Hermes Agent v0.21.0 expand execution primitives, but **under no circumstances do runtime primitives grant unconstrained authority within DNK OS**.

| Upstream Feature | Upstream Primitive | DNK OS Policy Boundary | Enforcement Mechanism |
|---|---|---|---|
| **Bot Mode & Roster** | Multi-agent group chat & visual roster | Presentation layer only. Does NOT distribute supervisor authority. Gerych Prime remains the sole supervisor. | `core/orchestrator/agents/` supervisor guard |
| **`hermes peer`** | Unfiltered P2P messaging between profiles | Normalized event delivery. Every peer exchange emits a structured task artifact into the DNK audit log. No private unlogged deals. | `core/contracts/hermes_event_contract.yaml` |
| **Cron Continuity** | Stateful memory carried across recurring ticks | Memory-scoped execution. Prohibited from writing directly to SCONES L3 memory. Runs in local sandbox only. | `core/scones_l3_memory.py` write gate |
| **Live Subagent Steering** | Parent agent steers or kills child processes | Strictly bound to TaskDNA DAG nodes. Steering cannot violate pre-allocated token or cost budgets. | `core/task_dna.py` execution validator |
| **Desktop Browser** | Live interaction with DOM and web inputs | Strictly isolated to Sandbox and Dev Store previews. Zero interaction with live production Shopify stores without human sign-off. | `docs/security/HERMES_PERMISSION_MATRIX.md` |
| **Instruction Protection**| Approval required for `AGENTS.md` & memories | Adopted 100% as an immutable baseline. Gerych cannot override its own core governance rules. | Hermes approval hooks & DNK pre-tool hook |

---

## 2. Priority Assimilation Roadmap

### 🔴 High Priority (Immediate Contractual Integration)

1. **Structured Delegation with JSON Schema & Live Steering**:
   * Integrate upstream `delegate_task` into `TaskDNA`.
   * Enforce schema contracts on all worker outputs.
   * Require explicit verification before output is ingested into the parent context.

2. **Audited Peer Messaging**:
   * Wrap `hermes peer` in an event-sourcing adapter:
     `Peer Message -> Normalized Event -> TaskDNA Artifact -> Audit Trail`.
   * Ensure Gerych Prime maintains 100% visibility over inter-agent data exchange.

3. **Memory-Scoped Cron Continuity**:
   * Attach explicit `memory_scope: project_only` and `write_to_l3: false` to all recurring jobs.
   * Restrict recurring jobs to differential change detection (diffs only).

4. **Protected Instruction & Memory Gates**:
   * Enforce fail-closed verification whenever files like `AGENTS.md`, `runtime_registry.yaml`, or core memories are accessed for write operations.

### 🟡 Medium Priority (Presentation & UI Adaptation)

1. **Bot Mode Visual Integration**:
   * Expose the 14 agent personas inside the DNK Visual Shell / Canvas for visual monitoring and human collaboration.
   * Keep orchestration logic decoupled from UI chat rooms.

2. **Sandbox Browser Verification**:
   * Connect browser execution solely to Liquid theme preview servers and local headless test suites.
   * Require DOM evidence, screenshots, and rollback scripts on every automated browser action.
