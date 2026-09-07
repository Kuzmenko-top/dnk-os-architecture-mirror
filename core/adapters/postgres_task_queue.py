# --- DNK-MRH-HEADER ---
# mrh_id: "core_adapters_postgres_task_queue"
# purpose: "PostgreSQL-based Task Queue implementation with prioritization, FIFO and SKIP LOCKED concurrency"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import json
import time
import asyncio
from threading import Thread
from typing import Optional, List
from uuid import UUID
import asyncpg

from core.queues.task_queue import TaskQueue
from core.models.collaboration import Task, TaskPriority, TaskStatus

class AsyncLoopThread:
    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_coro(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

class PostgresTaskQueue(TaskQueue):
    def __init__(self, pool: asyncpg.Pool, schema: str = "timeline"):
        self.pool = pool
        self.schema = schema
        self.loop_thread = AsyncLoopThread()
        self._init_db()

    def _init_db(self) -> None:
        async def init_schema():
            async with self.pool.acquire() as conn:
                await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema};")
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.collaboration_tasks (
                        id UUID PRIMARY KEY,
                        run_id UUID NOT NULL,
                        agent_id UUID NOT NULL,
                        task_type TEXT NOT NULL,
                        priority TEXT NOT NULL,
                        status TEXT NOT NULL,
                        payload JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        result JSONB,
                        error TEXT,
                        created_at BIGINT NOT NULL,
                        updated_at BIGINT NOT NULL
                    );
                """)
        self.loop_thread.run_coro(init_schema())

    def enqueue(self, task: Task) -> None:
        async def _enqueue():
            query = f"""
                INSERT INTO {self.schema}.collaboration_tasks (
                    id, run_id, agent_id, task_type, priority, status, payload, result, error, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET
                    priority = EXCLUDED.priority,
                    status = EXCLUDED.status,
                    payload = EXCLUDED.payload,
                    result = EXCLUDED.result,
                    error = EXCLUDED.error,
                    updated_at = EXCLUDED.updated_at;
            """
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query,
                    task.id,
                    task.run_id,
                    task.agent_id,
                    task.task_type,
                    task.priority.value,
                    task.status.value,
                    json.dumps(task.payload),
                    json.dumps(task.result) if task.result is not None else None,
                    task.error,
                    task.created_at,
                    task.updated_at
                )
        self.loop_thread.run_coro(_enqueue())

    def dequeue(self, agent_id: UUID) -> Optional[Task]:
        async def _dequeue():
            now = int(time.time())
            # FOR UPDATE SKIP LOCKED is highly concurrent and prevents lock contention
            query = f"""
                UPDATE {self.schema}.collaboration_tasks
                SET status = $1, updated_at = $2
                WHERE id = (
                    SELECT id FROM {self.schema}.collaboration_tasks
                    WHERE agent_id = $3 AND status = $4
                    ORDER BY 
                        CASE priority
                            WHEN 'CRITICAL' THEN 4
                            WHEN 'HIGH' THEN 3
                            WHEN 'MEDIUM' THEN 2
                            WHEN 'LOW' THEN 1
                            ELSE 0
                        END DESC,
                        created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                RETURNING *;
            """
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, TaskStatus.RUNNING.value, now, agent_id, TaskStatus.PENDING.value)
                if row:
                    return Task(
                        id=row["id"],
                        run_id=row["run_id"],
                        agent_id=row["agent_id"],
                        task_type=row["task_type"],
                        priority=TaskPriority(row["priority"]),
                        status=TaskStatus(row["status"]),
                        payload=json.loads(row["payload"]),
                        result=json.loads(row["result"]) if row["result"] else None,
                        error=row["error"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"]
                    )
                return None
        return self.loop_thread.run_coro(_dequeue())

    def get_pending_tasks(self, agent_id: UUID) -> List[Task]:
        async def _get_pending():
            query = f"""
                SELECT * FROM {self.schema}.collaboration_tasks
                WHERE agent_id = $1 AND status = $2
                ORDER BY 
                    CASE priority
                        WHEN 'CRITICAL' THEN 4
                        WHEN 'HIGH' THEN 3
                        WHEN 'MEDIUM' THEN 2
                        WHEN 'LOW' THEN 1
                        ELSE 0
                    END DESC,
                    created_at ASC;
            """
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, agent_id, TaskStatus.PENDING.value)
                return [
                    Task(
                        id=row["id"],
                        run_id=row["run_id"],
                        agent_id=row["agent_id"],
                        task_type=row["task_type"],
                        priority=TaskPriority(row["priority"]),
                        status=TaskStatus(row["status"]),
                        payload=json.loads(row["payload"]),
                        result=json.loads(row["result"]) if row["result"] else None,
                        error=row["error"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"]
                    )
                    for row in rows
                ]
        return self.loop_thread.run_coro(_get_pending())

    def reprioritize(self, task_id: UUID, new_priority: TaskPriority) -> None:
        async def _reprioritize():
            now = int(time.time())
            query = f"""
                UPDATE {self.schema}.collaboration_tasks
                SET priority = $1, updated_at = $2
                WHERE id = $3;
            """
            async with self.pool.acquire() as conn:
                await conn.execute(query, new_priority.value, now, task_id)
        self.loop_thread.run_coro(_reprioritize())
