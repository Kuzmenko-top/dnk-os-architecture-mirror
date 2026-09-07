# --- DNK-MRH-HEADER ---
# mrh_id: "core/executors/ptc/dnk_ptc_engine.py"
# purpose: "Programmatic Tool Calling (PTC) Engine assimilated from deepseek-ai/deepseek-harness"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import sys
import io
import time
import traceback
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class PTCExecutionRequest(BaseModel):
    code: str
    workspace_id: str = "ws-alpha-001"
    timeout_sec: float = 30.0
    allowed_globals: Optional[List[str]] = None


class PTCExecutionResponse(BaseModel):
    success: bool
    stdout: str
    return_value: Any = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    tool_calls_executed: int = 0


class PTCToolsSDK:
    """
    In-memory dynamic SDK exposed to PTC scripts (e.g. `await tools.call(...)` or `tools.call(...)`).
    """
    def __init__(self, registered_tools: Dict[str, Callable[..., Any]]):
        self._registered_tools = registered_tools
        self.call_history: List[Dict[str, Any]] = []

    def call(self, tool_name: str, **kwargs) -> Any:
        if tool_name not in self._registered_tools:
            raise KeyError(f"PTC SDK: tool '{tool_name}' is not registered.")
        
        start_t = time.perf_counter()
        tool_fn = self._registered_tools[tool_name]
        result = tool_fn(**kwargs)
        duration_ms = (time.perf_counter() - start_t) * 1000
        
        self.call_history.append({
            "tool_name": tool_name,
            "args": kwargs,
            "duration_ms": duration_ms,
        })
        return result

    def get_registered_tools(self) -> List[str]:
        return list(self._registered_tools.keys())


class DNKPTCEngine:
    """
    DeepSeek Harness Programmatic Tool Calling (PTC) Engine.
    Executes programmatic multi-step agent batches in a single sandbox turn.
    """

    def __init__(self, tool_registry: Optional[Dict[str, Callable[..., Any]]] = None):
        self.tool_registry = tool_registry or {}

    def register_tool(self, name: str, fn: Callable[..., Any]) -> None:
        self.tool_registry[name] = fn

    def execute_script(self, request: PTCExecutionRequest) -> PTCExecutionResponse:
        sdk = PTCToolsSDK(self.tool_registry)
        stdout_capture = io.StringIO()
        old_stdout = sys.stdout

        local_scope: Dict[str, Any] = {
            "tools": sdk,
            "ptc": sdk,
            "result": None,
        }

        # Safe restricted builtins
        safe_builtins = {
            "abs": abs,
            "all": all,
            "any": any,
            "bool": bool,
            "dict": dict,
            "enumerate": enumerate,
            "filter": filter,
            "float": float,
            "int": int,
            "isinstance": isinstance,
            "len": len,
            "list": list,
            "map": map,
            "max": max,
            "min": min,
            "print": print,
            "range": range,
            "round": round,
            "set": set,
            "str": str,
            "sum": sum,
            "tuple": tuple,
            "zip": zip,
        }

        global_scope = {
            "__builtins__": safe_builtins,
            "tools": sdk,
        }

        start_time = time.perf_counter()
        try:
            sys.stdout = stdout_capture
            # Execute agent-provided script in controlled sandbox
            exec(request.code, global_scope, local_scope)
            sys.stdout = old_stdout
            duration_ms = (time.perf_counter() - start_time) * 1000

            return_value = local_scope.get("result")
            return PTCExecutionResponse(
                success=True,
                stdout=stdout_capture.getvalue(),
                return_value=return_value,
                duration_ms=duration_ms,
                tool_calls_executed=len(sdk.call_history),
            )
        except Exception as e:
            sys.stdout = old_stdout
            duration_ms = (time.perf_counter() - start_time) * 1000
            error_trace = traceback.format_exc()
            return PTCExecutionResponse(
                success=False,
                stdout=stdout_capture.getvalue(),
                error=f"{type(e).__name__}: {str(e)}\n{error_trace}",
                duration_ms=duration_ms,
                tool_calls_executed=len(sdk.call_history),
            )
        finally:
            sys.stdout = old_stdout
