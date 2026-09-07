# --- DNK-MRH-HEADER ---
# mrh_id: "skills/software-development/sota-repository-assimilation/references/agno_multiagent_workflow_and_hitl_assimilation.md"
# purpose: "Reference patterns for assimilating Agno multi-agent teams, workflow DAGs, memory sync, and HITL approval gates into DNK OS Infinite Canvas"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧬 Agno Multi-Agent & Workflow DAG Assimilation Reference

## 🎯 Architectural Invariants & Topology
When assimilating multi-agent frameworks (such as Agno, CrewAI, AutoGen) into the DNK OS Infinite Canvas:

1. **Spatial Multi-Agent Team Modes (`TeamNode`)**:
   - `route`: Top-level orchestrator evaluates prompt and routes execution to the most specialized agent node (`dnk_shopify`, `dnk_dev_fullstack`, `dnk_video_ai_creator`).
   - `broadcast`: Fan-out execution across multiple agent nodes in parallel, consolidating outputs into a unified context payload.
   - `tasks`: Sequential pipeline where each node's output feeds the next node along directed edges (`Edge`).
   - `consensus`: Multi-agent deliberation/debate loop (e.g. Builder 🛡️ vs Auditor ⚔️) reaching synthesis or quorum.

2. **Non-Blocking Human-in-the-Loop (HITL) Checkpoints**:
   - Never block execution threads with synchronous CLI prompts during long-running workflows.
   - For risky tools (`delete_file`, `deploy_production`, `external_api_billing`), serialize a `HITLCheckpoint` into SQLite/Postgres.
   - Transition node status to `PAUSED_HITL` and return state snapshot with opaque `checkpoint_id`.
   - Resume execution asynchronously via `resume_hitl_checkpoint(checkpoint_id, decision, modified_params)`.

3. **Two-Way Agentic Memory Synchronization (`MemoryNode`)**:
   - Integrate node-level memory directly with SCONES long-term store (`ws-alpha-001`).
   - Extract synthesized facts upon node completion and inject matching workspace memories into agent prompt context prior to execution.

4. **Fallback Research Strategy**:
   - When upstream GitHub API rate limits or connection timeouts occur (`gh api` exit status 4 or urllib timeout), fall back immediately to `services/dnk_git_research` combined with targeted domain `web_search` over official docs.
