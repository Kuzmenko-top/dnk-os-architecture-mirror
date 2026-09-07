# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/specs/DNK-OBSERVE-001_distributed_tracing_observability_spec.md"
# purpose: "TaskDNA Architecture Specification & Implementation Plan for Distributed Tracing & Observability Platform (DNK-OBSERVE-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# DNK-OBSERVE-001: Distributed Tracing & Observability Platform Specification

## 1. Executive Summary & Goals
DNK-OBSERVE-001 establishes an enterprise-grade, OpenTelemetry-compliant Distributed Tracing and Observability Platform across the DNK OS ecosystem. It provides end-to-end correlation across REST APIs, A2A Mesh Agent Protocols (DNK-A2A-004), Real-Time Event Streaming Bus (DNK-STREAM-001), Auto-Healing Watchdogs (DNK-HEALTH-001), and ClickHouse Analytics OLAP.

### Key Architectural Invariants:
1. **W3C Trace Context Standard**: Strict adherence to W3C `traceparent` (`version-trace_id-parent_id-trace_flags`) and `tracestate` propagation.
2. **High-Throughput Spans & Low-Overhead**: Async in-memory ring-buffer collection with configurable batch processor and tail sampling.
3. **Multi-Service & Swarm Observability**: First-class tracking of agent reasoning steps, stream message hops, and cross-mesh A2A negotiations.
4. **Zero-Waste Quality Gate**: 100% test coverage, strict MRH compliance, and full regression pass.

---

## 2. TaskDNA Evolutionary DAG

```
[Phase 1: TaskDNA & Core Models] (DNK-OBSERVE-001-P1)
  ├── 1.1 TaskDNA Spec & Architecture Blueprint
  └── 1.2 6 ORM Models (TraceSpan, TraceService, TraceContext, SpanEvent, SpanLink, TraceMetricAggregation)
           │
           ▼
[Phase 2: OpenTelemetry Collector & Trace Engine] (DNK-OBSERVE-001-P2)
  ├── 2.1 OTLP Exporter & In-Memory Span Buffer
  ├── 2.2 Trace Context Propagator (W3C Header injection/extraction)
  └── 2.3 Tail Sampling & Latency Aggregator
           │
           ▼
[Phase 3: Service Auto-Instrumentation & Cross-System Correlation] (DNK-OBSERVE-001-P3)
  ├── 3.1 FastAPI Middleware & Database Tracer
  ├── 3.2 Event Stream Bus (DNK-STREAM-001) Trace Context Hop Injection
  └── 3.3 A2A Mesh Agent (DNK-A2A-004) Trace Envelope Injection
           │
           ▼
[Phase 4: Observability REST Router, Grafana Export & Evidence] (DNK-OBSERVE-001-P4)
  ├── 4.1 Trace Search, Span Tree & Service Topology REST API
  ├── 4.2 Latency Heatmaps & Health Alerting Correlation
  └── 4.3 Evidence Package & PR #50
```

---

## 3. Core Data Contracts (Phase 1 Models)

1. **`TraceSpan`**:
   - `id`: `spn_...` (16-hex character span identifier or uuid prefix)
   - `trace_id`: 32-hex character W3C trace ID
   - `parent_span_id`: Optional parent span ID for span tree hierarchy
   - `service_name`: Name of generating microservice/agent
   - `name`: Operation / endpoint / agent step name
   - `kind`: `SERVER`, `CLIENT`, `PRODUCER`, `CONSUMER`, `INTERNAL`
   - `status_code`: `OK`, `ERROR`, `UNSET`
   - `status_message`: Optional error description
   - `start_time`, `end_time`, `duration_ms`: High-resolution microsecond timestamps
   - `attributes`: JSON KV dictionary (e.g. `http.status_code`, `stream.topic`, `a2a.agent_id`)
   - `events`: Array/JSON of time-stamped sub-events
   - `links`: Array/JSON of causal links
   - `is_root`: Boolean flag indicating root trace initiator

2. **`TraceService`**:
   - `name`: Unique service identifier (e.g., `dnk_stream_bus`, `a2a_mesh_agent`, `api_gateway`)
   - `environment`: `production`, `staging`, `development`
   - `version`: Version string (e.g. `5.0.0`)
   - `runtime`: e.g. `Python 3.12 / FastAPI`
   - `health_status`: `HEALTHY`, `DEGRADED`, `CRITICAL`
   - `last_seen`: Timestamp of most recent span activity

3. **`TraceContext`**:
   - `trace_id`: 32-hex characters
   - `span_id`: 16-hex characters
   - `trace_flags`: Hex flag byte (e.g. `01` for sampled)
   - `trace_state`: W3C tracestate string
   - `baggage`: Correlation baggage dictionary for cross-cutting business metadata

4. **`SpanEvent`**:
   - `id`: `spe_...`
   - `span_id`: Bound span ID
   - `name`: Event name (e.g., `exception`, `cache_miss`, `rebalance_started`)
   - `timestamp`: Event occurrence time
   - `attributes`: Event attributes dictionary

5. **`SpanLink`**:
   - `id`: `spl_...`
   - `source_span_id`: Local span ID
   - `linked_trace_id`: Target trace ID
   - `linked_span_id`: Target span ID
   - `attributes`: Link metadata (e.g., `relationship: batch_item`)

6. **`TraceMetricAggregation`**:
   - `id`: `tma_...`
   - `service_name`: Monitored service
   - `operation`: Specific span operation name
   - `time_bucket`: Aggregation time window (e.g. 1-minute bucket)
   - `call_count`: Total requests in window
   - `error_count`: Total failed spans in window
   - `p50_ms`, `p95_ms`, `p99_ms`: Latency percentiles
   - `min_ms`, `max_ms`: Latency bounds
