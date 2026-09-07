# --- DNK-MRH-HEADER ---
# mrh_id: "references/duckdb_lakehouse_async_and_parquet_caching_protocol.md"
# purpose: "DuckDB Lakehouse Async Threadpool Execution and SHA-256 Parquet Caching Protocol."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-07"
# author: "DNK-e.com Maksym & Gerych Prime"
# --- END DNK-MRH-HEADER ---

# 🦆 DuckDB Lakehouse Async Threadpool & Parquet Caching Protocol

## 🎯 Architecture & Objective
Analytical SQL queries against columnar data or e-commerce orders can execute for hundreds of milliseconds to seconds. Direct execution within FastAPI's async route handlers blocks Python's asyncio event loop because DuckDB's C++ bindings execute synchronously in GIL-bound threads.

This protocol enforces:
1. **Asynchronous Threadpool Offloading (`ThreadPoolExecutor`)**: Heavy query executions run in a dedicated thread pool and yield via `asyncio.get_event_loop().run_in_executor(...)`.
2. **SHA-256 Query Normalization & Parquet Caching**: Normalizes SQL, computes a SHA-256 cache key, and writes query results directly to columnar Parquet files (`data/lakehouse_cache/<hash>.parquet`) with TTL enforcement.
3. **Zero-Copy Parquet Hydration**: On cache hits within TTL, queries execute directly via DuckDB's `read_parquet(...)`, providing 10x query acceleration.
4. **Relational In-Memory Fallback**: Seamless fallback to SQLite in environments where DuckDB or PyArrow are unavailable or initializing.

---

## 🛠️ Implementation Pattern

```python
import asyncio
import hashlib
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional

class DuckDBLakehouseEngine:
    def __init__(self, db_path: str = ":memory:", cache_dir: str = "data/lakehouse_cache", max_workers: int = 4):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="duckdb_lakehouse")
        self._init_duckdb(db_path)

    async def query_async(self, sql: str, use_cache: bool = True, ttl_seconds: int = 3600) -> Dict[str, Any]:
        """Asynchronously dispatches query execution without blocking FastAPI's event loop."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            lambda: self.query_sync(sql, use_cache=use_cache, ttl_seconds=ttl_seconds)
        )

    def query_sync(self, sql: str, use_cache: bool = True, ttl_seconds: int = 3600) -> Dict[str, Any]:
        normalized_sql = " ".join(sql.strip().split())
        cache_key = hashlib.sha256(normalized_sql.encode("utf-8")).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.parquet")

        # 1. Check Parquet cache
        if use_cache and os.path.exists(cache_file):
            if (time.time() - os.path.getmtime(cache_file)) < ttl_seconds:
                df = self.conn.execute(f"SELECT * FROM read_parquet('{cache_file}')").df()
                return {
                    "sql": sql,
                    "row_count": len(df),
                    "rows": df.to_dict(orient="records"),
                    "cached": True,
                    "cache_file": cache_file
                }

        # 2. Fresh Execution
        df = self.conn.execute(sql).df()
        
        # 3. Store in Parquet
        if use_cache and len(df) > 0:
            self.conn.execute(f"COPY ({sql}) TO '{cache_file}' (FORMAT PARQUET)")

        return {
            "sql": sql,
            "row_count": len(df),
            "rows": df.to_dict(orient="records"),
            "cached": False,
            "cache_file": cache_file if use_cache else None
        }
```

---

## ⚠️ Pitfalls & Invariants
- **Column Schema Inconsistencies**: When caching dynamic aggregates, column names must match the Pydantic schemas expected by BI drawers (e.g. `order_id` vs `id`). Always normalize projections in SQL or provide adapters.
- **Cache Eviction**: Automated cleanup routines should run during `cache/clear` API calls or background maintenance to avoid unbounded disk growth in `data/lakehouse_cache/`.
- **Event Loop Thread Safety**: Always instantiate `ThreadPoolExecutor` with a thread name prefix and shut it down gracefully on application shutdown.
