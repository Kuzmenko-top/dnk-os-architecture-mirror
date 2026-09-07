# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/standards/DNK-SEC-043_agno_execution_sandbox.md"
# purpose: "Security & Sandbox Standard for Agno Agentic Tool Execution and HITL Verification."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-CANVAS-AGNO-SEC"]
# status: "Approved"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Gerych (Hermes Prime)"
# --- END DNK-MRH-HEADER ---

# 🛡️ DNK-SEC-043: Agno Agent Tool Sandbox & Human-in-the-Loop Security Standard

## 1. Scope & Threat Model
When running dynamic multi-agent workflows on the DNK OS Infinite Canvas with Agno primitives, agents can invoke local tools, execute Python code, access file systems, and send network requests.

### Core Threat Vectors:
1. **Unbounded Code Execution**: Agent generating untrusted scripts affecting host OS.
2. **Secret & Key Leakage**: Propagation of API keys, database credentials, or auth tokens to client canvas UI.
3. **Irreversible Mutations**: Database drops, file overwrites, or third-party webhooks firing without human sign-off.
4. **Token Exhaustion & Denial of Service**: Uncontrolled agent-to-agent feedback loops.

---

## 2. Mandatory Security Invariants

### 2.1 Dangerous Operation Classification & HITL Gates
Any tool belonging to the following categories **MUST** trigger an asynchronous HITL checkpoint:
- **Filesystem Deletion / Overwrite**: `rm`, `delete_file`, `drop_table`.
- **Infrastructure Mutators**: `deploy_service`, `docker_run`, `git_push --force`.
- **External Webhooks / Payments**: Financial transactions, automated customer messaging.
- **Budget Limits**: Single-run token consumption exceeding threshold (e.g. 50,000 tokens).

### 2.2 Client-Side Sanitization
- Under no circumstances should backend environment variables (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `VERTEX_API_KEY`, `GH_TOKEN`) be included in node configs, DTOs, or SSE events sent to the web browser.
- Tool responses containing sensitive strings must be masked before saving to public canvas run logs.

### 2.3 Sandboxed Execution Environment
- All code-execution tools invoked by canvas agent nodes must execute inside bounded subprocesses or isolated containers with:
  - Read-only root mount (except designated `/tmp/sandbox/` scratchpad).
  - Memory limit (max 512MB per node runner).
  - CPU execution timeout (max 30s per tool call).
  - Restricted network egress (whitelisted domains only).

---

## 3. Compliance Verification
- Automated tests in `tests/test_agno_canvas_assimilation.py` must verify that attempting dangerous actions without approval halts execution in `PAUSED_HITL` state.
