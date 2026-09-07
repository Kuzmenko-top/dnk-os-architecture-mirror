# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/services/trace_instrumentation_service.py"
# purpose: "Distributed Trace Context Injection, W3C Propagation & Auto-Instrumentation Engine (DNK-OBSERVE-001)"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

import asyncio
import functools
import inspect
import re
import time
from contextvars import ContextVar
from typing import Any, Callable, Dict, List, Optional, Union
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from apps.api.db.models.trace_context import TraceContext
from apps.api.db.models.trace_span import TraceSpan
from apps.api.services.telemetry_collector_service import TelemetryCollectorService, get_default_collector

# Task-local ContextVars for active trace context and active span
current_trace_context: ContextVar[Optional[TraceContext]] = ContextVar("current_trace_context", default=None)
current_span: ContextVar[Optional[TraceSpan]] = ContextVar("current_span", default=None)


def get_current_trace_context() -> Optional[TraceContext]:
    """Retrieve the active W3C TraceContext in the current async/thread execution context."""
    return current_trace_context.get()


def set_current_trace_context(ctx: Optional[TraceContext]):
    """Set the active W3C TraceContext in the current async/thread execution context."""
    return current_trace_context.set(ctx)


def get_current_span() -> Optional[TraceSpan]:
    """Retrieve the active TraceSpan in the current async/thread execution context."""
    return current_span.get()


def set_current_span(span: Optional[TraceSpan]):
    """Set the active TraceSpan in the current async/thread execution context."""
    return current_span.set(span)


# --- W3C TRACE CONTEXT INJECTION & EXTRACTION ---

def inject_w3c_trace_context(carrier: Dict[str, Any], context: Optional[TraceContext] = None) -> Dict[str, Any]:
    """
    Inject W3C Trace Context (traceparent, tracestate, baggage) into a carrier dictionary or HTTP headers.
    """
    ctx = context or get_current_trace_context()
    if ctx is None:
        return carrier

    carrier["traceparent"] = ctx.traceparent
    if ctx.tracestate:
        carrier["tracestate"] = ctx.tracestate
    if ctx.baggage:
        carrier["baggage"] = ",".join(f"{k}={v}" for k, v in ctx.baggage.items())
    return carrier


def extract_w3c_trace_context(carrier: Dict[str, Any]) -> Optional[TraceContext]:
    """
    Extract W3C Trace Context from a carrier dictionary or HTTP headers.
    Supports case-insensitive lookups (e.g., 'traceparent' or 'Traceparent').
    """
    if not carrier:
        return None

    # Case-insensitive header dictionary lookup
    lookup = {str(k).lower(): v for k, v in carrier.items()}

    traceparent = lookup.get("traceparent")
    if not traceparent or not isinstance(traceparent, str):
        return None

    # W3C traceparent regex: 00-{32hex}-{16hex}-{2hex}
    match = re.match(r"^00-([0-9a-fA-F]{32})-([0-9a-fA-F]{16})-([0-9a-fA-F]{2})$", traceparent.strip())
    if not match:
        return None

    trace_id, parent_span_id, trace_flags = match.groups()
    tracestate = lookup.get("tracestate")

    baggage = {}
    baggage_header = lookup.get("baggage")
    if baggage_header and isinstance(baggage_header, str):
        for item in baggage_header.split(","):
            if "=" in item:
                k, v = item.strip().split("=", 1)
                baggage[k.strip()] = v.strip()

    sampled = bool(int(trace_flags, 16) & 1)

    return TraceContext(
        trace_id=trace_id.lower(),
        span_id=parent_span_id.lower(),
        parent_span_id=None,
        trace_flags=trace_flags,
        tracestate=tracestate,
        baggage=baggage,
        sampled=sampled,
    )


# --- EVENT STREAM BUS & A2A CONTEXT PROPAGATION ---

def inject_into_stream_message(event_data: Dict[str, Any], context: Optional[TraceContext] = None) -> Dict[str, Any]:
    """Inject W3C trace correlation fields into an Event Stream Bus event payload."""
    ctx = context or get_current_trace_context()
    if ctx:
        event_data["traceparent"] = ctx.traceparent
        if "metadata" not in event_data or not isinstance(event_data["metadata"], dict):
            event_data["metadata"] = {}
        event_data["metadata"]["trace_id"] = ctx.trace_id
        event_data["metadata"]["span_id"] = ctx.span_id
        if ctx.baggage:
            event_data["metadata"]["baggage"] = ctx.baggage
    return event_data


