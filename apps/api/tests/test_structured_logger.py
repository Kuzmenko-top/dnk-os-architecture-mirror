# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_tests_test_structured_logger"
# purpose: "Test runner and aliases for structured logger and distributed tracing"
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

from apps.api.tests.test_tracing import (
    test_json_formatter_valid_structure,
    test_structured_logger_levels_and_payload,
    test_trace_span_parent_child,
    test_trace_span_async_support,
    test_contextvars_async_isolation,
    test_http_middleware_trace_propagation,
    test_http_middleware_generates_new_uuid_when_omitted,
    test_websocket_broadcast_trace_injection,
    test_clear_context_resets_all_vars,
    test_json_log_validation_verification_command,
)

__all__ = [
    "test_json_formatter_valid_structure",
    "test_structured_logger_levels_and_payload",
    "test_trace_span_parent_child",
    "test_trace_span_async_support",
    "test_contextvars_async_isolation",
    "test_http_middleware_trace_propagation",
    "test_http_middleware_generates_new_uuid_when_omitted",
    "test_websocket_broadcast_trace_injection",
    "test_clear_context_resets_all_vars",
    "test_json_log_validation_verification_command",
]
