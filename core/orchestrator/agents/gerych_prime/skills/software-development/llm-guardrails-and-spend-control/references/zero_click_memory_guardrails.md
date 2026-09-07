# Zero-Click Memory Guardrails & SCONES Expectation Hook

## Overview
Cognitive memory engines (e.g., SCONES) store episodic knowledge, decisions, and architectural rules across agent turns. If unconstrained, agent writes can poison the memory bank with:
1. Malformed payload schemas (missing required fields like `topic`, `content`).
2. Numerical drift (e.g., `importance` outside `[0.0, 1.0]`).
3. Local environment path leaks (e.g., hardcoded absolute `/Users/...` or `/home/...` paths violating universal relative path invariants).

The Zero-Click Memory Guardrail intercepts all write operations at the storage engine boundary before persisting to disk or vector indexes.

## Architecture
```
Agent / Tool Call (scones_add_memory)
       │
       ▼
SCONESMemoryEngine.add_memory(topic, content, importance, ...)
       │
       ▼
SconesExpectationValidator.validate_episode(candidate)
       ├── Check required fields ('topic', 'content', 'importance')
       ├── Validate range (importance in [0.0, 1.0])
       └── Evaluate Predicates:
             └── no_hardcoded_user_paths: Regex scan for /Users/ or /home/
       │
       ├─── PASSED ───────────────► Persist to storage & return memory_id
       │
       └─── FAILED
             ├── Default Mode: Log WARNING, attach '_expectation_violations' metadata
             ├── Strict Mode: Raise ValueError(violations)
             └── Tool Layer: Catch ValueError and return JSON status='validation_error'
```

## Implementation Recipes

### 1. Engine-Level Middleware Hook
```python
class SCONESMemoryEngine:
    def __init__(self, ..., enable_expectation_hook: bool = True, strict_expectation: bool = False):
        self.enable_expectation_hook = enable_expectation_hook
        self.strict_expectation = strict_expectation
        if self.enable_expectation_hook:
            suite = EpisodeExpectationSuite(
                required_fields=['id', 'topic', 'content', 'importance'],
                importance_range=(0.0, 1.0),
                no_hardcoded_user_paths=True,
            )
            self.validator = SconesExpectationValidator(suite)

    def add_memory(self, topic: str, content: str, importance: float = 0.5, ...):
        candidate = {
            "id": memory_id,
            "topic": topic,
            "content": content,
            "importance": importance,
        }
        if self.enable_expectation_hook and self.validator:
            report = self.validator.validate_episode(candidate)
            if not report.passed:
                if self.strict_expectation:
                    raise ValueError(f"Memory validation failed: {report.violations}")
                candidate["_expectation_violations"] = report.violations
```

### 2. Tool-Level Self-Healing Handshake
In the agent tool wrapper (`dnk_scones_tool.py`), catch `ValueError` from strict validation and return a structured JSON response rather than bubbling an unhandled exception:
```python
try:
    memory_id = engine.add_memory(topic=topic, content=content, importance=importance)
    return json.dumps({"status": "success", "id": memory_id})
except ValueError as exc:
    return json.dumps({
        "status": "validation_error",
        "error": str(exc),
        "hint": "Ensure importance is within [0.0, 1.0] and paths are strictly relative (./ or ../)."
    })
```
This enables the calling LLM to inspect the validation error and self-correct on its next turn without terminating the agent turn.
