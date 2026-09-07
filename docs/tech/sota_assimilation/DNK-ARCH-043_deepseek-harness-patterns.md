# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-ARCH-043_deepseek-harness-patterns.md"
# purpose: "Architecture Specification: Tool Guard Pipeline, Cordis Microkernel & PTC Engine in DNK OS"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🏛️ Architecture Specification DNK-ARCH-043: DeepSeek Harness Integration

## 1. Modular Execution Pipeline
```
Tool Call Request
       │
       ▼
[Stage 1: pre_execute]   ─── Denies dangerous shell commands (forkbombs, rm -rf /)
       │
       ▼
[Stage 2: guard]         ─── Invariant enforcement (relative paths, .env tampering)
       │
       ▼
[Stage 3: around_execute]─── Async/sync dispatch with timeout & circuit breaker
       │
       ▼
[Stage 4: post_execute]  ─── Head/Tail symmetric truncation (context diet)
       │
       ▼
[Stage 5: observe]       ─── Telemetry logging, observability and audits
       │
       ▼
Tool Output to Agent
```

## 2. Programmatic Tool Calling (PTC Engine)
- Python code snippet receives a virtual SDK namespace `tools`.
- Script runs within an isolated evaluation scope with access only to allowed primitives.
- Tool executions within the script are tracked and logged via the 5-stage pipeline.
