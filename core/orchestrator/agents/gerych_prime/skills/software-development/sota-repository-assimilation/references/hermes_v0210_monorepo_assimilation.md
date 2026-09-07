# --- DNK-MRH-HEADER ---
# mrh_id: "sota_assimilation_references_hermes_v0210_monorepo_assimilation"
# purpose: "Technical Reference for Safe Staged Assimilation of Monorepo-Embedded Runtimes (Zero Blind Rsync)"
# author: "Gerych (Hermes Prime) & Maksym"
# status: "Active"
# version: "2.1.0"
# updated_at: "2026-09-03"
# --- END DNK-MRH-HEADER ---

# 🧬 Technical Reference: Safe Staged Assimilation of Embedded Runtimes

This reference defines the strict protocol for assimilating upstream releases of agent execution runtimes (e.g. `NousResearch/hermes-agent`) embedded within the DNK OS monorepo (`DNK_HUB`), ensuring zero regressions to local custom enhancements.

---

## 🚫 CRITICAL PITFALL: Blind Rsync / Overwrite Ban

**NEVER execute `rsync -av temp/ core/<runtime>/` directly into an embedded runtime directory.**

Why blind rsync is forbidden:
1. **Embedded Unmanaged Fork**: In monorepos, embedded runtimes contain local patches, custom hooks, and proprietary tools (e.g., `run_agent.py`, `toolsets.py`, DNK-specific tools, MRH validation headers, session storage wrappers). In our audit of v0.20.5 vs v0.21.0, blind copy would have permanently destroyed **994 DNK-exclusive files**.
2. **Silent Destruction of Custom Behaviors**: A direct rsync or directory copy overwrites modified source files and deletes uncommitted customizations without warnings.
3. **Control Plane vs. Execution Layer Invariant**: Upstream runtimes are **Execution Layers only**; they do not dictate policy, TaskDNA DAGs, security boundaries, or cognitive memory permissions. Blind copying risks breaking this architectural boundary.

---

## 🛡️ The 6-Phase Staged Assimilation Protocol (SSOT)

Follow the phased lifecycle documented in `docs/operations/HERMES_UPGRADE_RUNBOOK.md`:

### Phase A: Runtime Freeze & Working Tree Baseline
- Ensure all ongoing swarm tasks and background daemons are terminated.
- Record the exact git commit SHA and status of parent repo (`git rev-parse HEAD`, `git status --porcelain`).

### Phase B: State Backup & Asset Hash Recording
- Back up state, session DBs, and config folders:
  ```bash
  cp -r ~/.hermes ~/.hermes_backup_$(date +%Y%m%d_%H%M%S)
  ```
- Generate SHA-256 baseline hashes of critical modified files:
  ```bash
  find core/hermes_agent -type f -name "*.py" -exec sha256sum {} + > core/hermes_agent_baseline_hashes.txt
  ```

### Phase C: Isolated Staging Environment Setup
- Deploy upstream release strictly into an **isolated directory** (`core/hermes_agent_staging/`) with its own virtualenv:
  ```bash
  mkdir -p core/hermes_agent_staging
  curl -L https://github.com/NousResearch/hermes-agent/archive/refs/tags/v2026.8.31.tar.gz | tar -xz -C core/hermes_agent_staging --strip-components=1
  cd core/hermes_agent_staging
  uv venv .venv --python 3.12
  source .venv/bin/activate
  uv pip install -e .
  deactivate
  cd ../..
  ```
- **Staging Isolation Invariants**:
  - `HERMES_HOME` points strictly to `~/.hermes_staging` (never `~/.hermes`).
  - Isolated port binding (e.g., `gateway_port: 8766`).
  - State DB and session store isolated: zero sharing of `state.db`.
  - Zero leakage of production credentials or browser cookies.
  - Strict sandbox URL validation (e.g. Reject `*.myshopify.com` mutations).

### Phase D: Compatibility Audit & Surgical Patch Migration
- **Mathematical Reconciliation of File Space**: Before migration, resolve any file count discrepancies between the local fork and upstream archive. Map the total repository space using set theory to guarantee 100% accounting:
  $$|A \cup B \cup C \cup D| = |A| + |B| + |C| + |D|$$
  where:
  - **Set A (Upstream Only)**: Files present in the upstream release but absent in the local fork.
  - **Set B (DNK Only / Local Extensions)**: Files proprietary to our fork, representing extensions, scripts, and specifications.
  - **Set C (Identical Common)**: Shared files with identical SHA-256 hashes.
  - **Set D (Modified Common)**: Shared files with different SHA-256 hashes (the patch inventory candidates).
  *Reconciliation Pitfall*: The upstream count is $|A \cup C \cup D|$, while the local count is $|B \cup C \cup D|$. The total unique files in play is the union $|A \cup B \cup C \cup D|$. Discrepancies are mathematically resolved when the union matches the sum of the four mutually exclusive sets.

- **Explicit Resolution & Deferred Structure (Avoid Flat "Unresolved: 0")**:
  Never report a bare `unresolved: 0` without structured severity and deferred scope. A flat zero is easily misinterpreted as "all files in Set D were ported", even when upstream features were consciously omitted. Always declare:
  ```yaml
  unresolved:
    critical: 0
    high: 0
    medium: 0
    low: 0
    deferred:
      - name: "Bot Mode"
        reason: "Visual Shell UI component; excluded from core CLI/agent candidate scope."
        tier: "Tier 4"
      - name: "desktop UX"
        reason: "Native Electron desktop plugins; not required for core backend/CLI agent runtime."
        tier: "Tier 4"
      - name: "optional skills"
        reason: "Third-party optional skills deferred until core runtime stabilization."
        tier: "Tier 4"
  ```

