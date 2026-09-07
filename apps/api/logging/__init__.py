# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_logging_init"
# purpose: "Package initialization for structured logging and distributed tracing"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

from apps.api.logging.structured_logger import (
    StructuredLogger,
    get_logger,
    structured_logger,
    get_trace_id,
    set_trace_id,
    get_span_id,
    set_span_id,
    get_parent_span_id,
    set_parent_span_id,
    bind_context,
    get_context,
    clear_context,
    trace_span,
)

__all__ = [
    "StructuredLogger",
    "get_logger",
    "structured_logger",
    "get_trace_id",
    "set_trace_id",
    "get_span_id",
    "set_span_id",
    "get_parent_span_id",
    "set_parent_span_id",
    "bind_context",
    "get_context",
    "clear_context",
    "trace_span",
]
