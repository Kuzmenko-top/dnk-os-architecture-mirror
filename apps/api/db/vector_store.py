# --- DNK-MRH-HEADER ---
# mrh_id: "apps/api/db/vector_store.py"
# purpose: "PostgreSQL Vector Store implementation supporting pgvector Dense (1536-dim) and tsvector Sparse embeddings with tenant/workspace isolation"
# canonical_source: true
# alters_files: []
# triggers_tasks: ["DNK-VECTOR-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# author: "DNK-e.com Maksym"
# --- END DNK-MRH-HEADER ---

import os
import time
import json
import uuid
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

logger = logging.getLogger("VectorStore")

try:
    import psycopg2
    from psycopg2 import pool as psycopg2_pool  # type: ignore
    from psycopg2 import extras as psycopg2_extras  # type: ignore
    PSYCOPG2_AVAILABLE = True
except ImportError:
    psycopg2 = None  # type: ignore
    psycopg2_pool = None  # type: ignore
    psycopg2_extras = None  # type: ignore
    PSYCOPG2_AVAILABLE = False


def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two float vectors in pure Python."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(dot / (norm_a * norm_b))


class VectorStore:
    """
    Production-grade VectorStore for PostgreSQL pgvector (Dense 1536-dim) & tsvector (Sparse).
    Includes in-memory resilient fallback engine for standalone test harnesses.
    """

    def __init__(
        self,
        db_url: Optional[str] = None,
        min_connections: int = 1,
        max_connections: int = 10,
        statement_timeout_ms: int = 500,
    ):
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.statement_timeout_ms = statement_timeout_ms
        self.pool: Optional[Any] = None
        
        # In-memory storage fallback for standalone/unit testing environments
        self._memory_db: Dict[str, Dict[str, Any]] = {}
        self._collection_stats: Dict[str, Dict[str, Any]] = {}

        if self.db_url and PSYCOPG2_AVAILABLE and psycopg2_pool is not None:
            try:
                self.pool = psycopg2_pool.SimpleConnectionPool(
                    min_connections,
                    max_connections,
                    self.db_url,
                    connect_timeout=3,
                )
                self._init_postgres_schema()
                logger.info("Connected to PostgreSQL pgvector backend successfully.")
            except Exception as exc:
                logger.warning(f"PostgreSQL pool init failed ({exc}), falling back to memory backend.")
                self.pool = None

    def _init_postgres_schema(self) -> None:
        """Initialize PostgreSQL table schema and indexes for pgvector & tsvector."""
        if not self.pool:
            return

        conn = self.pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS vector_memory_embeddings (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        tenant_id VARCHAR(100) NOT NULL,
                        workspace_id VARCHAR(100) NOT NULL,
                        memory_type VARCHAR(50) NOT NULL,
                        content TEXT NOT NULL,
                        content_tokens INTEGER,
                        embedding_dense vector(1536),
                        embedding_sparse tsvector,
                        metadata JSONB,
                        embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-large',
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_vector_memory_tenant_workspace 
                    ON vector_memory_embeddings (tenant_id, workspace_id);
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_vector_memory_type 
                    ON vector_memory_embeddings (memory_type);
                    """
                )
                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_vector_memory_sparse 
                    ON vector_memory_embeddings USING GIN (embedding_sparse);
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS vector_collection_stats (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        workspace_id VARCHAR(100) NOT NULL UNIQUE,
                        total_points INTEGER NOT NULL DEFAULT 0,
                        total_size_bytes BIGINT NOT NULL DEFAULT 0,
                        last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )
                conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.error(f"Failed to initialize PostgreSQL schema: {exc}")
        finally:
            self.pool.putconn(conn)

    def ingest_vector(self, point: Dict[str, Any]) -> str:
        """
        Ingest a single vector record (Dense + Sparse) with tenant/workspace scoping.
        """
        record_id = point.get("id") or str(uuid.uuid4())
        tenant_id = str(point.get("tenant_id", "default_tenant"))
        workspace_id = str(point.get("workspace_id", "default_workspace"))
        memory_type = str(point.get("memory_type", "document"))
        content = str(point.get("content", ""))
        content_tokens = point.get("content_tokens") or len(content.split())
        embedding_dense = point.get("embedding_dense") or []
        embedding_sparse = point.get("embedding_sparse")
        metadata = point.get("metadata") or {}
        embedding_model = str(point.get("embedding_model", "text-embedding-3-large"))
        now_iso = datetime.now(timezone.utc).isoformat()

        if self.pool:
            conn = self.pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute(f"SET statement_timeout = {self.statement_timeout_ms};")
                    dense_str = f"[{','.join(map(str, embedding_dense))}]" if embedding_dense else None
                    cur.execute(
                        """
                        INSERT INTO vector_memory_embeddings (
                            id, tenant_id, workspace_id, memory_type, content, content_tokens,
                            embedding_dense, embedding_sparse, metadata, embedding_model, created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, to_tsvector('english', %s), %s, %s, NOW(), NOW()
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            content_tokens = EXCLUDED.content_tokens,
                            embedding_dense = EXCLUDED.embedding_dense,
                            embedding_sparse = EXCLUDED.embedding_sparse,
                            metadata = EXCLUDED.metadata,
                            updated_at = NOW();
                        """,
                        (
                            record_id,
                            tenant_id,
                            workspace_id,
                            memory_type,
                            content,
                            content_tokens,
                            dense_str,
                            content,
                            json.dumps(metadata),
                            embedding_model,
                        ),
                    )
                    conn.commit()
            except Exception as exc:
                conn.rollback()
                logger.error(f"PostgreSQL vector ingestion failed: {exc}")
                raise exc
            finally:
                self.pool.putconn(conn)
        else:
            # Memory backend store
            self._memory_db[record_id] = {
                "id": record_id,
                "tenant_id": tenant_id,
                "workspace_id": workspace_id,
                "memory_type": memory_type,
                "content": content,
                "content_tokens": content_tokens,
                "embedding_dense": embedding_dense,
                "embedding_sparse": embedding_sparse,
                "metadata": metadata,
                "embedding_model": embedding_model,
                "created_at": now_iso,
                "updated_at": now_iso,
            }

        # Update stats
        self._update_stats(workspace_id)
        return record_id

    def ingest_batch(self, points: List[Dict[str, Any]]) -> List[str]:
        """
        Ingest a batch of vector points atomically.
        """
        inserted_ids = []
        for pt in points:
            vid = self.ingest_vector(pt)
            inserted_ids.append(vid)
        return inserted_ids

    def delete_vector(self, vector_id: str, tenant_id: str, workspace_id: str) -> bool:
        """
        Delete a vector record ensuring tenant & workspace isolation.
        """
        if self.pool:
            conn = self.pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute(f"SET statement_timeout = {self.statement_timeout_ms};")
                    cur.execute(
                        """
                        DELETE FROM vector_memory_embeddings
                        WHERE id = %s AND tenant_id = %s AND workspace_id = %s;
                        """,
                        (vector_id, tenant_id, workspace_id),
                    )
                    deleted = cur.rowcount > 0
                    conn.commit()
                    self._update_stats(workspace_id)
                    return deleted
            except Exception as exc:
                conn.rollback()
                logger.error(f"PostgreSQL vector delete failed: {exc}")
                return False
            finally:
                self.pool.putconn(conn)
        else:
            if vector_id in self._memory_db:
                item = self._memory_db[vector_id]
                if item.get("tenant_id") == tenant_id and item.get("workspace_id") == workspace_id:
                    del self._memory_db[vector_id]
                    self._update_stats(workspace_id)
                    return True
            return False

    def query_dense(
        self,
        query_dense_vector: List[float],
        tenant_id: str,
        workspace_id: str,
        top_k: int = 10,
        memory_type: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Pure Dense Vector search via cosine similarity (pgvector cosine / in-memory cosine).
        """
        if not query_dense_vector:
            return []

        if self.pool and PSYCOPG2_AVAILABLE and psycopg2_extras is not None:
            conn = self.pool.getconn()
            try:
                with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                    cur.execute(f"SET statement_timeout = {self.statement_timeout_ms};")
                    dense_str = f"[{','.join(map(str, query_dense_vector))}]"
                    where_clauses = ["tenant_id = %s", "workspace_id = %s", "embedding_dense IS NOT NULL"]
                    params: List[Any] = [tenant_id, workspace_id]

                    if memory_type:
                        where_clauses.append("memory_type = %s")
                        params.append(memory_type)

                    params.insert(0, dense_str)  # for similarity distance
                    where_sql = " AND ".join(where_clauses)
                    sql = f"""
                        SELECT id, tenant_id, workspace_id, memory_type, content, metadata,
                               (1 - (embedding_dense <=> %s::vector)) as score
                        FROM vector_memory_embeddings
                        WHERE {where_sql}
                        ORDER BY embedding_dense <=> %s::vector ASC
                        LIMIT %s;
                    """
                    params.append(dense_str)
                    params.append(top_k)
                    cur.execute(sql, tuple(params))
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
            except Exception as exc:
                logger.error(f"PostgreSQL dense search failed: {exc}")
                return []
            finally:
                self.pool.putconn(conn)
        else:
            candidates = []
            for doc in self._memory_db.values():
                if doc["tenant_id"] != tenant_id or doc["workspace_id"] != workspace_id:
                    continue
                if memory_type and doc["memory_type"] != memory_type:
                    continue
                if filter_metadata:
                    m = doc.get("metadata", {})
                    if not all(m.get(k) == v for k, v in filter_metadata.items()):
                        continue

                doc_vec = doc.get("embedding_dense")
                if not doc_vec:
                    continue

                sim = _cosine_similarity(query_dense_vector, doc_vec)
                candidates.append({
                    "id": doc["id"],
                    "tenant_id": doc["tenant_id"],
                    "workspace_id": doc["workspace_id"],
                    "memory_type": doc["memory_type"],
                    "content": doc["content"],
                    "metadata": doc.get("metadata", {}),
                    "score": round(sim, 6),
                })
            candidates.sort(key=lambda x: x["score"], reverse=True)
            return candidates[:top_k]

    def query_sparse(
        self,
        query_text: str,
        tenant_id: str,
        workspace_id: str,
        top_k: int = 10,
        memory_type: Optional[str] = None,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Pure Sparse Lexical search via tsvector full-text matching / token BM25 scoring.
        """
        if not query_text or not query_text.strip():
            return []

        if self.pool and PSYCOPG2_AVAILABLE and psycopg2_extras is not None:
            conn = self.pool.getconn()
            try:
                with conn.cursor(cursor_factory=psycopg2_extras.RealDictCursor) as cur:
                    cur.execute(f"SET statement_timeout = {self.statement_timeout_ms};")
                    where_clauses = [
                        "tenant_id = %s",
                        "workspace_id = %s",
                        "embedding_sparse @@ plainto_tsquery('english', %s)",
                    ]
                    params: List[Any] = [tenant_id, workspace_id, query_text]

                    if memory_type:
                        where_clauses.append("memory_type = %s")
                        params.append(memory_type)

                    where_sql = " AND ".join(where_clauses)
                    sql = f"""
                        SELECT id, tenant_id, workspace_id, memory_type, content, metadata,
                               ts_rank_cd(embedding_sparse, plainto_tsquery('english', %s)) as score
                        FROM vector_memory_embeddings
                        WHERE {where_sql}
                        ORDER BY score DESC
                        LIMIT %s;
                    """
                    cur.execute(sql, tuple([query_text] + params + [top_k]))
                    rows = cur.fetchall()
                    return [dict(r) for r in rows]
            except Exception as exc:
                logger.error(f"PostgreSQL sparse search failed: {exc}")
                return []
            finally:
                self.pool.putconn(conn)
        else:
            query_terms = set(query_text.lower().replace(",", " ").replace(".", " ").split())
            if not query_terms:
                return []

            candidates = []
            for doc in self._memory_db.values():
                if doc["tenant_id"] != tenant_id or doc["workspace_id"] != workspace_id:
                    continue
                if memory_type and doc["memory_type"] != memory_type:
                    continue
                if filter_metadata:
                    m = doc.get("metadata", {})
                    if not all(m.get(k) == v for k, v in filter_metadata.items()):
                        continue

                doc_words = doc.get("content", "").lower().replace(",", " ").replace(".", " ").split()
                if not doc_words:
                    continue

                matched = sum(1 for w in doc_words if w in query_terms)
                if matched > 0:
                    # BM25-like normalized term frequency score
                    tf = matched / (len(doc_words) + 1.0)
                    overlap = len(set(doc_words) & query_terms) / float(len(query_terms))
                    score = (0.7 * overlap) + (0.3 * tf)
                    candidates.append({
                        "id": doc["id"],
                        "tenant_id": doc["tenant_id"],
                        "workspace_id": doc["workspace_id"],
                        "memory_type": doc["memory_type"],
                        "content": doc["content"],
                        "metadata": doc.get("metadata", {}),
                        "score": round(score, 6),
                    })
            candidates.sort(key=lambda x: x["score"], reverse=True)
            return candidates[:top_k]

    def _update_stats(self, workspace_id: str) -> None:
        """Internal helper to calculate collection stats."""
        total_pts = sum(1 for d in self._memory_db.values() if d.get("workspace_id") == workspace_id)
        total_size = sum(len(d.get("content", "").encode("utf-8")) for d in self._memory_db.values() if d.get("workspace_id") == workspace_id)
        self._collection_stats[workspace_id] = {
            "workspace_id": workspace_id,
            "total_points": total_pts,
            "total_size_bytes": total_size,
            "last_updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def get_stats(self, workspace_id: str) -> Dict[str, Any]:
        """Get collection metrics for a workspace."""
        if workspace_id in self._collection_stats:
            return self._collection_stats[workspace_id]
        return {
            "workspace_id": workspace_id,
            "total_points": 0,
            "total_size_bytes": 0,
            "last_updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def list_collections(self, workspace_id: str) -> List[Dict[str, Any]]:
        """List active memory collections / types within a workspace."""
        types_count: Dict[str, int] = {}
        for d in self._memory_db.values():
            if d.get("workspace_id") == workspace_id:
                mtype = d.get("memory_type", "default")
                types_count[mtype] = types_count.get(mtype, 0) + 1
        return [
            {"collection_name": mtype, "count": count, "workspace_id": workspace_id}
            for mtype, count in types_count.items()
        ]
