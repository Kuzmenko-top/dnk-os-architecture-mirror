# Distributed Tracing & W3C Trace Context Propagation

Standard patterns for implementing OpenTelemetry-compliant distributed tracing, W3C traceparent formatting, tail sampling, context injection/extraction, and causal span relationships across FastAPI, event stream buses, and multi-agent systems.

## 1. W3C Trace Context Specification

The W3C Trace Context header standard (`traceparent`) format:
`00-{trace_id_32hex}-{span_id_16hex}-{trace_flags_2hex}`

- **Version**: `00` (current W3C specification).
- **Trace ID**: 16 bytes (32 hexadecimal characters). Unique per distributed operation tree.
- **Span ID / Parent ID**: 8 bytes (16 hexadecimal characters). Identifies the immediate parent or current segment.
- **Trace Flags**: 1 byte (2 hexadecimal characters, e.g. `01` for sampled, `00` for not sampled).

### Header Serialization & Deserialization

```python
import re
from typing import Optional, Tuple

W3C_TRACEPARENT_REGEX = re.compile(r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$", re.IGNORECASE)

def format_w3c_traceparent(trace_id: str, span_id: str, sampled: bool = True) -> str:
    flags = "01" if sampled else "00"
    return f"00-{trace_id.lower()}-{span_id.lower()}-{flags}"

def parse_w3c_traceparent(header_value: str) -> Optional[Tuple[str, str, str]]:
    if not header_value:
        return None
    match = W3C_TRACEPARENT_REGEX.match(header_value.strip())
    if not match:
        return None
    _, trace_id, span_id, flags = match.groups()
    if trace_id == "0" * 32 or span_id == "0" * 16:
        return None
    return trace_id, span_id, flags
```

## 2. Core ORM & Domain Models

1. **TraceSpan**:
   - `trace_id` (32 hex), `span_id` (16 hex), `parent_span_id` (optional 16 hex).
   - `service_name`, `name` (operation), `kind` (`SERVER`, `CLIENT`, `PRODUCER`, `CONSUMER`, `INTERNAL`).
   - `status_code` (`OK`, `ERROR`, `UNSET`), `duration_ms`, `start_time`, `end_time`.
   - `attributes` (JSON map), `events` (JSON list), `links` (JSON list), `is_root` (bool).
2. **TraceService**:
   - Registry for tracking topology services, versioning, environment, runtime stack, and health.
3. **TraceContext**:
   - W3C context encapsulation with `baggage`, `trace_state`, and `sampled` state.
4. **SpanEvent**:
   - Timestamped in-span annotations (e.g. exception logs, checkpoint markers).
5. **SpanLink**:
   - Causal relationships across batch processing, async stream message consumption, or cross-agent handoffs (`relationship_type`: `CAUSAL`, `BATCH_ITEM`, `ASYNC_FOLLOW`).
6. **TraceMetricAggregation**:
   - Time-bucketed latency percentiles (`p50_ms`, `p95_ms`, `p99_ms`), throughput (`call_count`), and `error_rate`.

## 3. Auto-Instrumentation & Contextvars Storage

### Context-Local Task Storage (`contextvars`)

```python
from contextvars import ContextVar
from typing import Optional

current_trace_context: ContextVar[Optional[TraceContext]] = ContextVar("current_trace_context", default=None)
current_span: ContextVar[Optional[TraceSpan]] = ContextVar("current_span", default=None)

def get_current_trace_context() -> Optional[TraceContext]:
    return current_trace_context.get()

def get_current_span() -> Optional[TraceSpan]:
    return current_span.get()
```

### Context Manager & Dual Sync/Async Decorator Pattern

