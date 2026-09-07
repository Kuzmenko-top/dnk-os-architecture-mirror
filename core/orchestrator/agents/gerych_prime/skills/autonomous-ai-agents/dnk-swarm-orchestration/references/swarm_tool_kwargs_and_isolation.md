# Swarm Tool Kwargs & Execution Pitfalls

## 1. Custom Tool Kwargs Forwarding Invariant
When defining custom tools in Hermes (e.g., `dnk_swarm_parallel`, `dnk_swarm_status`, `dnk_decompose_task_dna`), Hermes runtime or execution wrappers may inject internal orchestration parameters such as `task_id` or session metadata.
- **Rule**: Always include `**kwargs: Any` in tool function definitions and Pydantic/dataclass parameter models.
- **Pitfall**: Omitting `**kwargs` leads to runtime `TypeError: dnk_swarm_parallel() got an unexpected keyword argument 'task_id'` which crashes autonomous swarm dispatch.

## 2. Namespace Collision in Subprocess Swarm Orchestration
When running inside nested agent environments where `core/` exists both at root and within a subdirectory (e.g. `core/hermes_agent`), Python's default `import core...` may resolve to the local subdirectory rather than `$HUB_ROOT/core`.
- **Solution**: Always resolve imports via explicit `sys.path.insert(0, os.environ.get('HUB_ROOT', '.'))` or direct dynamic module loading using `importlib.util.spec_from_file_location`.