def extract_from_stream_message(event_data: Dict[str, Any]) -> Optional[TraceContext]:
    """Extract W3C Trace Context from an Event Stream Bus event payload."""
    if not isinstance(event_data, dict):
        return None
    # Check top-level traceparent or metadata dictionary
    ctx = extract_w3c_trace_context(event_data)
    if ctx:
        return ctx
    metadata = event_data.get("metadata", {})
    if isinstance(metadata, dict):
        return extract_w3c_trace_context(metadata)
    return None


def inject_into_a2a_envelope(envelope: Dict[str, Any], context: Optional[TraceContext] = None) -> Dict[str, Any]:
    """Inject W3C trace correlation fields into an A2A Agent communication envelope."""
    ctx = context or get_current_trace_context()
    if ctx:
        envelope["traceparent"] = ctx.traceparent
        if "metadata" not in envelope or not isinstance(envelope["metadata"], dict):
            envelope["metadata"] = {}
        envelope["metadata"]["trace_id"] = ctx.trace_id
        envelope["metadata"]["span_id"] = ctx.span_id
        if ctx.baggage:
            envelope["metadata"]["baggage"] = ctx.baggage
    return envelope


def extract_from_a2a_envelope(envelope: Dict[str, Any]) -> Optional[TraceContext]:
    """Extract W3C Trace Context from an A2A Agent communication envelope."""
    if not isinstance(envelope, dict):
        return None
    ctx = extract_w3c_trace_context(envelope)
    if ctx:
        return ctx
    metadata = envelope.get("metadata", {})
    if isinstance(metadata, dict):
        return extract_w3c_trace_context(metadata)
    return None


# --- CONTEXT MANAGER & DECORATOR: trace_span ---

class TraceSpanContextManager:
    """
    Unified Synchronous and Asynchronous Context Manager and Decorator for creating and tracking spans.
    """

    def __init__(
        self,
        name: str,
        service_name: Optional[str] = None,
        kind: str = "INTERNAL",
        attributes: Optional[Dict[str, Any]] = None,
        collector: Optional[TelemetryCollectorService] = None,
    ):
        self.name = name
        self.service_name = service_name or "dnk_service"
        self.kind = kind
        self.attributes = attributes or {}
        self.collector = collector or get_default_collector()
        self.span: Optional[TraceSpan] = None
        self._token_ctx = None
        self._token_span = None
        self._start_time = 0.0

    def _enter(self) -> TraceSpan:
        parent_ctx = get_current_trace_context()
        active_parent_span = get_current_span()

        parent_span_id = None
        if active_parent_span:
            parent_span_id = active_parent_span.span_id
            trace_id = active_parent_span.trace_id
        elif parent_ctx:
            parent_span_id = parent_ctx.span_id
            trace_id = parent_ctx.trace_id
        else:
            trace_id = TraceSpan.generate_trace_id()

        span_id = TraceSpan.generate_span_id()
        self.span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=self.name,
            service_name=self.service_name,
            kind=self.kind,
            attributes=dict(self.attributes),
            status_code="UNSET",
        )

        child_ctx = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage=parent_ctx.baggage.copy() if parent_ctx and parent_ctx.baggage else {},
        )

        self._token_ctx = set_current_trace_context(child_ctx)
        self._token_span = set_current_span(self.span)
        self._start_time = time.time()
        return self.span

    def _exit(self, exc_type, exc_val, exc_tb):
        if not self.span:
            return

        duration_ms = (time.time() - self._start_time) * 1000.0
        self.span.duration_ms = round(duration_ms, 3)

        if exc_type is not None:
            self.span.status_code = "ERROR"
            self.span.status_message = str(exc_val)
            self.span.add_event(
                name="exception",
                attributes={
                    "exception.type": exc_type.__name__,
                    "exception.message": str(exc_val),
                },
            )
        elif self.span.status_code == "UNSET":
            self.span.status_code = "OK"

        # Ingest to collector
        if self.collector:
            self.collector.ingest_span(self.span.to_dict())

        # Reset ContextVars
        if self._token_ctx:
            current_trace_context.reset(self._token_ctx)
        if self._token_span:
            current_span.reset(self._token_span)

    def __enter__(self) -> TraceSpan:
        return self._enter()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exit(exc_type, exc_val, exc_tb)

    async def __aenter__(self) -> TraceSpan:
        return self._enter()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._exit(exc_type, exc_val, exc_tb)

    def __call__(self, fn: Callable) -> Callable:
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args, **kwargs):
                async with self:
                    return await fn(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args, **kwargs):
                with self:
                    return fn(*args, **kwargs)
            return sync_wrapper


