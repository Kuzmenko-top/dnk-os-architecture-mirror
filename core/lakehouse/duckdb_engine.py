# --- DNK-MRH-HEADER ---
# mrh_id: "core/lakehouse/duckdb_engine.py"
# purpose: "High-Performance Asynchronous DuckDB Lakehouse Engine with Parquet Caching & ThreadPool Offloading."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-LAKEHOUSE-ASYNC-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import asyncio
import hashlib
import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("dnk.lakehouse")

import sqlite3

try:
    import duckdb  # type: ignore[import-not-found]
    _DUCKDB_AVAILABLE = True
except ImportError:
    duckdb = None  # type: ignore[assignment]
    _DUCKDB_AVAILABLE = False


class LakehouseQueryResult(BaseModel):
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    execution_time_ms: float = 0.0
    row_count: int = 0
    engine: str = "duckdb"
    cached: bool = False
    cache_path: Optional[str] = None


class DuckDBLakehouseEngine:
    """
    High-performance Embedded DuckDB Lakehouse Engine:
    - ThreadPoolExecutor offloading to keep FastAPI event loop 100% non-blocking.
    - Automatic Parquet query caching for sub-millisecond repeated queries.
    - Analytical schema registration & seed data generation.
    - Natural language to SQL reasoning trace.
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        cache_dir: str = "data/lakehouse_cache",
        max_workers: int = 4,
    ):
        self.db_path = db_path
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="dnk_duckdb_worker"
        )
        self._init_database()

    def _init_database(self) -> None:
        """Initializes DuckDB or SQLite fallback connection and seed schemas."""
        with self._lock:
            if _DUCKDB_AVAILABLE and duckdb is not None:
                self._conn = duckdb.connect(self.db_path)
                self.engine_name = "duckdb-columnar"
                self._seed_duckdb_tables()
            else:
                self._conn = sqlite3.connect(":memory:", check_same_thread=False)
                self.engine_name = "sqlite-fallback"
                self._seed_sqlite_tables()
        logger.info(f"Initialized Lakehouse Engine ({self.engine_name}) at {self.db_path}")

    @property
    def is_duckdb(self) -> bool:
        return self.engine_name.startswith("duckdb")

    def _seed_duckdb_tables(self) -> None:
        cursor = self._conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopify_orders (
                order_id VARCHAR PRIMARY KEY,
                customer_id VARCHAR,
                product_name VARCHAR,
                revenue_usd DOUBLE,
                gross_amount DOUBLE,
                currency VARCHAR,
                status VARCHAR,
                created_at TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS agent_task_metrics (
                task_id VARCHAR PRIMARY KEY,
                agent_name VARCHAR,
                duration_ms DOUBLE,
                duration_seconds DOUBLE,
                tokens_spent INTEGER,
                status VARCHAR
            );
            CREATE TABLE IF NOT EXISTS swarm_token_ledger (
                entry_id VARCHAR PRIMARY KEY,
                sender_agent VARCHAR,
                recipient_agent VARCHAR,
                token_count INTEGER,
                category VARCHAR,
                timestamp TIMESTAMP
            );
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO shopify_orders VALUES 
            ('ord-1001', 'cust-01', 'AI Canvas Pro Subscription', 149.99, 149.99, 'USD', 'delivered', '2026-09-01 10:00:00'),
            ('ord-1002', 'cust-02', 'Liquid Theme FastPass Bundle', 289.50, 289.50, 'USD', 'delivered', '2026-09-01 14:30:00'),
            ('ord-1003', 'cust-01', 'Smart Ledger Migration Token', 75.00, 75.00, 'USD', 'pending', '2026-09-02 09:15:00');

            INSERT OR IGNORE INTO agent_task_metrics VALUES
            ('tsk-01', 'gerych_prime', 420.5, 0.42, 1250, 'completed'),
            ('tsk-02', 'dnk_shopify', 210.0, 0.21, 890, 'completed'),
            ('tsk-03', 'gerych_auditor', 150.2, 0.15, 450, 'completed'),
            ('tsk-04', 'dnk_dev_fullstack', 315.8, 0.31, 1600, 'completed'),
            ('tsk-05', 'gerych_builder', 180.4, 0.18, 720, 'completed');

            INSERT OR IGNORE INTO swarm_token_ledger VALUES
            ('led-01', 'gerych_prime', 'dnk_shopify', 1250, 'task_payload', '2026-09-05 10:00:00'),
            ('led-02', 'dnk_shopify', 'gerych_auditor', 890, 'artifact_review', '2026-09-05 10:05:00'),
            ('led-03', 'gerych_auditor', 'gerych_prime', 450, 'gate_report', '2026-09-05 10:07:00');
        """)

    def _seed_sqlite_tables(self) -> None:
        cursor = self._conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS shopify_orders (
                order_id TEXT PRIMARY KEY,
                customer_id TEXT,
                product_name TEXT,
                revenue_usd REAL,
                gross_amount REAL,
                currency TEXT,
                status TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS agent_task_metrics (
                task_id TEXT PRIMARY KEY,
                agent_name TEXT,
                duration_ms REAL,
                duration_seconds REAL,
                tokens_spent INTEGER,
                status TEXT
            );
            CREATE TABLE IF NOT EXISTS swarm_token_ledger (
                entry_id TEXT PRIMARY KEY,
                sender_agent TEXT,
                recipient_agent TEXT,
                token_count INTEGER,
                category TEXT,
                timestamp TEXT
            );
        """)
        cursor.executemany("INSERT OR IGNORE INTO shopify_orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
            ('ord-1001', 'cust-01', 'AI Canvas Pro Subscription', 149.99, 149.99, 'USD', 'delivered', '2026-09-01 10:00:00'),
            ('ord-1002', 'cust-02', 'Liquid Theme FastPass Bundle', 289.50, 289.50, 'USD', 'delivered', '2026-09-01 14:30:00'),
            ('ord-1003', 'cust-01', 'Smart Ledger Migration Token', 75.00, 75.00, 'USD', 'pending', '2026-09-02 09:15:00'),
        ])
        cursor.executemany("INSERT OR IGNORE INTO agent_task_metrics VALUES (?, ?, ?, ?, ?, ?)", [
            ('tsk-01', 'gerych_prime', 420.5, 0.42, 1250, 'completed'),
            ('tsk-02', 'dnk_shopify', 210.0, 0.21, 890, 'completed'),
            ('tsk-03', 'gerych_auditor', 150.2, 0.15, 450, 'completed'),
            ('tsk-04', 'dnk_dev_fullstack', 315.8, 0.31, 1600, 'completed'),
            ('tsk-05', 'gerych_builder', 180.4, 0.18, 720, 'completed'),
        ])
        cursor.executemany("INSERT OR IGNORE INTO swarm_token_ledger VALUES (?, ?, ?, ?, ?, ?)", [
            ('led-01', 'gerych_prime', 'dnk_shopify', 1250, 'task_payload', '2026-09-05 10:00:00'),
            ('led-02', 'dnk_shopify', 'gerych_auditor', 890, 'artifact_review', '2026-09-05 10:05:00'),
            ('led-03', 'gerych_auditor', 'gerych_prime', 450, 'gate_report', '2026-09-05 10:07:00'),
        ])
        self._conn.commit()

    def _get_cache_path(self, sql_query: str) -> Path:
        normalized = " ".join(sql_query.strip().lower().split())
        query_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return self.cache_dir / f"{query_hash}.parquet"

    def _is_cache_valid(self, cache_file: Path, ttl_seconds: int) -> bool:
        if not cache_file.exists():
            return False
        age = time.time() - cache_file.stat().st_mtime
        return age <= ttl_seconds

    def query_sync(
        self,
        sql_query: str,
        use_cache: bool = True,
        cache_ttl_seconds: int = 300
    ) -> LakehouseQueryResult:
        """
        Synchronously executes a SQL query with Parquet caching where supported.
        """
        start = time.time()
        is_select = bool(re.match(r"^\s*SELECT", sql_query, re.IGNORECASE))
        cache_file = self._get_cache_path(sql_query) if is_select and use_cache else None

        # Check Parquet Cache Hit (DuckDB only)
        if _DUCKDB_AVAILABLE and cache_file and self._is_cache_valid(cache_file, cache_ttl_seconds):
            try:
                with self._lock:
                    cached_cursor = self._conn.cursor()
                    res = cached_cursor.execute(f"SELECT * FROM read_parquet('{cache_file.as_posix()}')")
                    columns = [desc[0] for desc in res.description]
                    rows = res.fetchall()
                elapsed = round((time.time() - start) * 1000, 2)
                logger.debug(f"Lakehouse Parquet Cache HIT for query in {elapsed}ms: {cache_file.name}")
                return LakehouseQueryResult(
                    columns=columns,
                    rows=[list(r) for r in rows],
                    execution_time_ms=elapsed,
                    row_count=len(rows),
                    engine=f"{self.engine_name}-parquet-cached",
                    cached=True,
                    cache_path=str(cache_file)
                )
            except Exception as e:
                logger.warning(f"Failed to read Parquet cache {cache_file}: {e}. Falling back to live query.")

        # Cache Miss or Mutation Query -> Execute live
        with self._lock:
            if _DUCKDB_AVAILABLE:
                cursor = self._conn.cursor()
                res = cursor.execute(sql_query)
                if res.description:
                    columns = [desc[0] for desc in res.description]
                    rows = res.fetchall()
                else:
                    columns = []
                    rows = []
                
                # Materialize to Parquet Cache if eligible SELECT query
                if is_select and cache_file and len(rows) > 0:
                    try:
                        clean_sql = sql_query.rstrip(";").strip()
                        cursor.execute(f"COPY ({clean_sql}) TO '{cache_file.as_posix()}' (FORMAT PARQUET)")
                    except Exception as cache_err:
                        logger.warning(f"Could not write Parquet cache: {cache_err}")
            else:
                cursor = self._conn.cursor()
                cursor.execute(sql_query)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                else:
                    columns = []
                    rows = []
                if not is_select:
                    self._conn.commit()

        elapsed = round((time.time() - start) * 1000, 2)
        return LakehouseQueryResult(
            columns=columns,
            rows=[list(r) for r in rows],
            execution_time_ms=elapsed,
            row_count=len(rows),
            engine=self.engine_name,
            cached=False,
            cache_path=str(cache_file) if cache_file and cache_file.exists() else None
        )

    async def query_async(
        self,
        sql_query: str,
        use_cache: bool = True,
        cache_ttl_seconds: int = 300
    ) -> LakehouseQueryResult:
        """
        Asynchronously executes SQL via ThreadPoolExecutor to prevent event loop starvation.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self.query_sync,
            sql_query,
            use_cache,
            cache_ttl_seconds
        )

    def analyze_nl2sql_sync(self, question: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Translates analytical question into SQL with intent detection, reasoning plan, and chart spec.
        """
        q_lower = question.lower()
        if any(w in q_lower for w in ["revenue", "order", "sales", "gross"]):
            sql = "SELECT customer_id, SUM(gross_amount) as total_revenue, COUNT(*) as order_count FROM shopify_orders GROUP BY customer_id ORDER BY total_revenue DESC"
            chart_type = "bar"
            title = "Revenue by Customer"
        elif any(w in q_lower for w in ["latency", "agent", "token", "performance"]):
            sql = "SELECT agent_name, AVG(duration_ms) as avg_latency_ms, SUM(tokens_spent) as total_tokens FROM agent_task_metrics GROUP BY agent_name"
            chart_type = "line"
            title = "Agent Performance & Token Metrics"
        elif any(w in q_lower for w in ["ledger", "flow", "a2a", "mailbox"]):
            sql = "SELECT sender_agent, recipient_agent, SUM(token_count) as total_tokens, COUNT(*) as transfer_count FROM swarm_token_ledger GROUP BY sender_agent, recipient_agent"
            chart_type = "bar"
            title = "Swarm Token Transfers"
        else:
            sql = "SELECT * FROM shopify_orders LIMIT 10"
            chart_type = "table"
            title = "Raw Data Preview"

        result = self.query_sync(sql, use_cache=use_cache)
        return {
            "question": question,
            "sql_query": sql,
            "generated_sql": sql,
            "chart_type": chart_type,
            "chart_suggestion": chart_type,
            "title": title,
            "reasoning_plan": [
                f"1. Identified analytical intent: '{question}'",
                f"2. Synthesized Lakehouse query against schema",
                f"3. Executed via {result.engine} (cached={result.cached})",
                f"4. Rendered visual canvas recommendation: '{chart_type}'"
            ],
            "reasoning_steps": [
                f"Analyzed query intent for '{question}'",
                f"Generated SQL: {sql}",
                f"Execution engine: {result.engine}",
                f"Selected visualization: {chart_type}"
            ],
            "result": result.model_dump(),
            "query_results": result.model_dump(),
            "rows": result.rows,
            "columns": result.columns,
            "row_count": result.row_count,
            "cached": result.cached
        }

    # Aliases for sync methods
    query = query_sync
    analyze_nl2sql = analyze_nl2sql_sync

    async def analyze_nl2sql_async(self, question: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Asynchronous NL2SQL analysis.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._executor,
            self.analyze_nl2sql_sync,
            question,
            use_cache
        )

    def clear_cache(self) -> int:
        """Purges all cached Parquet query files."""
        count = 0
        for p in self.cache_dir.glob("*.parquet"):
            try:
                p.unlink()
                count += 1
            except OSError:
                pass
        return count


# Global Singleton Engine Instance
_global_lakehouse_engine: Optional[DuckDBLakehouseEngine] = None
_engine_init_lock = threading.Lock()


def get_lakehouse_engine() -> DuckDBLakehouseEngine:
    global _global_lakehouse_engine
    if _global_lakehouse_engine is None:
        with _engine_init_lock:
            if _global_lakehouse_engine is None:
                _global_lakehouse_engine = DuckDBLakehouseEngine()
    return _global_lakehouse_engine
