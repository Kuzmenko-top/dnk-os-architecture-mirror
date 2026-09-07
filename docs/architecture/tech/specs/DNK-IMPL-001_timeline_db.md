---
mrh_id: "dnk_impl_001_timeline_db"
purpose: "Technical specification and documentation of PostgreSQL-first Timeline DB"
author: "DNK-e.com Maksym"
license: "DNK-INTERNAL"
status: "Active"
version: "1.0.0"
updated_at: "2026-08-11"
---

# DNK-IMPL-001: PostgreSQL-first Timeline DB

This document specifies the design, schema, and interface of the PostgreSQL-first Timeline DB inside `DNK_HUB`. The database is responsible for tracking all agent executions (runs, events, agents, and tasks), enabling full auditability, reproducibility, and autonomous self-improvement.

## 1. Database Schema

The database uses four main tables isolated cleanly under a customizable schema (default `timeline`) to avoid naming collisions with general-purpose database tables:

### 1.1 Tables

1. **`agents`**
   - `id` (UUID, Primary Key)
   - `name` (TEXT, NOT NULL)
   - `description` (TEXT)
   - `created_at` (TIMESTAMP, NOT NULL, DEFAULT NOW())
   - `updated_at` (TIMESTAMP, NOT NULL, DEFAULT NOW())

2. **`runs`**
   - `id` (UUID, Primary Key)
   - `agent_id` (UUID, Foreign Key referencing `agents(id)`, NOT NULL, ON DELETE CASCADE)
   - `run_type` (TEXT, NOT NULL) — e.g., `task`, `research`, `orchestration`
   - `status` (TEXT, NOT NULL) — `pending`, `running`, `completed`, `failed`, `interrupted`
   - `idempotency_key` (TEXT, UNIQUE) — Used for deduplication
   - `started_at` (TIMESTAMP)
   - `completed_at` (TIMESTAMP)
   - `created_at` (TIMESTAMP, NOT NULL, DEFAULT NOW())
   - `updated_at` (TIMESTAMP, NOT NULL, DEFAULT NOW())

3. **`tasks`**
   - `id` (UUID, Primary Key)
   - `run_id` (UUID, Foreign Key referencing `runs(id)`, NOT NULL, ON DELETE CASCADE)
   - `task_type` (TEXT, NOT NULL) — e.g., `research`, `write`, `validate`
   - `status` (TEXT, NOT NULL) — `pending`, `running`, `completed`, `failed`
   - `payload` (JSONB, NOT NULL) — Input parameters
   - `result` (JSONB) — Task results
   - `error` (TEXT) — Error messages if failed
   - `started_at` (TIMESTAMP)
   - `completed_at` (TIMESTAMP)
   - `created_at` (TIMESTAMP, NOT NULL, DEFAULT NOW())
   - `updated_at` (TIMESTAMP, NOT NULL, DEFAULT NOW())

4. **`events`**
   - `id` (UUID, Primary Key)
   - `run_id` (UUID, Foreign Key referencing `runs(id)`, NOT NULL, ON DELETE CASCADE)
   - `task_id` (UUID, Foreign Key referencing `tasks(id)`, NULL, ON DELETE SET NULL)
   - `event_type` (TEXT, NOT NULL) — e.g., `run_started`, `task_created`, `task_completed`, `error`, `interrupt`
   - `payload` (JSONB, NOT NULL) — Event details
   - `created_at` (TIMESTAMP, NOT NULL, DEFAULT NOW())

### 1.2 Indexes

- `runs(agent_id, created_at)`
- `runs(idempotency_key)` (filtered index: `WHERE idempotency_key IS NOT NULL`)
- `tasks(run_id, created_at)`
- `events(run_id, created_at)`
- `events(task_id, created_at)` (filtered index: `WHERE task_id IS NOT NULL`)

---

## 2. Ports (Repository Interface)

Located at `core/ports/timeline_repository.py`:

```python
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID

from core.models.timeline import Agent, Run, Task, Event

class TimelineRepository(ABC):
    @abstractmethod
    async def create_agent(self, agent: Agent) -> Agent:
        pass

    @abstractmethod
    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        pass

    @abstractmethod
    async def create_run(self, run: Run) -> Run:
        pass

    @abstractmethod
    async def get_run(self, run_id: UUID) -> Optional[Run]:
        pass

    @abstractmethod
    async def get_runs_by_agent(self, agent_id: UUID, limit: int = 50) -> List[Run]:
        pass

    @abstractmethod
    async def create_task(self, task: Task) -> Task:
        pass

    @abstractmethod
    async def get_task(self, task_id: UUID) -> Optional[Task]:
        pass

    @abstractmethod
    async def get_tasks_by_run(self, run_id: UUID, limit: int = 100) -> List[Task]:
        pass

    @abstractmethod
    async def create_event(self, event: Event) -> Event:
        pass

    @abstractmethod
    async def get_events_by_run(self, run_id: UUID, limit: int = 200) -> List[Event]:
        pass

    @abstractmethod
    async def get_events_by_task(self, task_id: UUID, limit: int = 100) -> List[Event]:
        pass
```

---

## 3. Adapter Implementation (PostgreSQL)

Located at `core/adapters/postgres_timeline_repository.py`.

- Fully asynchronous operations utilizing the high-performance `asyncpg` library.
- Safely implements concurrent write handling with SQL `INSERT ... ON CONFLICT (idempotency_key) DO NOTHING` pattern, ensuring absolute concurrency safety during rapid multi-agent executions.
- Includes automatic size checking for `payload` and `result` fields to prevent database bloat, raising a clear `ValueError` if size exceeds the configured limit (`MAX_PAYLOAD_SIZE`).

---

## 4. Configuration

Located at `core/config/timeline_config.py`.

- `DATABASE_URL`: Connection URL for Postgres (defaults to `POSTGRES_URL` environment variable).
- `TIMELINE_SCHEMA`: Schema namespace used for database isolation (defaults to `timeline`).
- `ALLOW_SQLITE`: Boolean allowing SQLite local development fallbacks (defaults to `False`).
- `MAX_PAYLOAD_SIZE`: Payload size limit in bytes (defaults to 1MB).

---

## 5. Verification Tests

Located at `tests/verification/test_timeline_repository.py`.

The repository's functionality is thoroughly verified via 6 end-to-end tests:
1. `test_create_agent` - agent creation and fetching.
2. `test_create_run` - run creation, querying, and idempotency mapping.
3. `test_create_task` - task insertion, payload validation, and run-association.
4. `test_create_event` - event logging and mapping to task/run lines.
5. `test_concurrent_writes` - concurrent writes mapping identical keys safely to the same entity.
6. `test_payload_sanitization` - payload size limiting verification.

Run tests using:
```bash
cd . && PYTHONPATH=../ .venv/bin/pytest tests/verification/test_timeline_repository.py
```