def trace_span(
    name: str,
    service_name: Optional[str] = None,
    kind: str = "INTERNAL",
    attributes: Optional[Dict[str, Any]] = None,
    collector: Optional[TelemetryCollectorService] = None,
) -> TraceSpanContextManager:
    """Helper creating a TraceSpanContextManager instance for context management or decoration."""
    return TraceSpanContextManager(
        name=name,
        service_name=service_name,
        kind=kind,
        attributes=attributes,
        collector=collector,
    )


# --- STARLETTE / FASTAPI TRACING MIDDLEWARE ---

class TraceContextMiddleware(BaseHTTPMiddleware):
    """
    FastAPI & Starlette Middleware for HTTP Request Tracing & W3C Propagation:
    - Extracts incoming W3C traceparent / baggage headers.
    - Creates and instruments root/child SERVER span for HTTP lifecycle.
    - Sets response headers with traceparent and traceresponse.
    - Forwards completed telemetry to the collector.
    """

    def __init__(
        self,
        app,
        service_name: str = "dnk_api_gateway",
        collector: Optional[TelemetryCollectorService] = None,
        exempt_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.service_name = service_name
        self.collector = collector or get_default_collector()
        self.exempt_paths = exempt_paths or ["/health", "/api/health", "/metrics", "/favicon.ico"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check exempt paths
        if any(request.url.path == p or request.url.path.startswith(p + "/") for p in self.exempt_paths):
            return await call_next(request)

        # Extract incoming W3C trace context from request headers
        headers_dict = dict(request.headers)
        extracted_ctx = extract_w3c_trace_context(headers_dict)

        trace_id = extracted_ctx.trace_id if extracted_ctx else TraceSpan.generate_trace_id()
        parent_span_id = extracted_ctx.span_id if extracted_ctx else None
        span_id = TraceSpan.generate_span_id()

        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            name=f"{request.method} {request.url.path}",
            service_name=self.service_name,
            kind="SERVER",
            attributes={
                "http.method": request.method,
                "http.url": str(request.url),
                "http.path": request.url.path,
                "http.client_ip": request.client.host if request.client else "unknown",
                "http.user_agent": request.headers.get("user-agent", ""),
            },
            status_code="UNSET",
        )

        child_ctx = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            baggage=extracted_ctx.baggage.copy() if extracted_ctx and extracted_ctx.baggage else {},
        )

        token_ctx = set_current_trace_context(child_ctx)
        token_span = set_current_span(span)
        start_time = time.time()

        try:
            response: Response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000.0
            span.duration_ms = round(duration_ms, 3)
            span.attributes["http.status_code"] = response.status_code

            if response.status_code >= 500:
                span.status_code = "ERROR"
                span.status_message = f"HTTP {response.status_code} Server Error"
            else:
                span.status_code = "OK"

            # Inject trace headers into response
            response.headers["traceparent"] = child_ctx.traceparent
            response.headers["x-trace-id"] = trace_id
            return response

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000.0
            span.duration_ms = round(duration_ms, 3)
            span.status_code = "ERROR"
            span.status_message = str(exc)
            span.add_event(
                name="exception",
                attributes={
                    "exception.type": exc.__class__.__name__,
                    "exception.message": str(exc),
                },
            )
            raise exc

        finally:
            if self.collector:
                self.collector.ingest_span(span.to_dict())
            current_trace_context.reset(token_ctx)
            current_span.reset(token_span)
