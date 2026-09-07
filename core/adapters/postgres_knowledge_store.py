# --- DNK-MRH-HEADER ---
# mrh_id: "core_adapters_postgres_knowledge_store"
# purpose: "PostgreSQL pgvector-based Knowledge Store implementation with HNSW cosine search, JSONB filter containment, and timeline auditing"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.3.0"
# updated_at: "2026-08-11"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
import time
from datetime import datetime, UTC
from threading import Thread
from typing import List, Optional, Union
from uuid import UUID, uuid4
import asyncpg

from core.stores.knowledge_store import KnowledgeStore
from core.models.knowledge import KnowledgeDocument, KnowledgeQueryResult
from core.models.timeline import Event

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

class PostgresKnowledgeStore(KnowledgeStore):
    def __init__(self, dsn_or_pool: Union[str, asyncpg.Pool], schema: str = "timeline", timeline_repo=None):
        self.schema = schema
        self.timeline_repo = timeline_repo
        self.loop_thread = AsyncLoopThread()
        
        # Capture the main event loop for threadsafe cross-loop event logging
        try:
            self.main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self.main_loop = None
        
        # Safe async initialization of pool inside the AsyncLoopThread to prevent loop mismatch
        async def _init():
            if isinstance(dsn_or_pool, str):
                self.pool = await asyncpg.create_pool(dsn_or_pool)
                self._owns_pool = True
            else:
                self.pool = dsn_or_pool
                self._owns_pool = False
        
        self.loop_thread.run_coro(_init())
        self._init_db()

    def _init_db(self) -> None:
        async def init_schema():
            async with self.pool.acquire() as conn:
                await conn.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema};")
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.schema}.knowledge_documents (
                        id UUID PRIMARY KEY,
                        content TEXT NOT NULL,
                        embedding vector(768) NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        created_at BIGINT NOT NULL,
                        updated_at BIGINT NOT NULL
                    );
                """)
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS knowledge_embedding_idx 
                    ON {self.schema}.knowledge_documents 
                    USING hnsw (embedding vector_cosine_ops);
                """)
        self.loop_thread.run_coro(init_schema())

    def upsert_document(self, doc: KnowledgeDocument) -> None:
        async def _upsert():
            vector_str = "[" + ",".join(map(str, doc.embedding)) + "]"
            query = f"""
                INSERT INTO {self.schema}.knowledge_documents (
                    id, content, embedding, metadata, created_at, updated_at
                ) VALUES ($1, $2, $3::vector, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    embedding = EXCLUDED.embedding,
                    metadata = EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at;
            """
            async with self.pool.acquire() as conn:
                await conn.execute(
                    query,
                    doc.id,
                    doc.content,
                    vector_str,
                    json.dumps(doc.metadata),
                    doc.created_at,
                    doc.updated_at
                )
            
            run_id_str = doc.metadata.get("run_id")
            if run_id_str:
                try:
                    self._log_event(UUID(run_id_str), None, "knowledge_upserted", {
                        "doc_id": str(doc.id),
                        "source": doc.metadata.get("source")
                    })
                except Exception:
                    pass

        self.loop_thread.run_coro(_upsert())

    def search_similar(
        self,
        query: Union[str, List[float]],
        limit: int = 10,
        filters: Optional[dict] = None,
    ) -> List[KnowledgeQueryResult]:
        if isinstance(query, str):
            embedding = self._generate_mock_embedding(query)
        else:
            embedding = query

        async def _search():
            vector_str = "[" + ",".join(map(str, embedding)) + "]"
            
            if filters:
                filter_json = json.dumps(filters)
                query_str = f"""
                    SELECT id, content, metadata, (embedding <=> $1::vector) as distance
                    FROM {self.schema}.knowledge_documents
                    WHERE metadata @> $3::jsonb
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2;
                """
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(query_str, vector_str, limit, filter_json)
            else:
                query_str = f"""
                    SELECT id, content, metadata, (embedding <=> $1::vector) as distance
                    FROM {self.schema}.knowledge_documents
                    ORDER BY embedding <=> $1::vector
                    LIMIT $2;
                """
                async with self.pool.acquire() as conn:
                    rows = await conn.fetch(query_str, vector_str, limit)

            results = []
            for row in rows:
                distance = row["distance"]
                score = 1.0 - float(distance) if distance is not None else 0.0
                results.append(KnowledgeQueryResult(
                    doc_id=row["id"],
                    content=row["content"],
                    score=score,
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                ))

            if filters and "run_id" in filters:
                try:
                    self._log_event(UUID(filters["run_id"]), None, "knowledge_searched", {
                        "filters": filters,
                        "results_count": len(results)
                    })
                except Exception:
                    pass

            return results

        return self.loop_thread.run_coro(_search())

    def delete_document(self, doc_id: UUID) -> None:
        async def _delete():
            query = f"DELETE FROM {self.schema}.knowledge_documents WHERE id = $1;"
            async with self.pool.acquire() as conn:
                await conn.execute(query, doc_id)
        self.loop_thread.run_coro(_delete())

    def close(self) -> None:
        async def _close():
            if getattr(self, "_owns_pool", False) and self.pool:
                await self.pool.close()
        try:
            self.loop_thread.run_coro(_close())
        except Exception:
            pass

    def _generate_mock_embedding(self, text: str) -> List[float]:
        import hashlib
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vector = []
        for i in range(768):
            val = float((h[i % 32] * (i + 1)) % 1000) / 500.0 - 1.0
            vector.append(val)
        return vector

    def _log_event(self, run_id: UUID, task_id: Optional[UUID], event_type: str, payload: dict) -> None:
        if not self.timeline_repo:
            return
        event = Event(
            id=uuid4(),
            run_id=run_id,
            task_id=task_id,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(UTC)
        )
        
        async def _save():
            await self.timeline_repo.create_event(event)

        if self.main_loop and self.main_loop.is_running():
            self.main_loop.call_soon_threadsafe(asyncio.create_task, _save())
        else:
            # If no main loop is running, we can create a temporary loop
            asyncio.run(_save())
