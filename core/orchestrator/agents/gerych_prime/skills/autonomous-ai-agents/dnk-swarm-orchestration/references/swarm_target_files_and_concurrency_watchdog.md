# --- DNK-MRH-HEADER ---
# mrh_id: "core/orchestrator/agents/gerych_prime/skills/autonomous-ai-agents/dnk-swarm-orchestration/references/swarm_target_files_and_concurrency_watchdog.md"
# purpose: "Operational guidelines for explicit target files in swarm dispatches and concurrency watchdog protocols."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 🛡️ Swarm Target Files & Concurrency Watchdog Protocols

## 1. Explicit `target_files` Manifest in Swarm Dispatches
When dispatching parallel worker tasks via `dnk_swarm_parallel`, always include explicit relative paths in the task payload:
```python
dnk_swarm_parallel(tasks_json=[
    {
        "agent": "dnk_dev_fullstack",
        "action": "build_router",
        "payload": {
            "target_files": ["apps/api/routers/example.py"],
            "task_description": "..."
        }
    }
])
```
### Why:
- **Zero Collision**: Prevents concurrent agents from modifying overlapping files.
- **Auto-Scaffolding**: Enables runtime scaffolding engines to pre-create target file directories and stubs safely.
- **Scope Containment**: Disallows workers from roaming across unrelated modules.

## 2. High-Concurrency TestClient Thread Safety
Starlette's `TestClient` uses an underlying synchronous client that is **not thread-safe** when shared across concurrent worker threads in `ThreadPoolExecutor`.
### Pattern:
```python
import threading
from starlette.testclient import TestClient

_thread_local = threading.local()

def get_test_client(app):
    if not hasattr(_thread_local, "client"):
        _thread_local.client = TestClient(app)
    return _thread_local.client
```

## 3. Server Daemon Hang Watchdog & Hard Timeouts
Background servers running in daemon threads (e.g., `uvicorn.Server.run()` or WebSocket server loops) frequently fail to terminate on SIGINT or during Pytest teardown.
### Pattern:
- In test harnesses, apply explicit timeouts: `timeout 45s pytest tests/load/` or `pytest --timeout=45`.
- In dedicated stress-runner scripts, ensure `os._exit(0)` is called at the end of the script to terminate all dangling daemon threads.
- Always set `os.environ["TESTING"] = "1"` before high-concurrency benchmarks to bypass security rate limiters (`SecurityMiddleware HTTP 429`).
