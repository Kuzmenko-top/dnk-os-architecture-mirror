<!--
# --- DNK-MRH-HEADER ---
# mrh_id: "docs_logging_structured_logging"
# purpose: "Architecture specification, guide, and ELK/Loki integration for DNK OS Structured Logging and Distributed Tracing"
# standard: "DNK-STD-0080"
# author: "DNK-e.com Maksym / Gerych Prime"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# alters_files: []
# triggers_tasks: []
# canonical_source: true
# --- END DNK-MRH-HEADER ---
-->

# DNK OS Structured Logging & Distributed Tracing (DNK-STD-0080)

## 1. Overview & Architecture

DNK OS implements high-throughput, async-safe, JSON-structured logging and end-to-end distributed tracing across all system layers: HTTP endpoints, WebSocket real-time collaboration channels, internal background services, and Swarm multi-agent task executions.

### Tracing Flow Architecture

```
[ Client Request ]
       │
       ▼ (HTTP with optional X-Trace-ID)
┌──────────────────────────────────────────────┐
│ FastAPI HTTP Pipeline                        │
│ ├─ TraceMiddleware                           │
│ │   ├─ Extracts / Generates UUIDv4 Trace ID  │
│ │   ├─ Binds Trace ID to asyncio ContextVar  │
│ │   ├─ Injects into X-Trace-ID Response      │
│ │   └─ Logs HTTP access event with duration  │
└──────────────────────┬───────────────────────┘
                       │
       ┌───────────────┴───────────────┐
       ▼                               ▼
┌─────────────────────────┐  ┌─────────────────────────┐
│ WebSocket Subsystem     │  │ Swarm Agent Execution   │
│ (canvas_v3_ws.py)       │  │ (Task Context & Workers)│
│ ├─ Session Trace ID     │  │ ├─ Propagates Trace ID  │
│ ├─ Injects into Packets │  │ ├─ Parent / Child Spans │
│ └─ Logs CONNECT/DISC/MSG│  │ └─ Async Context Scopes │
└─────────────────────────┘  └─────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│ Structured Logger Engine                     │
│ (apps/api/logging/structured_logger.py)      │
│ ├─ ContextVar Storage (Trace ID, Span ID)   │
│ ├─ JSON Formatter (ISO 8601, Service Name)   │
│ └─ Thread-safe / Async-safe Stream Handler   │
└──────────────────────┬───────────────────────┘
                       │
                       ▼ (stdout / stderr)
┌──────────────────────────────────────────────┐
│ Log Aggregation: ELK Stack / Grafana Loki    │
└──────────────────────────────────────────────┘
```

---

## 2. Log Format Specification (JSON)

Every log emitted by `structured_logger` complies with the following JSON schema:

```json
{
  "timestamp": "2026-09-05T08:30:15.123456Z",
  "level": "INFO",
  "service": "dnk-api",
  "trace_id": "7f2e148b-3e51-4d37-883a-8cb9e53096b7",
  "span_id": "c1f7b029-9e7f-4315-bbbc-2144b611843b",
  "parent_span_id": null,
  "message": "GET /api/v1/health 200 - 1.25ms",
  "context": {
    "method": "GET",
    "path": "/api/v1/health",
    "status_code": 200
  },
  "duration_ms": 1.25
}
```

### Mandatory Fields
- `timestamp`: ISO 8601 UTC timestamp ending with `Z`.
- `level`: Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
- `service`: Identifier of the reporting component (`dnk-api` by default).
- `trace_id`: UUID v4 string representing the end-to-end request or event flow.
- `span_id`: UUID v4 string representing the current execution slice / unit of work.
- `message`: Human-readable summary string.
- `context`: JSON dictionary containing contextual parameters (e.g. `user_id`, `canvas_id`, `event_type`).
- `duration_ms`: Optional execution time in milliseconds.

---

## 3. Distributed Tracing Propagation

### A. HTTP Headers
- Header Name: `X-Trace-ID` (case-insensitive on ingress).
- When a request includes `X-Trace-ID`, DNK OS preserves and adopts it.
- If missing, `TraceMiddleware` generates a fresh UUID v4.
- All HTTP responses return the active `X-Trace-ID`.

### B. WebSocket Frames
- Handshake & `CONNECTED`: Server sends initial `trace_id` in connection payload.
- Inbound frames: Server inspects packet for `"trace_id"` field. If omitted, uses socket connection `trace_id`.
- Outbound broadcasts: `broadcast()` and `broadcast_except()` automatically stamp `"trace_id"` on all JSON payloads.
- Lifecycle logging: Structured logs record `CONNECT`, `DISCONNECT`, `MESSAGE`, and `ERROR` events.

### C. Nested Operations & Spans
Nested actions within a trace use `trace_span`:

```python
from apps.api.logging.structured_logger import trace_span, structured_logger

async def process_task(task_data: dict):
    async with trace_span("execute_swarm_node", agent="gerych_builder") as span_id:
        structured_logger.info("Starting subtask execution", task_id=task_data["id"])
        # Parent-child span relationship preserved in logs
```

---

## 4. Integration with Observability Stacks

### Grafana Loki / Promtail

Configure Promtail to parse the Docker/Kubernetes container logs as JSON:

```yaml
scrape_configs:
  - job_name: dnk-os-api
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
            duration_ms: duration_ms
            message: message
      - labels:
          level:
          service:
          trace_id:
      - timestamp:
          source: timestamp
          format: RFC3339Nano
```

#### LogQL Query Examples
- Filter logs for a specific trace:
  `{service="dnk-api"} | json | trace_id = "7f2e148b-3e51-4d37-883a-8cb9e53096b7"`
- Find slow HTTP requests (> 500ms):
  `{service="dnk-api"} | json | duration_ms > 500`
- Count errors by canvas_id:
  `sum by (canvas_id) (count_over_time({service="dnk-api"} | json | level = "ERROR" [5m]))`

### ELK Stack (Elasticsearch, Logstash, Kibana)

Configure Filebeat with JSON decode processor:

```yaml
filebeat.inputs:
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'
    processors:
      - decode_json_fields:
          fields: ["message"]
          target: ""
          overwrite_keys: true
```

In Elasticsearch / OpenSearch, fields `trace_id` and `span_id` are indexed as `keyword` for instant lookup and correlation with APM / Jaeger traces.
