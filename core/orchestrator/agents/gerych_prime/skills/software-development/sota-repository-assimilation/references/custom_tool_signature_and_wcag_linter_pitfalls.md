# Custom Tool Signature Hygiene & WCAG AA Linter Pitfalls

## 1. Custom Tool Signature Invariant for Tool Executors
When defining custom Python tools called dynamically by orchestrator frames (`tool_executor.py`):
- **Problem**: Orchestrators and agent runtimes often auto-inject context parameters such as `task_id`, `workspace_id`, or extra metadata into tool call keyword arguments.
- **Rule**: Every custom tool function MUST accept `task_id: Optional[str] = None` and `**kwargs: Any`, and provide default fallback values for positional parameters:
```python
def dnk_custom_tool(
    query: str = "",
    workspace_id: str = "ws-alpha-001",
    task_id: Optional[str] = None,
    **kwargs: Any
) -> str:
    ...
```
- **Benefit**: Prevents `TypeError: got an unexpected keyword argument 'task_id'` and unexpected missing argument crashes during automated swarm execution.

## 2. WCAG AA Contrast Ratio Linter Findings Pattern
When linting DESIGN.md color tokens and component themes for WCAG AA (4.5:1 for normal text) using relative luminance ($L = 0.2126R + 0.7152G + 0.0722B$):
- Palette-level findings structure: `{"rule": "contrast-ratio", "target": "primary_vs_bg", "ratio": 12.5, "passes_aa": True}`
- Component-level findings structure: `{"rule": "contrast-ratio", "component": "card-dark", "ratio": 1.2, "passes_aa": False}`
- **Pitfall**: Do not assume every finding dictionary contains a `"component"` key. Always extract safely with `f.get("component")` when filtering component failures.

## 3. Two-Tier Root Relocation Protocol
In a unified monorepo workspace (`DNK_HUB`), ensure all generated adapter code, test suites, and specifications live at the canonical root (`core/adapters/`, `docs/reports/`, `docs/tech/specs/`, `tests/`). Never leave generated artifacts buried inside agent subdirectories (`core/hermes_agent/...`).
