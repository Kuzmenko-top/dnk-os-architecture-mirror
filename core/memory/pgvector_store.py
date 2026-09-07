# --- DNK-MRH-HEADER ---
# mrh_id: "core/memory/pgvector_store.py"
# purpose: "High-performance pgvector HNSW memory engine backend with 500ms query timeout, tenant isolation, and connection pooling"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

"""
PostgreSQL pgvector memory engine backend.
Supports HNSW index (m=16, ef_construction=64), vector dimension 768,
statement query timeout (500ms), tenant/workspace isolation,
and dual tables: scones_memories and scones_error_solutions.
"""

import os
import time
import math
import json
import struct
import hashlib
import logging
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2 import pool as psycopg2_pool  # type: ignore
    from psycopg2 import extras as psycopg2_extras  # type: ignore
    from psycopg2 import sql as psycopg2_sql  # type: ignore
    PSYCOPG2_AVAILABLE = True
except ImportError:
    psycopg2 = None  # type: ignore
    psycopg2_pool = None  # type: ignore
    psycopg2_extras = None  # type: ignore
    psycopg2_sql = None  # type: ignore
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger("PgVectorStore")

VECTOR_DIMENSION = 768
HNSW_M = 16
HNSW_EF_CONSTRUCTION = 64
DEFAULT_QUERY_TIMEOUT_MS = 500


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def generate_embedding(text: str, dim: int = VECTOR_DIMENSION) -> List[float]:
    """
    Generates a deterministic unit-normalized embedding vector of size `dim` from text.
    Uses seeded hash projections for high-speed deterministic offline testing & execution.
    """
    if not text:
        return [0.0] * dim

    tokens = [t.strip().lower() for t in text.split() if t.strip()]
    if not tokens:
        tokens = [text.lower()]

    vec = [0.0] * dim
    for token in tokens:
        h = hashlib.sha256(token.encode("utf-8")).digest()
        for i in range(0, min(len(h), dim)):
            val = struct.unpack("b", h[i:i+1])[0] / 128.0
            idx = (i * 31 + int(h[i])) % dim
            vec[idx] += val

    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [float(x / norm) for x in vec]
    else:
        vec[0] = 1.0
    return vec


