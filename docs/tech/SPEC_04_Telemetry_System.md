# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/SPEC_04_Telemetry_System.md"
# purpose: "Canonical documentation and task tracking note"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-09"
# --- END DNK-MRH-HEADER ---

# 🧬 Local Telemetry System Specification (DNK OS 1.0.0)

This document provides the technical specification of the autonomous local bank for tracing, logs, metrics, and step trajectories within **DNK OS**.

---

## 🏛️ Storage Topology

The local telemetry files are structurally isolated to enforce data boundaries and allow fast access by agents and developers.

```
DNK OS/
├── telemetry/
│   ├── traces/          # JSONL files tracking workflow-level runtimes
│   │   └── <task_id>_trace.jsonl
│   ├── trajectories/    # Secure JSON files of overall task execution steps
│   │   └── <task_id>_trajectory.json
│   └── metrics/         # JSONL metrics for token consumption and cost
│       └── <name>_metrics.jsonl
└── logs/
    └── step_logs.jsonl  # Microservices and step logs
```

---

## ⚙️ Core Architecture (`core/local_telemetry.py`)

The system exposes `LocalTelemetryEngine` containing the following high-reliability operational gates:

1. **Atomic Write Protocol**: Re-writing large JSON structures (such as trajectories) is done via `tempfile.NamedTemporaryFile` + `os.replace` to prevent race conditions or partial file corruption.
2. **Strict Access Permissions**: Telemetry files and logs are explicitly saved with `0600` (owner read-write only) file permissions.
3. **Fail-Safe execution**: All file writes are wrapped in non-blocking try-except handlers, guaranteeing that tracing never interrupts main agent execution.

---

## 📋 Operational API & Code Example

```python
from core.local_telemetry import local_telemetry

# 1. Log execution trace
local_telemetry.log_trace(
    task_id="T101",
    tool_calls=[{"tool": "query_db"}],
    inputs={"sql": "SELECT 1"},
    outputs={"data": [1]},
    duration_ms=45,
    cost_usd=0.0001
)

# 2. Log performance metrics
local_telemetry.log_metric("db_latency", 45.0, tags=["postgres"])

# 3. Log granular step logs
local_telemetry.log_step("postgres_client", "Database queried successfully", "INFO")
```

---

*Verified & compiled under the Gerych Chief Builder Authority.*