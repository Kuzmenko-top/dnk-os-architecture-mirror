# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/founder_operational_verification_and_roadmap_delivery_protocol.md"
# purpose: "Founder-Level Operational Leverage, Automated E2E Verification & Local Recipe Delivery Protocol."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🎯 Founder-Level Operational Leverage, Automated E2E Verification & Local Recipe Delivery Protocol

## 1. Executive Context & Founder Psychology
Founders, lead architects, and operators do not accept narrative summaries or assertions like "everything has been implemented and tested successfully" without concrete, instant, and frictionless local proof.
When completing any multi-step architectural slice, roadmap, or refactoring sequence (e.g. `docs/notes/052_session_2f75dc_audit_and_swarm_execution_roadmap.md`), the delivering agent MUST provide immediate operational leverage.

Operational leverage is defined by three factors:
1. **Zero Cognitive Friction**: The founder should not need to guess how to run, import, or verify the newly created components.
2. **Deterministic Reproducibility**: One copy-pasteable CLI command executes a full-spectrum smoke test that exercises all changed layers live.
3. **Transparent Execution Latency & Telemetry**: Output includes concrete timings (sub-100ms retrieval, DAG completion flags) proving that components run in reality, not as mock stubs.

---

## 2. The 3-Tier Verification Recipe Deliverable

Every multi-component task completion report must contain:

### Tier 1: Unified E2E Live Runner (`scripts/system/verify_roadmap_<ID>.py`)
A dedicated Python test runner that exercises each subsystem sequentially:
- **Storage / Memory Tier**: Initializes `UnifiedMemoryBroker(vault_path=...)`, exercises `route_and_query(...)`, measures latency in milliseconds, verifies hit counts.
- **Hygiene & Gates Tier**: Programmatically audits YAML frontmatter, unique 3-digit prefixes, and path safety (rejecting `/Users/...`).
- **Swarm Control Plane Tier**: Invokes `SwarmDirector.list_agents()`, verifies all 14 agents report `HEALTHY`, tests semantic routing classification, and executes a multi-step `PipelineBuilder` DAG via `ExecutionBroker`.
- **Assets / Manifests Tier**: Syntactically extracts and parses JSON payloads (e.g. Remotion video specs, Shopify AST trees), verifying required dimensions, FPS, and schemas.

### Tier 2: Targeted Pytest Command
An isolated, high-speed pytest command targeting the exact verification test files:
```bash
./.venv/bin/pytest tests/verification/test_<module>_hygiene.py -v
```
Must finish in under 2 seconds to avoid cognitive fatigue.

### Tier 3: Stateful Telemetry / Subsystem Inspection Command
A deterministic CLI command inspecting real state (e.g. Task Forest graph nodes, SQLite/DuckDB stats, or Redis checkpoints):
```bash
./.venv/bin/python3 scripts/system/update_task_forest_metrics.py --json
```

---

## 3. Pitfalls & Anti-Patterns to Avoid
1. **The "Check it Yourself" Fallacy**: Telling the user "You can import X and call Y" without providing the exact executable script and CLI invocation.
2. **API Signature Guessing**: Calling `broker.query()` instead of checking `inspect.signature(broker.route_and_query)` or accessing `.text` instead of `.content`. Always inspect signatures before generating user-facing scripts.
3. **Synchronous vs Asynchronous Mismatch**: Treating synchronous methods as coroutines (`await pipe.execute()`) or vice-versa. Always check method signatures.
4. **Absolute Path Bleed**: Embedding machine-specific absolute paths (`/Users/...`) in test runners or output examples. Always use relative paths (`./`, `docs/notes/...`).
