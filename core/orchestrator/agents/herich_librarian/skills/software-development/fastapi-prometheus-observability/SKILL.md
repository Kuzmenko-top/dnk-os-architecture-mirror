---
name: fastapi-prometheus-observability
description: "Use when instrumenting FastAPI apps with Prometheus metrics."
version: 1.0.0
author: Gerych Core + Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [prometheus, grafana, metrics, fastapi, observability, monitoring]
    category: software-development
    requires_toolsets: [terminal]
---

# FastAPI Prometheus Metrics & Observability

Standard guide for architecting, instrumenting, and exposing Prometheus metrics in FastAPI applications and multi-agent systems.

## When to Use

Use this skill when:
- Instrumenting REST APIs or background workers with Prometheus counters, gauges, and histograms.
- Tracking request latency, active in-flight requests, and HTTP status distributions.
- Measuring multi-agent task execution time, swarm queue depth, and LLM/RAG latency.
- Exposing the `/metrics` endpoint with official Prometheus content types.
- Testing metrics collectors and decorators in unit/integration test suites.

## Core Architecture

### 1. Metric Types & Standard Taxonomy

- **Counter (`Counter`)**: Monotonically increasing values (e.g. `api_requests_total`, `agent_tasks_total`, `errors_total`). Labels: `endpoint`, `method`, `status`, `agent_type`.
- **Gauge (`Gauge`)**: Values that fluctuate up and down (e.g. `active_requests_in_progress`, `queue_depth`, `memory_usage_bytes`). Labels: `queue_name`, `service`.
- **Histogram (`Histogram`)**: Distribution of values across buckets (e.g. `request_latency_seconds`, `rag_query_latency_seconds`). Choose buckets matching expected SLOs (e.g. `(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)`).

### 2. Async Decorator Pattern

Wrap async endpoints and service functions cleanly to capture start/finish/error counts and latency:

```python
import time
from functools import wraps
from typing import Callable, Any
from prometheus_client import Counter, Histogram, Gauge, REGISTRY, generate_latest, CONTENT_TYPE

REQUEST_COUNT = Counter('app_requests_total', 'Total requests', ['endpoint', 'method', 'status'])
REQUEST_LATENCY = Histogram('app_request_latency_seconds', 'Request latency', ['endpoint', 'method'])
ACTIVE_REQUESTS = Gauge('app_requests_in_progress', 'Active requests', ['endpoint'])

def track_request(endpoint: str, method: str = 'GET'):
    """Decorator to track async request metrics."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            ACTIVE_REQUESTS.labels(endpoint=endpoint).inc()
            REQUEST_COUNT.labels(endpoint=endpoint, method=method, status='started').inc()
            
            start_time = time.time()
            status = 'success'
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                status = 'error'
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_LATENCY.labels(endpoint=endpoint, method=method).observe(duration)
                REQUEST_COUNT.labels(endpoint=endpoint, method=method, status=status).inc()
                ACTIVE_REQUESTS.labels(endpoint=endpoint).dec()
        return wrapper
    return decorator
```

### 3. Exposing `/metrics` in FastAPI

Avoid returning plain JSON or text without the official Prometheus media type:

```python
from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(REGISTRY).decode("utf-8"),
        media_type=CONTENT_TYPE
    )
```

## Prometheus & Grafana Infrastructure Setup

### 1. Prometheus Scrape Configuration (`prometheus.yml`)

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api'
    static_configs:
      - targets: ['api-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    scrape_timeout: 5s

rule_files:
  - 'rules/*.yml'
```

### 2. Pre-Computed Recording Rules (`rules/recording_rules.yml`)

Compute quantiles and rates ahead of time to avoid heavy query load on Grafana dashboards:

```yaml
groups:
  - name: api_latency_rules
    interval: 15s
    rules:
      - record: api:requests_per_second:rate5m
        expr: sum(rate(app_requests_total[5m])) by (endpoint)
      - record: api:latency_p95:histogram_quantile
        expr: histogram_quantile(0.95, sum(rate(app_request_latency_seconds_bucket[5m])) by (le, endpoint))
```

### 3. Alerting Rules (`rules/alerting_rules.yml`) & Alertmanager (`alertmanager/alertmanager.yml`)

Configure actionable alert rules with distinct severity levels (`critical`, `warning`) and route them via Alertmanager (see starter templates `templates/alerting_rules.yml` and `templates/alertmanager.yml`):

```yaml
groups:
  - name: api_alerts
    interval: 15s
    rules:
      - alert: HighAPILatency
        expr: api:latency_p95:histogram_quantile > 2.0
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: "High API latency on endpoint"
          description: "API P95 latency is above 2.0s for >5m."
```

Connect Alertmanager in `prometheus.yml`:
```yaml
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['dnk-alertmanager:9093']
```

Verify loaded rules and alertmanager runtime status:
- Prometheus rules: `curl -s http://localhost:9090/api/v1/rules | jq .`
- Alertmanager status: `curl -s http://localhost:9093/api/v1/status | jq .`

### 4. Automated Grafana Provisioning

- **Datasource Provisioning (`grafana/provisioning/datasources/prometheus.yml`)**:
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://dnk-prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
      httpMethod: POST
```
- **Dashboard Provisioning (`grafana/provisioning/dashboards/dashboards.yml`)**:
```yaml
apiVersion: 1
providers:
  - name: 'App Dashboards'
    orgId: 1
    folder: 'Observability'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /etc/grafana/dashboards
```

## Testing & Verification Protocol

### 1. Testing Metrics in Pytest

```python
import pytest

@pytest.mark.asyncio
async def test_metrics_collection():
    @track_request(endpoint="/api/v1/test", method="GET")
    async def endpoint():
        return {"ok": True}

    res = await endpoint()
    assert res == {"ok": True}
    
    metrics_text = generate_latest(REGISTRY).decode("utf-8")
    assert "app_requests_total" in metrics_text
    assert "app_request_latency_seconds" in metrics_text
```

## Advanced Streaming Anomaly Detection, Auto-Healing & Dynamic Alerting

For real-time anomaly detection algorithms (Z-Score, IQR, Holt-Winters, Isolation Forest), dynamic threshold auto-tuning, flap detection, auto-healing playbooks, safety circuit breakers, composite rules (`AND`/`OR`), and multi-channel notification dispatchers (Telegram, Slack, PagerDuty, Email), see [references/real_time_anomaly_detection_and_alerting.md](references/real_time_anomaly_detection_and_alerting.md).

## OpenTelemetry Distributed Tracing & W3C Trace Context

For distributed tracing architecture, W3C `traceparent` context serialization, span causal links, and cross-service/A2A trace propagation, see [references/distributed_tracing_and_w3c_context.md](references/distributed_tracing_and_w3c_context.md).

## Pitfalls & Best Practices

1. **Multi-Virtualenv Dependency Drift**: When working in monorepos or multi-service projects with separate `.venv` paths (e.g. root `.venv` vs `.venv`), ensure `prometheus-client` is installed in all active environments used by test runners and CI verification scripts.
2. **Label Cardinality Explosion**: Avoid using dynamic UUIDs, customer IDs, or raw query parameters in Prometheus labels. Keep label values strictly bounded (e.g. static route paths `/api/v1/users/{id}`, HTTP methods, status codes).
3. **Double Registration in Unit Tests**: Defining Prometheus metric objects at module import level registers them with the default `REGISTRY`. In test suites, do not re-instantiate identical metrics dynamically inside test functions.
