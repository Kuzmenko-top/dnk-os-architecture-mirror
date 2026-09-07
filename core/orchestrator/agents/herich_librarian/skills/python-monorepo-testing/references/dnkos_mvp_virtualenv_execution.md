# DNK OS Virtualenv Interpreter Selection Pattern

When running tests inside sub-applications like `DNK_HUB/` from a monorepo or orchestrator session:

## Symptom
Running a generic `pytest tests/workspace/` may default to the orchestrator or global virtualenv (e.g. `core/hermes_agent/.venv/bin/pytest` on Python 3.12), causing:
```text
ModuleNotFoundError: No module named 'asyncpg'
ModuleNotFoundError: No module named 'sqlalchemy'
```

## Solution
Always explicitly invoke the sub-application's local virtualenv interpreter:
```bash
./.venv/bin/pytest tests/workspace/ -v
```
Or with `uv run`:
```bash
uv run pytest tests/workspace/ -v
```
This guarantees that all service dependencies (asyncpg, sqlalchemy, fastapi, pytest-asyncio) are resolved against the active virtualenv.
