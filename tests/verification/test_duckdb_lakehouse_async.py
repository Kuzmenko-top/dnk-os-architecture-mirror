# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_duckdb_lakehouse_async.py"
# purpose: "Verification test suite for DuckDB Lakehouse Async Engine, Parquet Caching, and BI Router."
# canonical_source: true
# alters_files: []
# triggers_tasks: ["TASK-LAKEHOUSE-ASYNC-001"]
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-06"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import os
import shutil
import pytest
from starlette.testclient import TestClient

from core.lakehouse.duckdb_engine import DuckDBLakehouseEngine, get_lakehouse_engine
from apps.api.main import app


@pytest.fixture(scope="module")
def lakehouse_engine():
    cache_dir = "data/test_lakehouse_cache"
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir, ignore_errors=True)
    engine = DuckDBLakehouseEngine(db_path=":memory:", cache_dir=cache_dir)
    yield engine
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir, ignore_errors=True)


@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


def test_engine_initialization(lakehouse_engine):
    assert lakehouse_engine.engine_name in ("duckdb-columnar", "sqlite-fallback")
    assert lakehouse_engine.is_duckdb is True


def test_sync_query(lakehouse_engine):
    sql = "SELECT order_id, product_name, revenue_usd FROM shopify_orders WHERE status = 'delivered' ORDER BY revenue_usd DESC"
    result = lakehouse_engine.query(sql, use_cache=False)
    assert result.row_count > 0
    assert "revenue_usd" in result.columns
    assert result.cached is False


@pytest.mark.asyncio
async def test_async_query_and_parquet_caching(lakehouse_engine):
    sql = "SELECT product_name, sum(revenue_usd) as total_rev FROM shopify_orders GROUP BY product_name ORDER BY total_rev DESC"
    
    # 1. First execution: cache miss, runs query, writes Parquet cache
    result1 = await lakehouse_engine.query_async(sql, use_cache=True)
    assert result1.row_count > 0
    assert result1.cached is False
    assert result1.cache_path is not None
    assert os.path.exists(result1.cache_path)
    assert result1.cache_path.endswith(".parquet")

    # 2. Second execution: cache hit, reads from Parquet
    result2 = await lakehouse_engine.query_async(sql, use_cache=True)
    assert result2.row_count == result1.row_count
    assert result2.columns == result1.columns
    assert result2.cached is True

    # 3. Clear cache
    cleared = lakehouse_engine.clear_cache()
    assert cleared >= 1
    assert not os.path.exists(result1.cache_path)

    # 4. Third execution: cache miss again after clearing
    result3 = await lakehouse_engine.query_async(sql, use_cache=True)
    assert result3.cached is False


@pytest.mark.asyncio
async def test_nl2sql_reasoning_trace(lakehouse_engine):
    question = "What is the total revenue by product?"
    analysis = await lakehouse_engine.analyze_nl2sql_async(question, use_cache=True)
    assert "generated_sql" in analysis
    assert "reasoning_steps" in analysis
    assert "chart_suggestion" in analysis
    assert "query_results" in analysis
    assert len(analysis["reasoning_steps"]) >= 2
    assert analysis["query_results"]["row_count"] > 0


def test_lakehouse_bi_router_endpoints(api_client):
    # Query endpoint
    query_payload = {
        "sql_query": "SELECT * FROM agent_task_metrics ORDER BY duration_seconds ASC",
        "use_cache": True,
        "cache_ttl_seconds": 60
    }
    resp = api_client.post("/api/v3/lakehouse/query", json=query_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "columns" in data
    assert "rows" in data
    assert len(data["rows"]) > 0

    # NL2SQL endpoint
    nl2sql_payload = {
        "question": "Which tasks took the longest duration?"
    }
    resp_nl2sql = api_client.post("/api/v3/lakehouse/nl2sql", json=nl2sql_payload)
    assert resp_nl2sql.status_code == 200
    nl_data = resp_nl2sql.json()
    assert "generated_sql" in nl_data
    assert "query_results" in nl_data

    # Cache clear endpoint
    resp_clear = api_client.post("/api/v3/lakehouse/cache/clear")
    assert resp_clear.status_code == 200
    clear_data = resp_clear.json()
    assert clear_data["status"] == "success"
