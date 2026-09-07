# 🏛️ Architecture Spec: Subagent Sandbox Runtime
# --- DNK-MRH-HEADER ---
# mrh_id: "DNK-ARCH-002_agent-sandbox-runtime.md"
# purpose: "Define Sandbox Architecture, Code Lifecycles, and Communication Protocols for DNK OS."
# author: "Maxim"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-10"
# --- END DNK-MRH-HEADER ---

## 📌 1. Subagent Sandbox Topologies

To guarantee zero host pollution on the MacBook, DNK OS partitions execution into three distinct sandbox profiles depending on the subagent's role:

```
               [ DNK OS Supervisor ]
                        │
         ┌──────────────┼──────────────┐
         ▼              ▼              ▼
     [ Rick ]       [ Yuriy ]        [ Cas ]
   (Scout Profile) (Slicer Profile) (Synthesizer Profile)
     Egress: ALL    Egress: NONE     Egress: GATEWAY ONLY
     Disk: R/O      Disk: Temp W/W   Disk: Sandboxed W/W
```

### Profile A: Rick (Scout Profile)
- **Purpose:** Scanning external repositories and scouting open-source patterns.
- **Egress network policy:** Unrestricted outbound (HTTP/HTTPS) to allow GitHub API queries and repository cloning.
- **Disk access:** Mounts codebases as Read-Only (`ro`). Write operations are blocked.

### Profile B: Yuriy (Slicer Profile)
- **Purpose:** Abstract Syntax Tree (AST) parsing, file slicing, and lexical code inspections.
- **Egress network policy:** Strict offline. Zero network interface bindings (`--network none`).
- **Disk access:** Isolated write access to `/tmp/slicer_work` to hold temporary AST representations, with immediate cleanup.

### Profile C: Cas (Synthesizer Profile)
- **Purpose:** Clean-room code generation and blueprint integration.
- **Egress network policy:** Gateway-Only. Allowed to query internal model routers (NVIDIA NIM Gateway, OmniRoute) but strictly blocked from general internet.
- **Disk access:** Bound sandboxed workspace `/workspace/output`. Writes generated assets using structural validation.

---

## ⚙️ 2. Code Execution Lifecycle

Every code evaluation or task run executed by a subagent follows a strict four-stage sequential pipeline:

```
  [ Spawn ] ──────► [ Execute ] ──────► [ Capture Output ] ──────► [ Terminate ]
(Container Boot)   (Harness Code)       (Stream Logs/JSON)        (Prune Sandbox)
```

1. **Spawn (Container Boot)**
   - The Supervisor triggers `docker run` or an equivalent container runtime API call.
   - Applies strict cgroups constraints: memory ceiling `512MB`, CPU shares limit `0.5 CPU`, and a hard execution timeout (default: `30s`).
2. **Execute (Harness Code)**
   - The container boots with an isolated Python execution harness that loads the safe subset of standard libraries.
   - Command/Code payload is passed via standard input (STDIN) or an in-memory unix socket to avoid exposing arguments in `ps` output.
3. **Capture Output (Stream Logs/JSON)**
   - Capture STDOUT and STDERR streams in real-time.
   - Parse outputs, separating execution logs from structured return payloads (formatted as JSON).
4. **Terminate (Prune Sandbox)**
   - The container is immediately killed (`SIGKILL` is sent if `SIGTERM` fails to complete within 3s).
   - `docker rm -f` is executed to prune the container layer, returning the execution node to a pristine state.

---

## 📬 3. Communication Protocol: Supervisor to Worker Sandbox

To isolate the supervisor process from dangerous user-generated scripts or unpredictable agent code, communication is mediated via an asynchronous queue system.

### Queue Channels
- **`mailbox_queue:tasks` (Durable Redis / SQLite Queue):** The Supervisor pushes a structured task payload (MRH header + payload).
- **`mailbox_queue:results`:** The Worker Sandbox posts the outcome back once execution terminates or times out.

### Message Payloads

#### Task Request Payload (Supervisor ➔ Sandbox):
```json
{
  "task_id": "task_mda_002_0091",
  "profile": "Cas",
  "code": "print('Simulated pattern replication')",
  "env_vars": {
    "ALLOWED_GATEWAY_URL": "https://integrate.api.nvidia.com"
  },
  "timeout": 30
}
```

#### Task Response Payload (Sandbox ➔ Supervisor):
```json
{
  "task_id": "task_mda_002_0091",
  "status": "completed",
  "exit_code": 0,
  "stdout": "Simulated pattern replication\n",
  "stderr": "",
  "execution_time_seconds": 0.42,
  "cryptographic_hash": "sha256_bc2f98144ee650117"
}
```

This decoupled model ensures that even a kernel panic or segmentation fault inside the Sandbox cannot hang or crash the master DNK OS Orchestrator.
