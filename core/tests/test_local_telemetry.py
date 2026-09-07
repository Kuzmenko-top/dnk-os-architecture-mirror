# --- DNK-MRH-HEADER ---
# mrh_id: "core/tests/test_local_telemetry.py"
# purpose: "Comprehensive Unit and Integration Tests for LocalTelemetryEngine."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-06"
# --- END DNK-MRH-HEADER ---

import os
import shutil
import pytest
from typing import Generator
from core.local_telemetry import LocalTelemetryEngine

TEST_DIR = "test_run_telemetry_temp"

@pytest.fixture(autouse=True)
def run_around_tests() -> Generator[None, None, None]:
    """Cleans and scaffolds the temporary test telemetry directory."""
    os.makedirs(TEST_DIR, exist_ok=True)
    yield
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR, ignore_errors=True)


def test_local_telemetry_operations():
    engine = LocalTelemetryEngine(telemetry_dir=TEST_DIR, logs_dir=f"{TEST_DIR}/logs")

    # 1. Test log_trace and read_traces
    tool_calls = [{"tool": "test_tool", "arguments": {"x": 1}}]
    inputs = {"query": "test input"}
    outputs = {"result": "test output"}
    
    engine.log_trace("T_TRACE_1", tool_calls, inputs, outputs, duration_ms=150, cost_usd=0.002)
    
    traces = engine.read_traces("T_TRACE_1")
    assert len(traces) == 1
    assert traces[0]["task_id"] == "T_TRACE_1"
    assert traces[0]["duration_ms"] == 150
    assert traces[0]["cost_usd"] == 0.002
    assert traces[0]["tool_calls"] == tool_calls

    # Test reading non-existent trace
    assert engine.read_traces("NON_EXISTENT") == []

    # 2. Test log_trajectory and read_trajectory
    steps = [{"action": "init"}, {"action": "execute", "status": "ok"}]
    engine.log_trajectory("T_TRACE_1", steps)
    
    trajectory = engine.read_trajectory("T_TRACE_1")
    assert trajectory is not None
    assert trajectory["task_id"] == "T_TRACE_1"
    assert len(trajectory["steps"]) == 2
    assert trajectory["steps"][0]["action"] == "init"

    # Test reading non-existent trajectory
    assert engine.read_trajectory("NON_EXISTENT") is None

    # 3. Test log_metric
    engine.log_metric("latency_ms", 12.5, tags=["fast", "local"])
    metric_file = os.path.join(engine.metrics_dir, "latency_ms_metrics.jsonl")
    assert os.path.exists(metric_file)

    # 4. Test log_step
    engine.log_step("test_module", "Testing step execution log", "WARNING")
    step_file = os.path.join(engine.logs_dir, "step_logs.jsonl")
    assert os.path.exists(step_file)
