# Structured Logging & Distributed Tracing Specification (DNK-STD-0080)

This reference documents the architectural patterns, ContextVars state propagation, and integration recipes for ELK and Grafana Loki stacks.

## 1. Standard Log Record JSON Schema

Every log line MUST be an independent, self-contained JSON string matching ELK/Loki ingestion schemas:

```json
{
  "timestamp": "2026-09-05T11:01:14.123456Z",
  "level": "INFO",
  "service": "dnk-api",
  "trace_id": "b0a68d7e-72bc-4402-9bc5-c8e6a17b019a",
  "span_id": "e6a17b01-9bc5-4402-b0a6-8d7e72bc0011",
  "parent_span_id": "00000000-0000-0000-0000-000000000000",
  "message": "GET /api/v3/canvas/live 200 - 12.45ms",
  "context": {
    "method": "GET",
    "path": "/api/v3/canvas/live",
    "client_ip": "127.0.0.1",
    "status_code": 200,
    "duration_ms": 12.45
  }
}
```

## 2. Distributed Tracing Propagation Patterns

### A. HTTP Entrypoint (`X-Trace-ID`)
- **FastAPI / Starlette Middleware**:
  1. Inspect `request.headers.get("x-trace-id") or request.headers.get("X-Trace-ID")`.
  2. If missing, generate `str(uuid.uuid4())`.
  3. Set ContextVar `set_trace_id(trace_id)`.
  4. Generate root `span_id = set_span_id()`.
  5. Compute `duration_ms = round((time.perf_counter() - start_time) * 1000, 2)`.
  6. Return `response.headers["X-Trace-ID"] = trace_id`.
  7. In `finally` block: `clear_context()` to prevent task pollution.

### B. WebSocket Room Multiplexing
- **Connection Handshake**:
  1. Generate unique `trace_id` upon WebSocket upgrade.
  2. Emit `CONNECTED` frame to client carrying `{"trace_id": trace_id}`.
- **Message Loop**:
  1. If client frame contains `"trace_id"`, adopt it via `set_trace_id(data["trace_id"])`.
  2. If client frame omits `"trace_id"`, inject current connection `trace_id`.
  3. Ensure server broadcast payloads include `"trace_id"`.
  4. Log `CONNECT`, `MESSAGE`, `ERROR`, `DISCONNECT` events with structured logger.

### C. Nested Spans (Parent-Child Hierarchy)
- Support both sync (`with trace_span("operation")`) and async (`async with trace_span("operation")`).
- Child span sets `parent_span_id` to the previous active `span_id`.
- On exit, previous parent and span IDs are restored in the ContextVar stack.

## 3. Log Ingestion Stack Setup

### Grafana Loki (via Promtail / Docker Logging Driver)
```yaml
clients:
  - url: http://loki:3100/loki/api/v1/push
scrape_configs:
  - job_name: dnk_containers
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
    pipeline_stages:
      - json:
          expressions:
            timestamp: timestamp
            level: level
            service: service
            trace_id: trace_id
            span_id: span_id
            message: message
      - labels:
          level:
          service:
          trace_id:
```

### ElasticSearch / Logstash
```text
filter {
  json {
    source => "message"
  }
  date {
    match => ["timestamp", "ISO8601"]
    target => "@timestamp"
  }
}
```
