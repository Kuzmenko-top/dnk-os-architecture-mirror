# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_logging_structured_logger"
# purpose: "Structured JSON logging and distributed tracing engine compatible with ELK and Loki stacks"
# standard: "DNK-STD-0080"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# alters_files: []
# triggers_tasks: []
# canonical_source: true
# --- END DNK-MRH-HEADER ---

import sys
import json
import time
import uuid
import logging
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Any, Dict, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variables for distributed tracing across async tasks
_trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_span_id_var: ContextVar[Optional[str]] = ContextVar("span_id", default=None)
_parent_span_id_var: ContextVar[Optional[str]] = ContextVar("parent_span_id", default=None)
_context_var: ContextVar[Dict[str, Any]] = ContextVar("context_dict", default={})

SERVICE_NAME = "dnk-api"


def get_trace_id() -> str:
    """Retrieve the current trace_id or generate a new UUID v4 if not set."""
    tid = _trace_id_var.get()
    if not tid:
        tid = str(uuid.uuid4())
        _trace_id_var.set(tid)
    return tid


def set_trace_id(trace_id: Optional[str] = None) -> str:
    """Set the current trace_id. If None, generates a new UUID v4."""
    if not trace_id:
        trace_id = str(uuid.uuid4())
    _trace_id_var.set(trace_id)
    return trace_id


def get_span_id() -> str:
    """Retrieve the current span_id or generate a new UUID v4 if not set."""
    sid = _span_id_var.get()
    if not sid:
        sid = str(uuid.uuid4())
        _span_id_var.set(sid)
    return sid


def set_span_id(span_id: Optional[str] = None) -> str:
    """Set the current span_id. If None, generates a new UUID v4."""
    if not span_id:
        span_id = str(uuid.uuid4())
    _span_id_var.set(span_id)
    return span_id


def get_parent_span_id() -> Optional[str]:
    """Retrieve parent_span_id if present."""
    return _parent_span_id_var.get()


def set_parent_span_id(parent_span_id: Optional[str]) -> None:
    """Set the parent span ID."""
    _parent_span_id_var.set(parent_span_id)


def get_context() -> Dict[str, Any]:
    """Get a copy of the current context dictionary."""
    return dict(_context_var.get())


def bind_context(**kwargs: Any) -> None:
    """Bind key-value pairs into the current context dictionary."""
    ctx = dict(_context_var.get())
    ctx.update(kwargs)
    _context_var.set(ctx)


def clear_context() -> None:
    """Reset the context variables for current async context."""
    _trace_id_var.set(None)
    _span_id_var.set(None)
    _parent_span_id_var.set(None)
    _context_var.set({})


class trace_span:
    """Dual sync/async context manager for nested operation tracing with parent-child span linkage."""

    def __init__(self, span_name: str, **kwargs: Any):
        self.span_name = span_name
        self.kwargs = kwargs
        self.old_span: Optional[str] = None
        self.old_parent: Optional[str] = None
        self.new_span: Optional[str] = None

    def __enter__(self) -> str:
        self.old_span = _span_id_var.get()
        self.old_parent = _parent_span_id_var.get()
        self.new_span = str(uuid.uuid4())

        _parent_span_id_var.set(self.old_span)
        _span_id_var.set(self.new_span)

        if self.kwargs:
            bind_context(**self.kwargs)

        return self.new_span

    def __exit__(self, exc_type, exc_val, exc_tb):
        _span_id_var.set(self.old_span)
        _parent_span_id_var.set(self.old_parent)

    async def __aenter__(self) -> str:
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.__exit__(exc_type, exc_val, exc_tb)


class JSONFormatter(logging.Formatter):
    """Standard logging.Formatter that outputs structured JSON for ELK / Loki."""

    def __init__(self, service_name: str = SERVICE_NAME):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        tid = get_trace_id()
        sid = get_span_id()
        pid = get_parent_span_id()

        merged_context = dict(_context_var.get())
        rec_context = getattr(record, "context", None)
        if isinstance(rec_context, dict):
            merged_context.update(rec_context)
        if pid and "parent_span_id" not in merged_context:
            merged_context["parent_span_id"] = pid

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self.service_name,
            "trace_id": tid,
            "span_id": sid,
            "message": record.getMessage(),
            "context": merged_context,
        }
        rec_duration = getattr(record, "duration_ms", None)
        if rec_duration is not None:
            payload["duration_ms"] = rec_duration
        return json.dumps(payload, default=str)


class StructuredLogger:
    """High-velocity async-safe JSON Structured Logger compatible with ELK & Loki."""

    def __init__(
        self,
        service: str = SERVICE_NAME,
        stream=None,
        service_name: Optional[str] = None,
    ):
        self.service = service_name or service
        self.stream = stream or sys.stdout
        self.logger = logging.getLogger(self.service)

    def _format_record(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        tid = get_trace_id()
        sid = get_span_id()
        pid = get_parent_span_id()

        merged_context = dict(_context_var.get())
        if extra:
            merged_context.update(extra)
        if kwargs:
            merged_context.update(kwargs)
        if pid and "parent_span_id" not in merged_context:
            merged_context["parent_span_id"] = pid

        record: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "service": self.service,
            "trace_id": tid,
            "span_id": sid,
            "message": str(message),
            "context": merged_context,
        }
        if "duration_ms" in merged_context:
            record["duration_ms"] = merged_context["duration_ms"]

        return record

    def log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> str:
        record = self._format_record(level, message, extra=extra, **kwargs)
        line = json.dumps(record, default=str)
        try:
            self.stream.write(line + "\n")
            self.stream.flush()
        except Exception:
            pass
        return line

    def info(self, message: str, **kwargs: Any) -> str:
        return self.log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> str:
        return self.log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> str:
        return self.log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> str:
        return self.log("CRITICAL", message, **kwargs)

    def debug(self, message: str, **kwargs: Any) -> str:
        return self.log("DEBUG", message, **kwargs)


# Global singleton instance
structured_logger = StructuredLogger()


def get_logger(name: Optional[str] = None) -> StructuredLogger:
    """Return a StructuredLogger instance bound to service name or component."""
    if name:
        return StructuredLogger(service=name)
    return structured_logger


class TraceMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware for distributed tracing with X-Trace-ID propagation."""

    async def dispatch(self, request: Request, call_next) -> Response:
        trace_id = (
            request.headers.get("x-trace-id")
            or request.headers.get("X-Trace-ID")
            or str(uuid.uuid4())
        )
        set_trace_id(trace_id)
        set_span_id()
        bind_context(method=request.method, path=request.url.path)
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Trace-ID"] = trace_id
            structured_logger.info(
                f"{request.method} {request.url.path} {response.status_code} - {duration_ms}ms",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            return response
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            structured_logger.error(
                f"{request.method} {request.url.path} ERROR - {duration_ms}ms: {exc}",
                error=str(exc),
                duration_ms=duration_ms,
            )
            raise exc
        finally:
            clear_context()
