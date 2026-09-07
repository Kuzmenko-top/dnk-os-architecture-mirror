# --- DNK-MRH-HEADER ---
# mrh_id: "tests/harness/test_tool_guard_pipeline.py"
# purpose: "Unit tests for 5-Stage Guarded Tool Execution Pipeline assimilated from deepseek-harness"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import asyncio
import pytest
from core.security.tool_guard_pipeline import (
    ToolGuardPipeline,
    ToolExecutionContext,
    ToolPipelineOutput,
)


@pytest.mark.asyncio
async def test_tool_guard_pipeline_normal_execution():
    pipeline = ToolGuardPipeline()

    def sample_tool(text: str) -> str:
        return f"Echo: {text}"

    ctx = ToolExecutionContext(
        tool_name="echo_tool",
        arguments={"text": "hello DNK OS"},
    )

    output = await pipeline.execute_tool(ctx, sample_tool)
    assert output.success is True
    assert output.result == "Echo: hello DNK OS"
    assert output.truncated is False
    assert len(pipeline.observation_log) == 1
    assert pipeline.observation_log[0]["tool_name"] == "echo_tool"


@pytest.mark.asyncio
async def test_tool_guard_pipeline_pre_execute_block_dangerous_command():
    pipeline = ToolGuardPipeline()

    def terminal_mock(command: str) -> str:
        return "executed"

    ctx = ToolExecutionContext(
        tool_name="terminal",
        arguments={"command": "rm -rf /"},
    )

    output = await pipeline.execute_tool(ctx, terminal_mock)
    assert output.success is False
    assert output.error is not None
    assert "Pre-execute denied" in output.error
    assert "Dangerous command" in output.error


@pytest.mark.asyncio
async def test_tool_guard_pipeline_guard_blocks_env_tampering():
    pipeline = ToolGuardPipeline(disallow_env_mutation=True)

    def write_file_mock(path: str, content: str) -> str:
        return "ok"

    ctx = ToolExecutionContext(
        tool_name="write_file",
        arguments={"path": ".env", "content": "SECRET_KEY=123"},
    )

    output = await pipeline.execute_tool(ctx, write_file_mock)
    assert output.success is False
    assert output.error is not None
    assert "Guard invariant violation" in output.error
    assert ".env" in output.error


@pytest.mark.asyncio
async def test_tool_guard_pipeline_guard_blocks_absolute_paths():
    pipeline = ToolGuardPipeline(enforce_relative_paths=True)

    def read_file_mock(path: str) -> str:
        return "content"

    abs_path = f"/{'Users'}/kuzmenko.top/secret.txt"
    ctx = ToolExecutionContext(
        tool_name="read_file",
        arguments={"path": abs_path},
    )

    output = await pipeline.execute_tool(ctx, read_file_mock)
    assert output.success is False
    assert output.error is not None
    assert f"Absolute path '{abs_path}' rejected" in output.error


@pytest.mark.asyncio
async def test_tool_guard_pipeline_timeout_handling():
    pipeline = ToolGuardPipeline(execution_timeout_sec=0.05)

    async def slow_async_tool() -> str:
        await asyncio.sleep(0.2)
        return "slow"

    ctx = ToolExecutionContext(
        tool_name="slow_tool",
        arguments={},
    )

    output = await pipeline.execute_tool(ctx, slow_async_tool)
    assert output.success is False
    assert output.error is not None
    assert "timed out after" in output.error


@pytest.mark.asyncio
async def test_tool_guard_pipeline_head_tail_truncation():
    pipeline = ToolGuardPipeline(max_output_chars=500)

    def huge_tool() -> str:
        return "A" * 2000

    ctx = ToolExecutionContext(
        tool_name="huge_tool",
        arguments={},
    )

    output = await pipeline.execute_tool(ctx, huge_tool)
    assert output.success is True
    assert output.truncated is True
    assert "TRUNCATED" in output.result
    assert len(output.result) < 600
    assert output.original_size_bytes == 2000
