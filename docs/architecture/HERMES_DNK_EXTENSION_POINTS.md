# --- DNK-MRH-HEADER ---
# mrh_id: "docs_architecture_hermes_dnk_extension_points"
# purpose: "Architecture spec for loose coupling and clean integration boundaries between upstream Hermes and DNK Control Plane."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-03"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🧬 Hermes-to-DNK Integration & Extension Points Spec

## 1. Architectural Philosophy (Decoupled Extensions)

To maintain a SOTA 10x velocity and zero upstream conflict on future upgrades (such as `v0.22.0+`), we strictly enforce the **Hexagonal Adapter Invariant**:
- **Prohibited**: Direct modifications to upstream core execution files (e.g. `agent/agent.py`, `hermes_cli/config.py`, hardcoding tools in `tools/toolsets.py`).
- **Required**: Accessing and extending Hermes strictly through defined boundaries, dynamic registries, and custom tool bundles located outside the upstream core module.

```text
                  ┌─────────────────────────────────┐
                  │       DNK OS CONTROL PLANE       │
                  │  (TaskDNA DAGs, Swarms, Audit)  │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │    DNK INTEGRATION ADAPTERS     │
                  │  (acp_adapter, event Normal.)   │
                  └────────────────┬────────────────┘
                                   │
                                   ▼
                  ┌─────────────────────────────────┐
                  │     HERMES UPSTREAM RUNTIME     │
                  │ (Execution Layer, Tool Calling) │
                  └─────────────────────────────────┘
```

---

## 2. Extension Point 1: Dynamic Custom Tool Registration

Instead of patching `tools/toolsets.py` to inject DNK-specific tools, Hermes v0.21.0 supports pluggable tool directories and MCP (Model Context Protocol).

### 2.1 Dynamic Tool directories
All custom tools for DNK OS live in `core/hermes_agent_staging/tools/custom_tools/`. At runtime, we configure Hermes to load tools dynamically from this directory by setting the environment variable or `config.yaml` setting:
```yaml
tools:
  custom_tool_directories:
    - "./tools/custom_tools"
```
During startup, Hermes automatically discovers and registers all tools with `@tool` decorators defined in files inside this directory, avoiding any edit of `tools/toolsets.py`.

### 2.2 MCP-Driven Tools (FastMCP)
For deep DNK OS control-plane integrations (e.g., querying TaskDNA or writing SCONES memories), we expose them via an MCP Server. This completely isolates our proprietary control-plane from Hermes core.
```yaml
mcp:
  servers:
    dnk_control_plane:
      command: "python"
      args: ["-m", "core.mcp.server"]
      env:
        PYTHONPATH: "."
```

---

## 3. Extension Point 2: Event Normalization & Logging Bridge

Every event inside the Hermes execution loop (agent loop iteration, tool call, error, subagent spawn, steering) is normalled according to `core/contracts/hermes_event_contract.yaml` and streamed to the DNK Audit trail.

### 3.1 Normalization Pipeline
1. **Raw Hermes Hook**: In `run_agent.py` or via a custom event listener, we hook the streaming event queue.
2. **Translation Adapter**: Maps Hermes native events to the DNK Unified event schema:
```python
def normalize_hermes_event(hermes_event: dict) -> dict:
    return {
        "event_id": hermes_event.get("id"),
        "timestamp": hermes_event.get("timestamp"),
        "task_id": hermes_event.get("context", {}).get("task_id", "orphan"),
        "source": "hermes_v0.21.0_staging",
        "type": hermes_event.get("type"),  # e.g., tool_call, llm_thought
        "payload": {
            "name": hermes_event.get("name"),
            "arguments": hermes_event.get("arguments"),
            "response": redact_secrets(hermes_event.get("response"))
        }
    }
```
3. **TaskDNA Transition**: Emitted events trigger corresponding state transitions in the TaskDNA state-machine, tracking progress in real time.

---

## 4. Extension Point 3: ACP (Agent Connection Protocol) Bridge

For IDE integration (VS Code, Zed, JetBrains), the `acp_adapter/` acts as an isolated RPC boundary:
- Operates strictly as a wrapper around `~/.local/bin/hermes`.
- Handles bi-directional JSON-RPC 2.0 messages.
- Decouples IDE client sessions from the underlying Hermes home environment (`~/.hermes` or `~/.hermes_staging`).

---

## 5. Classification and Mapping of the 988 DNK-Exclusive Files

The 988 files existing only in our DNK Fork are mapped to clean layers under the new Extension Point rules:

| Category | File Count | Target Layer / Extension Strategy |
|---|---|---|
| **DNK Control Plane & Domain Specs** | 40 | Kept in the authoritative DNK Control Plane. Hermes is only granted execution permission, never control. |
| **DNK Model Adapters** | 5 | Configured as pluggable standard provider overrides via custom `llm_providers/` configuration, not inside the core. |
| **Custom Tools Package** | 15 | Relocated to dynamic directories under `./tools/custom_tools/` or exposed via FastMCP. |
| **ACP Adapter (Boundary)** | 3 | Maintained as an isolated IPC wrapper. Zero modifications to Hermes core. |
| **MRH Utilities** | 2 | Maintained within the verification and linting layer of the DNK workspace (`scripts/system/`). |
| **DNK Architectural Artifacts** | 624 | Kept entirely within the `docs/` and `core/dna/` repositories. Completely excluded from Hermes core package. |
| **Local Maintenance Scripts** | 281 | Kept in `scripts/` at workspace root. Never loaded by the execution engine. |
| **Caches / Generated Files** | 18 | Fully excluded via `.gitignore` and `.dockerignore`. |
