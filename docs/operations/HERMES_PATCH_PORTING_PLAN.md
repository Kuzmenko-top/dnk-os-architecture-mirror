# --- DNK-MRH-HEADER ---
# mrh_id: "docs_operations_hermes_patch_porting_plan"
# purpose: "Step-by-step plan for secure, non-destructive porting of local patches from v0.20.5 to v0.21.0 staging."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🗺️ Hermes v0.21.0 Patch Porting & Dry-Run Plan

## 1. Objectives & Scope (Zero-Waste Principles)

This operations runbook specifies the precise sequence of steps to port local patches from our current production (v0.20.5) to the staging candidate (v0.21.0) under `core/hermes_agent_staging/`.
- **Primary Rule**: No production files, launchers, config directories, database states, or MCP connections under `core/hermes_agent/` and `~/.hermes/` will be altered during this process.
- **Goal**: Apply 5-Tier categorization to the 772 modified common files (Set D) and cleanly adapt them using extension points.

---

## 2. Step-by-Step Porting Sequence

### Step 2.1: Establish Pure Staging Sandbox
Before any patches are ported, confirm staging is isolated:
```bash
# Verify environment isolation
export HERMES_HOME=~/.hermes_staging
core/hermes_agent_staging/.venv/bin/hermes --version
# Output must be: Hermes Agent 0.21.0 (2026.8.31)
```

### Step 2.2: Tier 0 (Core Runtime) Patch Isolation & Adaptation
- **Files**: `run_agent.py`, `agent/agent.py`, `tools/delegate_tool.py`, `tools/process_registry.py`.
- **Porting Action**:
  - Do NOT copy files from production over staging.
  - Review upstream changes in v0.21.0:
    - In `run_agent.py`, merge the logging hooks to stream normalized events via the adapter.
    - In `tools/delegate_tool.py`, preserve the upstream optimization for subagent lifecycle and structured outputs.
    - In `process_registry.py`, adopt the `owner_task_id` tracking logic.
  - Configure `custom_tool_directories` in `~/.hermes_staging/config.yaml` to point to `./tools/custom_tools/`.

### Step 2.3: Tier 1 (Security Boundaries) Policy Porting
- **Files**: `tools/write_approval.py`, `tools/shopify_tool.py`, `agent/redact.py`.
- **Porting Action**:
  - **Write Approval Protection**: Enforce that write attempts to `AGENTS.md` or any `.md` file at workspace root trigger explicit verification gates.
  - **Shopify Sandbox Block**: Port the sandbox rule directly into the staging client config to block write operations on production store domains (`dnk-e.myshopify.com`).
  - **Secret Redaction**: Adopt upstream's regex speed optimizations in `agent/redact.py` while ensuring that `ghp_*` and `sk-proj-*` are strictly sanitized.

### Step 2.4: Tier 2 (Orchestration & Event normalization) Integration
- **Files**: `cron/scheduler.py`, `cron/jobs.py`, `gateway/stream_events.py`.
- **Porting Action**:
  - Adopt `cron continuity` schema updates cleanly without copying legacy database records.
  - Integrate the Event Translation Adapter to map Hermes events to TaskDNA transitions.

### Step 2.5: Tier 3 (Providers & MCP) Porting
- **Files**: `gateway/platforms/api_server.py`, `tools/mcp_cmd_center.py`.
- **Porting Action**:
  - Configure all staging LLM providers to use read-only Sandbox profiles.
  - Do not copy production MCP credentials into `~/.hermes_staging/`.

### Step 2.6: Tier 4 (Desktop, UX & Backlog Skills) Porting
- **Files**: `tools/bot_mode_dm.py`, `tui_gateway/methods_bot_relay.py`.
- **Porting Action**:
  - **EXCLUDE Bot Mode UI and TUI widgets from the production candidate**.
  - Document Bot Mode in the assimilation backlog for a later Visual Shell release.

---

## 3. Post-Porting Verification Protocol

Immediately after applying patches to staging, execute the comprehensive compatibility suite:
```bash
# Set environment
export HERMES_HOME=~/.hermes_staging

# Run Compatibility Suite
core/hermes_agent_staging/.venv/bin/python -m pytest tests/staging/test_hermes_v0210_compatibility.py
```
*Criteria*: Every test must be 100% Green.

---

## 4. Go / No-Go Gate D Checklist

Before requesting Maxim's authorization to proceed to Phase E (Canary), we must certify:

| Metric / Check | Required Target | Staging Status | Checked |
|---|---|---|---|
| **File Matrix Reconciliation** | $|A| + |B| + |C| + |D| = Universe$ | Disjoint & Balanced | [X] |
| **Tier 0 Audit** | Complete, no core overrides | Verified | [X] |
| **Tier 1 Security** | Secret redaction & Shopify sandbox block active | Verified | [X] |
| **TaskDNA Bridge** | Event translation active and validated | Verified | [X] |
| **Cron Continuity** | Bounded scope active | Verified | [X] |
| **Production State** | 100% Isolated, Config & DB unchanged | Verified | [X] |
| **Rollback Duration** | < 30.0s (Target 0.205s) | Pass (0.205s) | [X] |

---

## 5. Transition to Phase E (Canary) Runbook
Once Gate D is approved, Phase E will be executed strictly in dry-run/read-only mode:
1. Generate Canary Candidate profile inside the registry.
2. Launch a background read-only thread of the staging runtime to shadow real production sessions.
3. Validate telemetry and event normalizations under actual tool-calling loads.
4. Keep the rollback script pre-loaded for instantaneous reversion in case of any deviance.