- **5-Tier Component Audit Classification**:
  Categorize and audit all Set D (Modified Common) files by tier to limit blast-radius:
  - **Tier 0 (Core)**: The agent loop (`agent.py`), execution entrypoint (`run_agent.py`), state persistence (`state_db`), and core execution engines. Require line-by-line review of edits.
  - **Tier 1 (Security)**: Context sandboxing (`AGENTS.md` and system prompt boundaries), secret redaction pipelines, and tool approval engines. Zero-compromise tier.
  - **Tier 2 (Orchestration)**: Live-steering protocols, cron scheduling, peer/subagent events, and task graph integration.
  - **Tier 3 (Providers & MCP)**: Model configurations, API schema mappings, and server declarations.
  - **Tier 4 (UX / Experimental)**: Bot Mode, desktop panels, and web dashboards.
  *Architecture Rule*: High-impact features like Bot Mode that are not needed for initial core automation should be isolated and placed into the backlog to streamline initial core promotion.

- Run patch inventory diff inspection and generate the file matrix:
  ```bash
  python3 scripts/system/generate_phase_d_matrix.py
  ```
- Surgically port DNK-specific extensions into staging, ensuring all new files maintain `DNK-STD-0075` MRH headers. Use loose coupling and explicit extension points rather than direct core modifications.

### Phase E: Automated Canary Verification & Process-Level Integration Tests
- **Two Distinct Testing Tiers Invariant**:
  - **Tier 1: Unit & Contract Tests**: Fast execution (<0.01s), mock objects, signature and contract validation. Valid for Phase D compatibility, but **insufficient on their own for Phase E Canary**.
  - **Tier 2: Process & Integration Tests**: Must run real OS processes, allocate PIDs, dispatch OS signals (`SIGTERM`, `SIGKILL`), execute SQLite transactions, and verify runtime telemetry.
- **Canary Pre-Flight Check**:
  Record baseline SHA-256 cryptographic hashes of all production artifacts (`~/.hermes/state.db`, `~/.hermes/config.yaml`, launcher binaries) before executing canary suites.
- **7 Mandatory Canary Scenarios (C1–C7)**:
  1. **C1 (Supervisor Task)**: Real task decomposition from TaskDNA, worker profile matching, sandbox parameter validation, and persistent tracking in staging DB.
  2. **C2 (Delegation Lifecycle)**: Spawn real OS subprocess, live `steer` instruction delivery, graceful stop via `SIGTERM`, verification of partial results recovery, and 0 orphan processes via `psutil`.
  3. **C3 (Peer Communication Bridge)**: Multi-agent message exchange across staging event bus (`researcher -> builder -> auditor`) with normalized contract schemas.
  4. **C4 (Cron Continuity 3-Run Engine)**:
     - Run 1: Baseline generation.
     - Run 2: Unchanged tick -> duplicate alert suppression (`no_change`).
     - Run 3: Modified state -> change alert trigger with payload verification.
     - Scoped memory footprint bounded (<8 KB) with zero write-through to production.
  5. **C5 (Security Boundary & Containment)**: Probing 5 attack vectors (`AGENTS.md` tamper, secret extraction, production e-com/ERP mutations, unauthorized MCP registration, unvalidated L3 memory writes) — all must be contained.
  6. **C6 (Cost Accounting)**: Multi-session token attribution (interactive, delegated child, cron, failed retries) with 0 double-counting.
  7. **C7 (Crash & Recovery)**: Forcible worker termination via `SIGKILL (-9)`, lock cleanup, and transaction recovery from latest persistent checkpoint.
- **Canary Pass Gate Criteria**:
  - `orphan_processes == 0`
  - `production_writes == 0` (Post-Canary SHA-256 == Pre-Canary SHA-256)
  - `policy_bypasses == 0`
  - `unaccounted_events == 0`
  - `rollback_sla <= 2.0s` (Target: < 0.5s)
- **Gate E Halt**: Once canary tests succeed and thresholds are certified, HALT and await explicit review. Never auto-promote.

### Phase F: Controlled Atomic Promotion
- Swap runtimes atomically only after **explicit approval from Maxim**:
  ```bash
  mv core/hermes_agent core/hermes_agent_prev_v0.20.5
  mv core/hermes_agent_staging core/hermes_agent
  ```
- Update `core/registry/runtime_registry.yaml` with the new active runtime metadata and SHA hashes.

---

## ⏱️ Programmatic 30-Second Rollback Drill (T0 - T4 Benchmark)

To validate rollback viability prior to promotion, run `scripts/system/measure_rollback_drill.py`:
- **T0**: Trigger rollback drill.
- **T1**: Verify runtime pointer resolves to stable baseline (`~/.local/bin/hermes` -> `core/hermes_agent/.venv/bin/hermes`).
- **T2**: Restore production environment variables (`HERMES_HOME=~/.hermes`).
- **T3**: Execute stable CLI (`hermes --version` returns v0.20.5).
- **T4**: Healthcheck & session resume (verify `state.db` schema: column `started_at`, 24 tables intact).
- **Threshold**: Total duration `T4 - T0 <= 30.0s` (Measured: ~0.205s).

---

## 🛠️ Upstream API Signatures & Schema Pitfalls
- **SessionDB API in Hermes v0.21.0**:
  `SessionDB.create_session()` takes `(session_id, source)` instead of `(title, profile)`. Title assignment is performed via `db._set_session_title(session_id, title)`.
- **Sessions Table Column Schema**:
  The SQLite timestamp column is named `started_at` (not `created_at`). Queries ordering by timestamp must use `ORDER BY started_at DESC`.
