# --- DNK-MRH-HEADER ---
# mrh_id: "references/structured_logging_and_distributed_tracing_protocol.md"
# purpose: "Canonical Structured Logging, Async Context Tracing & Virtualenv Execution Protocol (DNK-STD-0080)."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 📊 Structured Logging, Async Context Tracing & Venv Execution Protocol

## 1. Overview & Standard (DNK-STD-0080)
DNK OS employs JSON-structured logging and distributed tracing across HTTP, WebSockets, and Swarm Agent tasks to ensure complete observability, correlation, and ELK/Loki ingestion compatibility.

## 2. Core Log Schema
Every log entry emitted by `StructuredLogger` complies with the canonical schema:
```json
{
  "timestamp": "2026-09-05T12:00:00.000000Z",
  "level": "INFO",
  "service": "dnk-api",
  "trace_id": "4b68e987-9bc0-4e3a-9357-19011be47bf5",
  "span_id": "a953e5dc-298a-4be4-a823-1d01f8aa2266",
  "parent_span_id": null,
  "message": "Processing request",
  "context": {
    "method": "POST",
    "path": "/api/v1/agent/run",
    "status_code": 200,
    "duration_ms": 12.4
  }
}
```

## 3. Distributed Tracing Propagation
1. **HTTP Requests**:
   - `TraceMiddleware` in `apps/api/main.py` extracts incoming `X-Trace-ID` or generates a fresh UUIDv4.
   - Sets `trace_id` in Python's `contextvars` for the request lifecycle.
   - Logs request method, path, status_code, and `duration_ms`.
   - Injects `X-Trace-ID` in the outgoing response header.

2. **WebSocket Events**:
   - In `apps/api/routers/canvas_v3_ws.py`, on connect, a `trace_id` is assigned to the session.
   - If incoming message carries `trace_id`, it is preserved; otherwise the connection's `trace_id` is used.
   - Outgoing messages echo `trace_id`.
   - Logs `WS_CONNECT`, `WS_DISCONNECT`, `WS_MESSAGE`, and `WS_ERROR`.

3. **Agent Tasks & Spans**:
   - Spans are generated using `trace_span(span_name, **metadata)` context manager.
   - Nesting auto-links `span_id` and `parent_span_id`.

## 4. Execution Invariant: Virtualenv Python vs System Python
- **Trap**: Running `python3 -c "..."` or bare `pytest` in terminal commands invokes the host/macOS Python which lacks workspace packages (`starlette`, `fastapi`, `pydantic`), causing `ModuleNotFoundError`.
- **Rule**: ALWAYS execute tests and verification scripts via the workspace virtual environment:
  ```bash
  ./.venv/bin/python -c "..."
  ./.venv/bin/pytest apps/api/tests/test_tracing.py -v
  ```