```python
import time
import functools
import inspect
from typing import Optional, Dict, Any, Callable

class TraceContextManager:
    """Supports both synchronous/asynchronous context managers and function decorators."""
    def __init__(self, name: str, service_name: Optional[str] = None, kind: str = "INTERNAL", collector=None):
        self.name = name
        self.service_name = service_name
        self.kind = kind
        self.collector = collector
        self.span: Optional[TraceSpan] = None
        self._start_time: float = 0.0

    def __enter__(self) -> TraceSpan:
        self._start_time = time.time()
        parent = get_current_span()
        ctx = get_current_trace_context()
        trace_id = ctx.trace_id if ctx else TraceSpan.generate_trace_id()
        parent_id = parent.span_id if parent else (ctx.span_id if ctx else None)
        
        self.span = TraceSpan(
            trace_id=trace_id,
            span_id=TraceSpan.generate_span_id(),
            parent_span_id=parent_id,
            name=self.name,
            service_name=self.service_name or (parent.service_name if parent else "app"),
            kind=self.kind,
            is_root=parent_id is None,
        )
        self._token = current_span.set(self.span)
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.span:
            return
        duration_ms = (time.time() - self._start_time) * 1000.0
        self.span.duration_ms = round(duration_ms, 3)
        if exc_type is not None:
            self.span.status_code = "ERROR"
            self.span.add_event("exception", {"exception.type": exc_type.__name__, "exception.message": str(exc_val)})
        else:
            if self.span.status_code == "UNSET":
                self.span.status_code = "OK"
        if self.collector:
            self.collector.ingest_span(self.span)
        current_span.reset(self._token)

    async def __aenter__(self) -> TraceSpan:
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return self.__exit__(exc_type, exc_val, exc_tb)

    def __call__(self, func: Callable) -> Callable:
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                async with self:
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)
            return sync_wrapper
```

### FastAPI / Starlette Middleware

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class TraceContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, service_name: str = "api_gateway", collector=None):
        super().__init__(app)
        self.service_name = service_name
        self.collector = collector

    async def dispatch(self, request: Request, call_next) -> Response:
        traceparent = request.headers.get("traceparent")
        parsed = parse_w3c_traceparent(traceparent) if traceparent else None
        
        trace_id = parsed[0] if parsed else TraceSpan.generate_trace_id()
        parent_span_id = parsed[1] if parsed else None
        span_id = TraceSpan.generate_span_id()
        
        ctx = TraceContext(trace_id=trace_id, span_id=span_id, sampled=True)
        token_ctx = current_trace_context.set(ctx)
        
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=f"{request.method} {request.url.path}",
            service_name=self.service_name,
            kind="SERVER",
            is_root=parent_span_id is None,
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.client_ip": request.client.host if request.client else "",
            }
        )
        token_span = current_span.set(span)
        start_time = time.time()
        
        try:
            response = await call_next(request)
            span.duration_ms = round((time.time() - start_time) * 1000.0, 3)
            span.status_code = "OK" if response.status_code < 400 else "ERROR"
            span.attributes["http.status_code"] = response.status_code
            response.headers["traceparent"] = ctx.to_w3c_traceparent()
            return response
        except Exception as exc:
            span.duration_ms = round((time.time() - start_time) * 1000.0, 3)
            span.status_code = "ERROR"
            span.add_event("exception", {"exception.type": type(exc).__name__, "exception.message": str(exc)})
            raise
        finally:
            if self.collector:
                self.collector.ingest_span(span)
            current_span.reset(token_span)
            current_trace_context.reset(token_ctx)
```

## 4. Multi-Channel Context Propagation Invariants

- **HTTP Requests**: Inject and extract `traceparent`, `tracestate`, and `baggage` headers across FastAPI middlewares and outgoing HTTP client requests.
- **Event Streams (EventStreamBus)**: Inject `traceparent` and context dictionary into event message metadata envelope upon publishing (`PRODUCER`), and extract when consumer worker groups receive and process the message (`CONSUMER`).
- **A2A Agent Protocols**: Propagate trace context inside `A2AMessageEnvelope` or task context metadata so agent-to-agent delegations and swarm worker executions form an unbroken distributed trace DAG.
