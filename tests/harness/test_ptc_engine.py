# --- DNK-MRH-HEADER ---
# mrh_id: "tests/harness/test_ptc_engine.py"
# purpose: "Unit tests for Programmatic Tool Calling (PTC) Engine assimilated from deepseek-harness"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import pytest
from core.executors.ptc.dnk_ptc_engine import DNKPTCEngine, PTCExecutionRequest


def test_ptc_engine_basic_script_execution():
    engine = DNKPTCEngine()

    def add(a: int, b: int) -> int:
        return a + b

    engine.register_tool("add", add)

    code = """
val1 = tools.call('add', a=10, b=25)
print(f"Calculated: {val1}")
result = val1 * 2
"""
    req = PTCExecutionRequest(code=code)
    resp = engine.execute_script(req)

    assert resp.success is True
    assert "Calculated: 35" in resp.stdout
    assert resp.return_value == 70
    assert resp.tool_calls_executed == 1


def test_ptc_engine_multi_tool_batch_execution():
    engine = DNKPTCEngine()

    storage = {}

    def set_key(key: str, value: str) -> str:
        storage[key] = value
        return "stored"

    def get_key(key: str) -> str:
        return storage.get(key, "")

    engine.register_tool("set_key", set_key)
    engine.register_tool("get_key", get_key)

    code = """
items = [('k1', 'v1'), ('k2', 'v2'), ('k3', 'v3')]
for k, v in items:
    tools.call('set_key', key=k, value=v)

res = [tools.call('get_key', key=k) for k, _ in items]
result = res
"""
    req = PTCExecutionRequest(code=code)
    resp = engine.execute_script(req)

    assert resp.success is True
    assert resp.tool_calls_executed == 6
    assert resp.return_value == ["v1", "v2", "v3"]


def test_ptc_engine_error_capture():
    engine = DNKPTCEngine()

    code = """
# Deliberate division by zero
x = 10 / 0
result = x
"""
    req = PTCExecutionRequest(code=code)
    resp = engine.execute_script(req)

    assert resp.success is False
    assert resp.error is not None
    assert "ZeroDivisionError" in resp.error
