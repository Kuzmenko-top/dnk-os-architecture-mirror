# --- DNK-MRH-HEADER ---
# mrh_id: "core_adapters_postgres_timeline_repository"
# purpose: "PostgreSQL implementation of ITimelineRepository using asyncpg with timeline schema isolation, recursive sanitization, and strict concurrency safety"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.2.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import json
from typing import Optional, List, Any
from uuid import UUID
try:
    import asyncpg
except ImportError:
    asyncpg = None

from core.ports.timeline_repository import ITimelineRepository
from core.models.timeline import Agent, Run, Task, Event
from core.config.timeline_config import MAX_PAYLOAD_SIZE

class PostgresTimelineRepository(ITimelineRepository):
    def __init__(self, pool: Any):
        self.pool = pool

    def _sanitize_payload(self, payload: Any) -> Any:
        if isinstance(payload, dict):
            sanitized = {}
            for k, v in payload.items():
                if k.lower() in {
                    "password", "passwd", "token", "api_key", "apikey", 
                    "secret", "authorization", "access_token", "refresh_token", 
                    "private_key", "cookie"
                }:
                    sanitized[k] = "***"
                else:
                    sanitized[k] = self._sanitize_payload(v)
            return sanitized
        elif isinstance(payload, list):
            return [self._sanitize_payload(item) for item in payload]
        else:
            return payload

    def _validate_payload_size(self, payload: dict) -> None:
        if not payload:
            return
        serialized = json.dumps(payload)
        if len(serialized.encode("utf-8")) > MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload size exceeds MAX_PAYLOAD_SIZE ({MAX_PAYLOAD_SIZE} bytes)")

    async def create_agent(self, agent: Agent) -> Agent:
        query = """
            INSERT INTO timeline.agents (id, name, description, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE 
            SET name = EXCLUDED.name, description = EXCLUDED.description, updated_at = EXCLUDED.updated_at
            RETURNING *;
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                agent.id,
                agent.name,
                agent.description,
                agent.created_at,
                agent.updated_at
            )
            return Agent(**dict(row))

    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        query = "SELECT * FROM timeline.agents WHERE id = $1;"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, agent_id)
            if row:
                return Agent(**dict(row))
            return None

    async def create_run(self, run: Run) -> Run:
        if run.idempotency_key:
            # Idempotency lock/write: INSERT ON CONFLICT DO NOTHING
            query_insert = """
                INSERT INTO timeline.runs (id, agent_id, run_type, status, idempotency_key, started_at, completed_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING *;
            """
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    query_insert,
                    run.id,
                    run.agent_id,
                    run.run_type,
                    run.status,
                    run.idempotency_key,
                    run.started_at,
                    run.completed_at,
                    run.created_at,
                    run.updated_at
                )
                if row:
                    return Run(**dict(row))
                
                # If ON CONFLICT fired, fetch the existing run
                query_select = "SELECT * FROM timeline.runs WHERE idempotency_key = $1;"
                row = await conn.fetchrow(query_select, run.idempotency_key)
                if row:
                    return Run(**dict(row))
                raise RuntimeError("Failed to create or retrieve idempotent run")
        else:
            query = """
                INSERT INTO timeline.runs (id, agent_id, run_type, status, idempotency_key, started_at, completed_at, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (id) DO UPDATE
                SET status = EXCLUDED.status, completed_at = EXCLUDED.completed_at, updated_at = EXCLUDED.updated_at
                RETURNING *;
            """
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(
                    query,
                    run.id,
                    run.agent_id,
                    run.run_type,
                    run.status,
                    run.idempotency_key,
                    run.started_at,
                    run.completed_at,
                    run.created_at,
                    run.updated_at
                )
                return Run(**dict(row))

    async def get_run(self, run_id: UUID) -> Optional[Run]:
        query = "SELECT * FROM timeline.runs WHERE id = $1;"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, run_id)
            if row:
                return Run(**dict(row))
            return None

    async def get_runs_by_agent(self, agent_id: UUID, limit: int = 50) -> List[Run]:
        query = "SELECT * FROM timeline.runs WHERE agent_id = $1 ORDER BY created_at DESC LIMIT $2;"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, agent_id, limit)
            return [Run(**dict(row)) for row in rows]

    async def create_task(self, task: Task) -> Task:
        # Sanitize sensitive fields in payload and result
        sanitized_payload = self._sanitize_payload(task.payload)
        sanitized_result = self._sanitize_payload(task.result) if task.result else None

        self._validate_payload_size(sanitized_payload)
        if sanitized_result:
            self._validate_payload_size(sanitized_result)
            
        # Serialize payload & result to json string
        payload_json = json.dumps(sanitized_payload)
        result_json = json.dumps(sanitized_result) if sanitized_result else None

        query = """
            INSERT INTO timeline.tasks (id, run_id, task_type, status, payload, result, error, started_at, completed_at, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, $9, $10, $11)
            ON CONFLICT (id) DO UPDATE
            SET status = EXCLUDED.status, result = EXCLUDED.result, error = EXCLUDED.error, 
                completed_at = EXCLUDED.completed_at, updated_at = EXCLUDED.updated_at
            RETURNING *;
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                task.id,
                task.run_id,
                task.task_type,
                task.status,
                payload_json,
                result_json,
                task.error,
                task.started_at,
                task.completed_at,
                task.created_at,
                task.updated_at
            )
            data = dict(row)
            if isinstance(data["payload"], str):
                data["payload"] = json.loads(data["payload"])
            if isinstance(data["result"], str):
                data["result"] = json.loads(data["result"])
            return Task(**data)

    async def get_task(self, task_id: UUID) -> Optional[Task]:
        query = "SELECT * FROM timeline.tasks WHERE id = $1;"
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(query, task_id)
            if row:
                data = dict(row)
                if isinstance(data["payload"], str):
                    data["payload"] = json.loads(data["payload"])
                if isinstance(data["result"], str):
                    data["result"] = json.loads(data["result"])
                return Task(**data)
            return None

    async def get_tasks_by_run(self, run_id: UUID, limit: int = 100) -> List[Task]:
        query = "SELECT * FROM timeline.tasks WHERE run_id = $1 ORDER BY created_at ASC LIMIT $2;"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, run_id, limit)
            results = []
            for row in rows:
                data = dict(row)
                if isinstance(data["payload"], str):
                    data["payload"] = json.loads(data["payload"])
                if isinstance(data["result"], str):
                    data["result"] = json.loads(data["result"])
                results.append(Task(**data))
            return results

    async def create_event(self, event: Event) -> Event:
        # Sanitize sensitive fields in payload
        sanitized_payload = self._sanitize_payload(event.payload)

        self._validate_payload_size(sanitized_payload)
        payload_json = json.dumps(sanitized_payload)

        query = """
            INSERT INTO timeline.events (id, run_id, task_id, event_type, payload, created_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6)
            ON CONFLICT (id) DO NOTHING
            RETURNING *;
        """
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                event.id,
                event.run_id,
                event.task_id,
                event.event_type,
                payload_json,
                event.created_at
            )
            if not row:
                # Event already exists due to ON CONFLICT. Fetch the existing event to prevent None dict cast.
                query_select = "SELECT * FROM timeline.events WHERE id = $1;"
                row = await conn.fetchrow(query_select, event.id)
                if not row:
                    raise RuntimeError("Failed to create or retrieve duplicate event")
            data = dict(row)
            if isinstance(data["payload"], str):
                data["payload"] = json.loads(data["payload"])
            return Event(**data)

    async def get_events_by_run(self, run_id: UUID, limit: int = 200) -> List[Event]:
        query = "SELECT * FROM timeline.events WHERE run_id = $1 ORDER BY created_at ASC LIMIT $2;"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, run_id, limit)
            results = []
            for row in rows:
                data = dict(row)
                if isinstance(data["payload"], str):
                    data["payload"] = json.loads(data["payload"])
                results.append(Event(**data))
            return results

    async def get_events_by_task(self, task_id: UUID, limit: int = 100) -> List[Event]:
        query = "SELECT * FROM timeline.events WHERE task_id = $1 ORDER BY created_at ASC LIMIT $2;"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, task_id, limit)
            results = []
            for row in rows:
                data = dict(row)
                if isinstance(data["payload"], str):
                    data["payload"] = json.loads(data["payload"])
                results.append(Event(**data))
            return results
