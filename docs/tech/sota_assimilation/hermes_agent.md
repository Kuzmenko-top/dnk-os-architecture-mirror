# --- DNK-MRH-HEADER ---
# mrh_id: "docs_tech_sota_assimilation_hermes_agent"
# purpose: "SOTA Assimilation Spec for NousResearch/hermes-agent v0.21.0 (The Pantheon Release) Execution Runtime into DNK OS"
# author: "Gerych (Hermes Prime) & Maksym"
# status: "Active"
# version: "2.0.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

# 🧬 SOTA Assimilation Spec: NousResearch/hermes-agent v0.21.0

- **Upstream URL**: [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)
- **Release Tag**: `v2026.8.31` (Hermes Agent v0.21.0 "The Pantheon Release", Aug 31, 2026)
- **Stars**: ~1,200+ ⭐
- **License**: `MIT` (Approved: Track 1 Permissive)
- **Assimilation Mode**: `Execution/Runtime Layer Update & Pattern Assimilation`
- **Architectural Scope**: **Execution & Tool Runtime Layer ONLY** (Does NOT replace Gerych Core, TaskDNA, SCONES Memory, or DNK Control Plane).
- **Target Bounded Context**: `core/hermes_agent/` / `core/contracts/` / `core/registry/`

---

## 1. Architectural Scope & Definition

**Hermes Agent v0.21.0 ("The Pantheon Release")** serves exclusively as an **Execution and Tool Runtime Layer** underneath the DNK_HUB Control Plane:

```text
Gemini / Vertex AI
        │
        ▼
Model Adapter
        │
        ▼
Hermes Agent v0.21.0 (Execution / Tool Runtime Layer)
        │
        ├── Agent Loop & Trajectory Management
        ├── Tool Execution Sandbox
        ├── Session State DB
        ├── Cron Scheduler
        ├── Subagent Delegation (`delegate_task`)
        ├── Peer Messaging (`hermes peer`)
        └── System File Approvals
                │
                ▼
DNK_HUB Control Plane (Gerych Core)
        │
        ├── TaskDNA Engine
        ├── Swarm Orchestrator (14 Profiles)
        ├── SCONES L1/L2/L3 Cognitive Memory
        ├── Runtime Registry & Permission Matrix
        ├── Financial Token Accounting & Budgeting
        └── Adversarial Verification Gates
```

> **Canonical Definition**: Gerych operates on top of Hermes Agent v0.21.0 as its execution runtime. Gerych's supervisor identity, TaskDNA DAGs, memory policies, registry, DNK permissions, and verification gates remain the sovereign responsibility of DNK_HUB. Upstream capabilities do NOT automatically become DNK OS permissions.

---

## 2. Adopted Concepts & Prioritized Integration

### 🔴 High Priority

#### A. Structured Delegation with Live Steering (`delegate_task`)
- **Upstream Primitive**: Child agent lifecycle management (`action='steer'`, `action='stop'`) and strict JSON Schema output contracts.
- **DNK Assimilation**: Bound directly to TaskDNA DAG execution. Worker agents must return outputs validating against explicit contracts before Gerych Prime ingests them into the supervisor context.

#### B. Normalized Peer Messaging (`hermes peer`)
- **Upstream Primitive**: P2P direct messaging between profile handles.
- **DNK Assimilation**: Normalizes into the DNK Event Log (`core/contracts/hermes_event_contract.yaml`). Peer messages emit structured task artifacts, ensuring full auditability and preventing shadow inter-agent negotiations outside TaskDNA.

#### C. Scoped Cron Continuity (`continuity=true`)
- **Upstream Primitive**: Stateful cron jobs carrying preceding execution outputs across runs.
- **DNK Assimilation**: Restricted to diff-only reporting (`memory_scope: project_only`, `write_to_l3: false`). Used for health-checks, GitHub monitors, and financial spend watchdogs.

#### D. Protected Instruction & Policy Sandboxing
- **Upstream Primitive**: Required approval before writing to `AGENTS.md`, memory, or skills.
- **DNK Assimilation**: Adopted 100% as a zero-trust baseline. System files, permissions, and security headers cannot be rewritten autonomously.

### 🟡 Medium Priority

#### E. Bot Mode Roster (Presentation Layer)
- **Upstream Primitive**: Named personas, avatars, and group rooms.
- **DNK Assimilation**: Mapped to the DNK Visual Shell and Canvas to visualize the 14 specialized swarm profiles. Orchestration remains driven by TaskDNA, not free-form chat.

#### F. Desktop Browser Automation (Dev Preview Only)
- **Upstream Primitive**: Direct DOM and browser interaction via `cua_browser_*`.
- **DNK Assimilation**: Strictly quarantined to Liquid theme dev stores (`*.myshopify.com/preview`) and local headless test servers. Absolute human approval gate for any live store operations.

---

## 3. Upstream Isolation & Prohibitions

- **Prohibition of Blind Overwrite (`rsync`)**: `core/hermes_agent` is an embedded fork containing local DNK adaptations (`run_agent.py`, `toolsets.py`, custom tools, MRH utilities). Blind overwrites are strictly banned.
- **Upstream Auto-Update CLI**: `hermes update` requires a clean standalone git clone and is disabled in favour of the staged assimilation protocol.
- **Uncontrolled Data Leaks**: Default telemetry and telemetry collectors are disabled; state is isolated to local workspace `ws-alpha-001`.

---

## 4. Staged Assimilation Runbook & Governance

All runtime upgrade operations must strictly follow `docs/operations/HERMES_UPGRADE_RUNBOOK.md`:

1. **Phase A (Freeze)**: Stop background services, record git commit SHA and status.
2. **Phase B (Baseline)**: Full backup of `~/.hermes/` and SHA-256 recording of runtime files.
3. **Phase C (Staging Runtime)**: Independent installation into `core/hermes_agent_staging/`.
4. **Phase D (Compatibility Audit)**: Diff analysis and surgical porting of DNK custom patches.
5. **Phase E (Canary Verification)**: Execution of 10 automated verification checks per `docs/verification/HERMES_V0_21_0_VERIFICATION.md`.
6. **Phase F (Controlled Promotion)**: Atomic runtime swap executed ONLY with Maxim's explicit sign-off.
7. **Rollback Drill**: Reversible within 30 seconds back to v0.20.5 upon any anomaly.

---

*Compiled, verified, and integrated into DNK OS architecture under Task DNK-HUB-ARCH-002.*
