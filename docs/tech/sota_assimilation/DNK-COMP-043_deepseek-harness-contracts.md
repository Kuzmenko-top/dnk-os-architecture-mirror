# --- DNK-MRH-HEADER ---
# mrh_id: "docs/tech/sota_assimilation/DNK-COMP-043_deepseek-harness-contracts.md"
# purpose: "Component Contracts: Python Interfaces, Data Structures, and Schemas for DeepSeek Harness"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

# 📋 Component Contracts DNK-COMP-043: DeepSeek Harness Tool Guard & PTC

## 1. ToolExecutionContext & ToolPipelineOutput (Pydantic v2)
```python
class ToolExecutionContext(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    invoked_by: str = "agent"
    context_id: Optional[str] = None
    timeout_sec: Optional[float] = None

class ToolPipelineOutput(BaseModel):
    success: bool
    result: Any = None
    error: Optional[str] = None
    truncated: bool = False
    original_size_bytes: int = 0
    duration_ms: float = 0.0
    stage_failed: Optional[str] = None
```

## 2. PTC Engine Schemas
```python
class PTCExecutionRequest(BaseModel):
    code: str
    timeout_sec: float = 10.0
    context_vars: Dict[str, Any] = Field(default_factory=dict)

class PTCExecutionResponse(BaseModel):
    success: bool
    stdout: str = ""
    return_value: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    tool_calls_executed: int = 0
```