class PgVectorStore:
    """
    PostgreSQL pgvector HNSW memory engine backend.
    
    Invariants:
    - Vector dimension: 768
    - HNSW index parameters: m=16, ef_construction=64
    - Query statement timeout: 500ms
    - Resilient connection pooling with graceful fallback detection
    """

    def __init__(
        self,
        connection_string: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        dbname: Optional[str] = None,
        vector_dim: int = VECTOR_DIMENSION,
        query_timeout_ms: int = DEFAULT_QUERY_TIMEOUT_MS,
        connect_timeout_s: int = 2,
        min_pool_size: int = 1,
        max_pool_size: int = 10,
        auto_init_schema: bool = False
    ):
        self.vector_dim = vector_dim
        self.query_timeout_ms = query_timeout_ms
        self.connect_timeout_s = connect_timeout_s
        self.min_pool_size = min_pool_size
        self.max_pool_size = max_pool_size

        # Resolve connection parameters
        if connection_string:
            self.connection_string = connection_string
            self.host = host or os.getenv("POSTGRES_HOST", "localhost")
            self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        elif host or port:
            self.connection_string = None
            self.host = host or os.getenv("POSTGRES_HOST", "localhost")
            self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        else:
            self.connection_string = (
                os.getenv("PGVECTOR_URL")
                or os.getenv("POSTGRES_URL")
                or os.getenv("DATABASE_URL")
            )
            self.host = os.getenv("POSTGRES_HOST", "localhost")
            self.port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.user = user or os.getenv("POSTGRES_USER", "postgres")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "postgres")
        self.dbname = dbname or os.getenv("POSTGRES_DB", "dnk_memory")

        self._pool = None
        self._is_available = False
        self._schema_initialized = False

        # Attempt pool initialization
        self._try_init_pool()
        if self._is_available and auto_init_schema:
            self.initialize_schema()

    def _get_conn_kwargs(self) -> Dict[str, Any]:
        """Construct connection parameters dict for psycopg2."""
        if self.connection_string:
            return {
                "dsn": self.connection_string,
                "connect_timeout": self.connect_timeout_s,
                "options": f"-c statement_timeout={self.query_timeout_ms}"
            }
        return {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "dbname": self.dbname,
            "connect_timeout": self.connect_timeout_s,
            "options": f"-c statement_timeout={self.query_timeout_ms}"
        }

    def _try_init_pool(self) -> bool:
        if not PSYCOPG2_AVAILABLE or psycopg2_pool is None:
            self._is_available = False
            return False
        try:
            kwargs = self._get_conn_kwargs()
            self._pool = psycopg2_pool.ThreadedConnectionPool(
                minconn=self.min_pool_size,
                maxconn=self.max_pool_size,
                **kwargs
            )
            # Test a connection
            conn = self._pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute(f"SET statement_timeout = {self.query_timeout_ms};")
                    cur.execute("SELECT 1;")
                self._is_available = True
            finally:
                if self._pool and conn:
                    self._pool.putconn(conn)
            return True
        except Exception as e:
            logger.info("PgVector PostgreSQL is not reachable (%s). Operating in fallback mode.", e)
            self._is_available = False
            if self._pool:
                try:
                    self._pool.closeall()
                except Exception:
                    pass
                self._pool = None
            return False

    def is_healthy(self) -> bool:
        """Check if pgvector database backend is connected and healthy."""
        if not self._pool:
            return self._try_init_pool()
        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    return True
        except Exception:
            self._is_available = False
            return False

    @contextmanager
    def connection(self):
        """Context manager to acquire and release connection from pool with timeout setting."""
        if not self._pool or not self._is_available:
            if not self._try_init_pool() or self._pool is None:
                raise ConnectionError("PostgreSQL pgvector pool is unavailable")
        
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cur:
                cur.execute(f"SET statement_timeout = {self.query_timeout_ms};")
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise e
        finally:
            if self._pool and conn:
                try:
                    self._pool.putconn(conn)
                except Exception:
                    pass

    def initialize_schema(self) -> bool:
        """
        Creates pgvector extension, scones_memories table, scones_error_solutions table,
        and HNSW indexes (m=16, ef_construction=64).
        """
        if not self.is_healthy():
            return False

        schema_sql = f"""
        -- 1. Enable pgvector extension
        CREATE EXTENSION IF NOT EXISTS vector;

        -- 2. scones_memories table
        CREATE TABLE IF NOT EXISTS scones_memories (
            id VARCHAR(128) PRIMARY KEY,
            topic VARCHAR(256) NOT NULL,
            content TEXT NOT NULL,
            importance DOUBLE PRECISION DEFAULT 1.0,
            metadata JSONB DEFAULT '{{}}'::jsonb,
            embedding vector({self.vector_dim}),
            created_at DOUBLE PRECISION NOT NULL
        );

        -- Standard and GIN indexes
        CREATE INDEX IF NOT EXISTS idx_scones_memories_topic ON scones_memories (topic);
        CREATE INDEX IF NOT EXISTS idx_scones_memories_metadata ON scones_memories USING gin (metadata);

        -- HNSW Vector Index (m={HNSW_M}, ef_construction={HNSW_EF_CONSTRUCTION})
        CREATE INDEX IF NOT EXISTS idx_scones_memories_hnsw ON scones_memories 
        USING hnsw (embedding vector_cosine_ops) 
        WITH (m = {HNSW_M}, ef_construction = {HNSW_EF_CONSTRUCTION});

        -- 3. scones_error_solutions table
        CREATE TABLE IF NOT EXISTS scones_error_solutions (
            id VARCHAR(128) PRIMARY KEY,
            error_signature VARCHAR(512),
            error_text TEXT NOT NULL,
            solution_text TEXT NOT NULL,
            root_cause TEXT,
            metadata JSONB DEFAULT '{{}}'::jsonb,
            embedding vector({self.vector_dim}),
            created_at DOUBLE PRECISION NOT NULL,
            success_rate DOUBLE PRECISION DEFAULT 1.0
        );

        CREATE INDEX IF NOT EXISTS idx_scones_error_solutions_sig ON scones_error_solutions (error_signature);
        CREATE INDEX IF NOT EXISTS idx_scones_error_solutions_metadata ON scones_error_solutions USING gin (metadata);

        -- HNSW Vector Index for error solutions
        CREATE INDEX IF NOT EXISTS idx_scones_error_solutions_hnsw ON scones_error_solutions 
        USING hnsw (embedding vector_cosine_ops) 
        WITH (m = {HNSW_M}, ef_construction = {HNSW_EF_CONSTRUCTION});

        -- 4. Full-text search tsvector columns, GIN indexes, and auto-update triggers
        ALTER TABLE scones_error_solutions ADD COLUMN IF NOT EXISTS search_vector tsvector;
        CREATE INDEX IF NOT EXISTS idx_scones_error_solutions_search_vector ON scones_error_solutions USING gin (search_vector);

        ALTER TABLE scones_memories ADD COLUMN IF NOT EXISTS search_vector tsvector;
        CREATE INDEX IF NOT EXISTS idx_scones_memories_search_vector ON scones_memories USING gin (search_vector);

        CREATE OR REPLACE FUNCTION scones_error_solutions_search_vector_update()
        RETURNS trigger AS $$
        BEGIN
          NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.error_signature, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.error_text, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.root_cause, '')), 'B') ||
            setweight(to_tsvector('english', COALESCE(NEW.solution_text, '')), 'C');
          RETURN NEW;
        END
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS scones_error_solutions_search_vector_trigger ON scones_error_solutions;
        CREATE TRIGGER scones_error_solutions_search_vector_trigger
        BEFORE INSERT OR UPDATE ON scones_error_solutions
        FOR EACH ROW EXECUTE FUNCTION scones_error_solutions_search_vector_update();

        CREATE OR REPLACE FUNCTION scones_memories_search_vector_update()
        RETURNS trigger AS $$
        BEGIN
          NEW.search_vector :=
            setweight(to_tsvector('english', COALESCE(NEW.topic, '')), 'A') ||
            setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
          RETURN NEW;
        END
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS scones_memories_search_vector_trigger ON scones_memories;
        CREATE TRIGGER scones_memories_search_vector_trigger
        BEFORE INSERT OR UPDATE ON scones_memories
        FOR EACH ROW EXECUTE FUNCTION scones_memories_search_vector_update();
        """

        try:
            with self.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(schema_sql)
            self._schema_initialized = True
            logger.info("PgVector HNSW schema and indexes successfully initialized.")
            return True
        except Exception as e:
            logger.error("Failed to initialize pgvector schema: %s", e)
            return False

    # -------------------------------------------------------------------------
    # scones_memories CRUD & Vector Search
    # -------------------------------------------------------------------------

    def _get_dict_cursor_factory(self) -> Any:
        if psycopg2_extras is not None:
            return psycopg2_extras.RealDictCursor
        return None

    def upsert_memory(
        self,
        id: str,
        topic: str,
        content: str,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        created_at: Optional[float] = None
    ) -> Dict[str, Any]:
        """Upsert a memory entry into scones_memories."""
        meta = metadata or {}
        ts = created_at or time.time()
        emb_str = f"[{','.join(str(x) for x in embedding)}]" if embedding else None

        sql_query = """
        INSERT INTO scones_memories (id, topic, content, importance, metadata, embedding, created_at)
        VALUES (%s, %s, %s, %s, %s::jsonb, %s::vector, %s)
        ON CONFLICT (id) DO UPDATE SET
            topic = EXCLUDED.topic,
            content = EXCLUDED.content,
            importance = EXCLUDED.importance,
            metadata = EXCLUDED.metadata,
            embedding = EXCLUDED.embedding,
            created_at = EXCLUDED.created_at;
        """

        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql_query,
                    (
                        id,
                        topic,
                        content,
                        float(importance),
                        json.dumps(meta),
                        emb_str,
                        float(ts)
                    )
                )

        return {
            "id": id,
            "topic": topic,
            "content": content,
            "importance": importance,
            "metadata": meta,
            "embedding": embedding,
            "created_at": ts
        }

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID."""
        sql_query = """
        SELECT id, topic, content, importance, metadata, created_at
        FROM scones_memories
        WHERE id = %s;
        """
        with self.connection() as conn:
            with conn.cursor(cursor_factory=self._get_dict_cursor_factory()) as cur:
                cur.execute(sql_query, (memory_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return dict(row)

    def query_memories(
        self,
        query_embedding: Optional[List[float]] = None,
        topic: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Query memories with HNSW vector cosine search, metadata filtering, and 500ms timeout.
        """
        where_clauses = ["1=1"]
        params: List[Any] = []

        if topic:
            where_clauses.append("topic = %s")
            params.append(topic)
        if tenant_id:
            where_clauses.append("metadata->>'tenant_id' = %s")
            params.append(tenant_id)
        if workspace_id:
            where_clauses.append("metadata->>'workspace_id' = %s")
            params.append(workspace_id)

        if query_embedding:
            emb_str = f"[{','.join(str(x) for x in query_embedding)}]"
            where_sql = " AND ".join(where_clauses)
            sql_query = f"""
            SELECT id, topic, content, importance, metadata, created_at,
                   1.0 - (embedding <=> %s::vector) AS similarity
            FROM scones_memories
            WHERE {where_sql}
            """
            params_full: List[Any] = [emb_str] + list(params)

            if min_similarity > 0.0:
                sql_query += " AND (1.0 - (embedding <=> %s::vector)) >= %s"
                params_full.extend([emb_str, float(min_similarity)])

            sql_query += """
            ORDER BY embedding <=> %s::vector ASC
            LIMIT %s;
            """
            params_full.extend([emb_str, int(limit)])
        else:
            where_sql = " AND ".join(where_clauses)
            sql_query = f"""
            SELECT id, topic, content, importance, metadata, created_at, 1.0 AS similarity
            FROM scones_memories
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s;
            """
            params_full: List[Any] = list(params) + [int(limit)]

        with self.connection() as conn:
            with conn.cursor(cursor_factory=self._get_dict_cursor_factory()) as cur:
                cur.execute(sql_query, tuple(params_full))
                rows = cur.fetchall()
                results = []
                for r in rows:
                    item = dict(r)
                    if "similarity" in item:
                        item["similarity"] = float(item["similarity"])
                    results.append(item)
                return results

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory from scones_memories."""
        sql_query = "DELETE FROM scones_memories WHERE id = %s;"
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, (memory_id,))
                return cur.rowcount > 0

    # -------------------------------------------------------------------------
    # scones_error_solutions CRUD & Vector Search
    # -------------------------------------------------------------------------

    def upsert_error_solution(
        self,
        id: str,
        error_text: str,
        solution_text: str,
        error_signature: Optional[str] = None,
        root_cause: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        created_at: Optional[float] = None,
        success_rate: float = 1.0
    ) -> Dict[str, Any]:
        """Upsert an error solution into scones_error_solutions."""
        meta = metadata or {}
        ts = created_at or time.time()
        emb_str = f"[{','.join(str(x) for x in embedding)}]" if embedding else None

        sql_query = """
        INSERT INTO scones_error_solutions (
            id, error_signature, error_text, solution_text, root_cause, metadata, embedding, created_at, success_rate
        )
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s::vector, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            error_signature = EXCLUDED.error_signature,
            error_text = EXCLUDED.error_text,
            solution_text = EXCLUDED.solution_text,
            root_cause = EXCLUDED.root_cause,
            metadata = EXCLUDED.metadata,
            embedding = EXCLUDED.embedding,
            created_at = EXCLUDED.created_at,
            success_rate = EXCLUDED.success_rate;
        """

        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    sql_query,
                    (
                        id,
                        error_signature,
                        error_text,
                        solution_text,
                        root_cause,
                        json.dumps(meta),
                        emb_str,
                        float(ts),
                        float(success_rate)
                    )
                )

        return {
            "id": id,
            "error_signature": error_signature,
            "error_text": error_text,
            "solution_text": solution_text,
            "root_cause": root_cause,
            "metadata": meta,
            "embedding": embedding,
            "created_at": ts,
            "success_rate": success_rate
        }

    def get_error_solution(self, solution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific error solution by ID."""
        sql_query = """
        SELECT id, error_signature, error_text, solution_text, root_cause, metadata, created_at, success_rate
        FROM scones_error_solutions
        WHERE id = %s;
        """
        with self.connection() as conn:
            with conn.cursor(cursor_factory=self._get_dict_cursor_factory()) as cur:
                cur.execute(sql_query, (solution_id,))
                row = cur.fetchone()
                if not row:
                    return None
                return dict(row)

    def query_error_solutions(
        self,
        query_embedding: Optional[List[float]] = None,
        error_signature: Optional[str] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        limit: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Query error solutions using HNSW cosine distance search with tenant isolation.
        """
        where_clauses = ["1=1"]
        params: List[Any] = []

        if error_signature:
            where_clauses.append("error_signature = %s")
            params.append(error_signature)
        if tenant_id:
            where_clauses.append("metadata->>'tenant_id' = %s")
            params.append(tenant_id)
        if workspace_id:
            where_clauses.append("metadata->>'workspace_id' = %s")
            params.append(workspace_id)

        if query_embedding:
            emb_str = f"[{','.join(str(x) for x in query_embedding)}]"
            where_sql = " AND ".join(where_clauses)
            sql_query = f"""
            SELECT id, error_signature, error_text, solution_text, root_cause, metadata, created_at, success_rate,
                   1.0 - (embedding <=> %s::vector) AS similarity
            FROM scones_error_solutions
            WHERE {where_sql}
            """
            params_full: List[Any] = [emb_str] + list(params)

            if min_similarity > 0.0:
                sql_query += " AND (1.0 - (embedding <=> %s::vector)) >= %s"
                params_full.extend([emb_str, float(min_similarity)])

            sql_query += """
            ORDER BY embedding <=> %s::vector ASC
            LIMIT %s;
            """
            params_full.extend([emb_str, int(limit)])
        else:
            where_sql = " AND ".join(where_clauses)
            sql_query = f"""
            SELECT id, error_signature, error_text, solution_text, root_cause, metadata, created_at, success_rate, 1.0 AS similarity
            FROM scones_error_solutions
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT %s;
            """
            params_full: List[Any] = list(params) + [int(limit)]

        with self.connection() as conn:
            with conn.cursor(cursor_factory=self._get_dict_cursor_factory()) as cur:
                cur.execute(sql_query, tuple(params_full))
                rows = cur.fetchall()
                results = []
                for r in rows:
                    item = dict(r)
                    if "similarity" in item:
                        item["similarity"] = float(item["similarity"])
                    results.append(item)
                return results

    def delete_error_solution(self, solution_id: str) -> bool:
        """Delete an error solution from scones_error_solutions."""
        sql_query = "DELETE FROM scones_error_solutions WHERE id = %s;"
        with self.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_query, (solution_id,))
                return cur.rowcount > 0

    # -------------------------------------------------------------------------
    # Unified PostgreSQL Hybrid Search (pgvector + tsvector + SQL RRF)
    # -------------------------------------------------------------------------

    def hybrid_search_error_solutions(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        top_k: int = 20,
        candidate_limit: int = 50,
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Unified PostgreSQL Hybrid Search (pgvector + tsvector + RRF Reranking) for error solutions.
        Combines dense HNSW cosine similarity distance with sparse tsvector lexical matching via SQL CTE RRF.
        """
        if not query:
            return []

        q_vec = query_vector or generate_embedding(query, dim=self.vector_dim)
        emb_str = f"[{','.join(str(x) for x in q_vec)}]"

        if not self.is_healthy():
            logger.info("PgVector DB not connected; returning empty hybrid search list.")
            return []

        sql_query = """
        WITH
        fulltext AS (
          SELECT id, ROW_NUMBER() OVER (
            ORDER BY ts_rank_cd(search_vector, plainto_tsquery('english', %s)) DESC
          ) AS r
          FROM scones_error_solutions
          WHERE search_vector @@ plainto_tsquery('english', %s)
            AND (%s::text IS NULL OR metadata->>'tenant_id' = %s)
            AND (%s::text IS NULL OR metadata->>'workspace_id' = %s)
          LIMIT %s
        ),
        semantic AS (
          SELECT id, ROW_NUMBER() OVER (
            ORDER BY embedding <=> %s::vector ASC
          ) AS r
          FROM scones_error_solutions
          WHERE (%s::text IS NULL OR metadata->>'tenant_id' = %s)
            AND (%s::text IS NULL OR metadata->>'workspace_id' = %s)
          LIMIT %s
        ),
        rrf AS (
          SELECT id, 1.0 / (%s + r) AS s FROM fulltext
          UNION ALL
          SELECT id, 1.0 / (%s + r) AS s FROM semantic
        )
        SELECT
          m.id,
          SUM(s) AS rrf_score,
          m.error_signature,
          m.error_text,
          m.solution_text,
          m.root_cause,
          m.metadata,
          m.created_at,
          m.success_rate
        FROM rrf
        JOIN scones_error_solutions AS m USING (id)
        GROUP BY m.id, m.error_signature, m.error_text, m.solution_text, m.root_cause, m.metadata, m.created_at, m.success_rate
        ORDER BY rrf_score DESC
        LIMIT %s;
        """

        try:
            with self.connection() as conn:
                with conn.cursor(cursor_factory=self._get_dict_cursor_factory()) as cur:
                    cur.execute(
                        sql_query,
                        (
                            query, query, tenant_id, tenant_id, workspace_id, workspace_id, candidate_limit,
                            emb_str, tenant_id, tenant_id, workspace_id, workspace_id, candidate_limit,
                            rrf_k, rrf_k,
                            top_k
                        )
                    )
                    rows = cur.fetchall()
                    results = []
                    for r in rows:
                        item = dict(r)
                        if "rrf_score" in item:
                            item["rrf_score"] = float(item["rrf_score"])
                        results.append(item)
                    return results
        except Exception as e:
            logger.error("Error executing SQL hybrid search for error solutions: %s", e)
            return []

    def hybrid_search_memories(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        top_k: int = 20,
        candidate_limit: int = 50,
        rrf_k: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Unified PostgreSQL Hybrid Search (pgvector + tsvector + RRF Reranking) for scones_memories.
        """
        if not query:
            return []

        q_vec = query_vector or generate_embedding(query, dim=self.vector_dim)
        emb_str = f"[{','.join(str(x) for x in q_vec)}]"

        if not self.is_healthy():
            logger.info("PgVector DB not connected; returning empty hybrid search list.")
            return []

        sql_query = """
        WITH
        fulltext AS (
          SELECT id, ROW_NUMBER() OVER (
            ORDER BY ts_rank_cd(search_vector, plainto_tsquery('english', %s)) DESC
          ) AS r
          FROM scones_memories
          WHERE search_vector @@ plainto_tsquery('english', %s)
            AND (%s::text IS NULL OR metadata->>'tenant_id' = %s)
            AND (%s::text IS NULL OR metadata->>'workspace_id' = %s)
          LIMIT %s
        ),
        semantic AS (
          SELECT id, ROW_NUMBER() OVER (
            ORDER BY embedding <=> %s::vector ASC
          ) AS r
          FROM scones_memories
          WHERE (%s::text IS NULL OR metadata->>'tenant_id' = %s)
            AND (%s::text IS NULL OR metadata->>'workspace_id' = %s)
          LIMIT %s
        ),
        rrf AS (
          SELECT id, 1.0 / (%s + r) AS s FROM fulltext
          UNION ALL
          SELECT id, 1.0 / (%s + r) AS s FROM semantic
        )
        SELECT
          m.id,
          SUM(s) AS rrf_score,
          m.topic,
          m.content,
          m.importance,
          m.metadata,
          m.created_at
        FROM rrf
        JOIN scones_memories AS m USING (id)
        GROUP BY m.id, m.topic, m.content, m.importance, m.metadata, m.created_at
        ORDER BY rrf_score DESC
        LIMIT %s;
        """

        try:
            with self.connection() as conn:
                with conn.cursor(cursor_factory=self._get_dict_cursor_factory()) as cur:
                    cur.execute(
                        sql_query,
                        (
                            query, query, tenant_id, tenant_id, workspace_id, workspace_id, candidate_limit,
                            emb_str, tenant_id, tenant_id, workspace_id, workspace_id, candidate_limit,
                            rrf_k, rrf_k,
                            top_k
                        )
                    )
                    rows = cur.fetchall()
                    results = []
                    for r in rows:
                        item = dict(r)
                        if "rrf_score" in item:
                            item["rrf_score"] = float(item["rrf_score"])
                        results.append(item)
                    return results
        except Exception as e:
            logger.error("Error executing SQL hybrid search for memories: %s", e)
            return []

    def hybrid_search(
        self,
        query: str,
        query_vector: Optional[List[float]] = None,
        tenant_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        top_k: int = 20,
        table_name: str = "scones_error_solutions"
    ) -> List[Dict[str, Any]]:
        """Generic entry point for PostgreSQL Hybrid Search (pgvector + tsvector + RRF)."""
        if table_name == "scones_memories":
            return self.hybrid_search_memories(
                query=query,
                query_vector=query_vector,
                tenant_id=tenant_id,
                workspace_id=workspace_id,
                top_k=top_k
            )
        return self.hybrid_search_error_solutions(
            query=query,
            query_vector=query_vector,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            top_k=top_k
        )

    def search_memories(self, *args, **kwargs):
        """Alias for query_memories."""
        return self.query_memories(*args, **kwargs)

    def search_error_solutions(self, *args, **kwargs):
        """Alias for query_error_solutions."""
        return self.query_error_solutions(*args, **kwargs)

    def close(self):
        """Close connection pool and cleanup resources."""
        if self._pool:
            try:
                self._pool.closeall()
            except Exception:
                pass
            self._pool = None
        self._is_available = False
