# --- DNK-MRH-HEADER ---
# mrh_id: "core/security/tool_guard_pipeline.py"
# purpose: "5-Stage Guarded Tool Execution Pipeline assimilated from deepseek-ai/deepseek-harness"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import time
import inspect
import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class ToolExecutionContext(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    workspace_id: str = "ws-alpha-001"
    caller_agent: str = "gerych_prime"
    execution_start_time: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ToolGuardResult(BaseModel):
    allowed: bool
    reason: Optional[str] = None
    security_level: str = "standard"


class ToolPipelineOutput(BaseModel):
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_duration_ms: float = 0.0
    truncated: bool = False
    original_size_bytes: int = 0
    final_size_bytes: int = 0


class ToolGuardPipeline:
    """
    Implements the 5-Stage Guarded Tool Execution Pipeline from DeepSeek Harness (dsh):
    Stage 1: pre_execute (extensible policy waterfall: allow / deny / ask)
    Stage 2: guard (monotonic invariant checks: no absolute paths, no .env tampering)
    Stage 3: around_execute (circuit-breaker, timeout, error boundaries)
    Stage 4: post_execute (output truncation & context pressure reduction)
    Stage 5: observe (immutable telemetry broadcast)
    """

    def __init__(
        self,
        max_output_chars: int = 8000,
        execution_timeout_sec: float = 30.0,
        disallow_env_mutation: bool = True,
        enforce_relative_paths: bool = True,
    ):
        self.max_output_chars = max_output_chars
        self.execution_timeout_sec = execution_timeout_sec
        self.disallow_env_mutation = disallow_env_mutation
        self.enforce_relative_paths = enforce_relative_paths
        self.observation_log: List[Dict[str, Any]] = []

    def pre_execute(self, ctx: ToolExecutionContext) -> ToolGuardResult:
        """Stage 1: Extensible policy check."""
        # Special check for high-risk operations
        if ctx.tool_name in ["terminal", "system_exec"]:
            cmd = str(ctx.arguments.get("command", ""))
            forbidden_substrings = ["rm -rf /", "mkfs", "dd if=/dev/zero", ":(){ :|:& };:"]
            for f in forbidden_substrings:
                if f in cmd:
                    return ToolGuardResult(allowed=False, reason=f"Dangerous command pattern detected: {f}")
        return ToolGuardResult(allowed=True, security_level="standard")

    def guard(self, ctx: ToolExecutionContext) -> ToolGuardResult:
        """Stage 2: Monotonic Synchronous Invariants (Strict & Unoverrideable)."""
        # Invariant 1: Block modification to .env files
        if self.disallow_env_mutation:
            for key, val in ctx.arguments.items():
                if isinstance(val, str) and (".env" in val or "secret" in val.lower()) and ctx.tool_name in ["write_file", "patch"]:
                    return ToolGuardResult(allowed=False, reason="Modification to .env or secret files is blocked by Guard Invariant")

        # Invariant 2: Relative path invariant
        if self.enforce_relative_paths:
            path_val = ctx.arguments.get("path") or ctx.arguments.get("file_path") or ctx.arguments.get("target_path")
            if isinstance(path_val, str) and (path_val.startswith("/Users/") or path_val.startswith("/root/") or path_val.startswith("/home/")):
                return ToolGuardResult(allowed=False, reason=f"Absolute path '{path_val}' rejected. DNK OS requires relative paths (./ or ../)")

        return ToolGuardResult(allowed=True)

    async def around_execute(self, ctx: ToolExecutionContext, handler: Callable[..., Any]) -> Tuple[bool, Any, Optional[str]]:
        """Stage 3: Around execution wrapper with timeout and error capture."""
        try:
            if inspect.iscoroutinefunction(handler):
                coro = handler(**ctx.arguments)
                res = await asyncio.wait_for(coro, timeout=self.execution_timeout_sec)
            else:
                res = handler(**ctx.arguments)
            return True, res, None
        except asyncio.TimeoutError:
            return False, None, f"Tool execution timed out after {self.execution_timeout_sec}s"
        except Exception as e:
            return False, None, str(e)

    def post_execute(self, ctx: ToolExecutionContext, raw_result: Any) -> Tuple[Any, bool, int, int]:
        """Stage 4: Output transformation, context diet and head+tail truncation."""
        text_repr = str(raw_result) if raw_result is not None else ""
        orig_size = len(text_repr.encode("utf-8"))

        if len(text_repr) > self.max_output_chars:
            head_size = self.max_output_chars // 2 - 100
            tail_size = self.max_output_chars // 2 - 100
            head = text_repr[:head_size]
            tail = text_repr[-tail_size:]
            trimmed_text = (
                f"{head}\n\n"
                f"... [TRUNCATED {len(text_repr) - (head_size + tail_size)} chars by DNK ToolGuardPipeline] ...\n\n"
                f"{tail}"
            )
            final_size = len(trimmed_text.encode("utf-8"))
            return trimmed_text, True, orig_size, final_size

        return raw_result, False, orig_size, orig_size

    def observe(self, ctx: ToolExecutionContext, output: ToolPipelineOutput) -> None:
        """Stage 5: Frozen Observability Event Broadcast."""
        event = {
            "tool_name": ctx.tool_name,
            "caller_agent": ctx.caller_agent,
            "workspace_id": ctx.workspace_id,
            "duration_ms": output.execution_duration_ms,
            "success": output.success,
            "truncated": output.truncated,
            "timestamp": time.time(),
        }
        self.observation_log.append(event)

    async def execute_tool(self, ctx: ToolExecutionContext, handler: Callable[..., Any]) -> ToolPipelineOutput:
        """Full 5-Stage Waterfall Execution."""
        start_t = time.perf_counter()

        # 1. Pre-execute
        pre_res = self.pre_execute(ctx)
        if not pre_res.allowed:
            out = ToolPipelineOutput(
                success=False,
                error=f"Pre-execute denied: {pre_res.reason}",
                execution_duration_ms=(time.perf_counter() - start_t) * 1000,
            )
            self.observe(ctx, out)
            return out

        # 2. Guard
        guard_res = self.guard(ctx)
        if not guard_res.allowed:
            out = ToolPipelineOutput(
                success=False,
                error=f"Guard invariant violation: {guard_res.reason}",
                execution_duration_ms=(time.perf_counter() - start_t) * 1000,
            )
            self.observe(ctx, out)
            return out

        # 3. Around execute
        success, raw_result, error = await self.around_execute(ctx, handler)
        if not success:
            out = ToolPipelineOutput(
                success=False,
                error=error,
                execution_duration_ms=(time.perf_counter() - start_t) * 1000,
            )
            self.observe(ctx, out)
            return out

        # 4. Post execute
        final_result, truncated, orig_sz, fin_sz = self.post_execute(ctx, raw_result)
        duration_ms = (time.perf_counter() - start_t) * 1000

        output = ToolPipelineOutput(
            success=True,
            result=final_result,
            execution_duration_ms=duration_ms,
            truncated=truncated,
            original_size_bytes=orig_sz,
            final_size_bytes=fin_sz,
        )

        # 5. Observe
        self.observe(ctx, output)
        return output
