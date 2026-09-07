# --- DNK-MRH-HEADER ---
# mrh_id: "tests/verification/test_lakehouse_bi_router.py"
# purpose: "Integration Tests for Lakehouse BI Router, AI Analyst NL2SQL & Swarm DAG Execution."
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-02"
# author: "Antigravity (Mentor) & Gerych Prime"
# license: "DNK-INTERNAL"
# --- END DNK-MRH-HEADER ---

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)


def test_lakehouse_raw_query_endpoint():
    resp = client.post("/api/v3/lakehouse/query", json={
        "sql_query": "SELECT customer_id, gross_amount FROM shopify_orders ORDER BY gross_amount DESC"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "columns" in data
    assert "rows" in data
    assert len(data["rows"]) == 3
    assert data["columns"] == ["customer_id", "gross_amount"]
    assert data["execution_time_ms"] >= 0.0


def test_lakehouse_nl2sql_ai_analyst_endpoint():
    resp = client.post("/api/v3/lakehouse/nl2sql", json={
        "question": "What is the total revenue by customer?"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "question" in data
    assert "reasoning_plan" in data
    assert len(data["reasoning_plan"]) == 4
    assert data["chart_type"] == "bar"
    assert "shopify_orders" in data["generated_sql"]
    assert data["result"]["row_count"] > 0


def test_lakehouse_semantic_metrics_endpoint():
    resp = client.get("/api/v3/lakehouse/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["metrics_count"] >= 2
    metric_names = [m["name"] for m in data["metrics"]]
    assert "total_revenue" in metric_names
    assert "avg_task_latency" in metric_names


def test_lakehouse_swarm_workflow_create_and_execute():
    # 1. Create Workflow
    create_resp = client.post("/api/v3/lakehouse/workflows", json={
        "title": "Shopify Analytics & Quality Gate DAG",
        "nodes": [
            {"id": "n1", "node_type": "agent", "name": "Planner", "config": {"agent": "gerych_prime"}},
            {"id": "n2", "node_type": "tool", "name": "Query Engine", "config": {"tool_name": "duckdb_query"}},
            {"id": "n3", "node_type": "condition", "name": "Revenue Threshold", "config": {"expression": "rev > 0"}}
        ],
        "edges": [
            {"id": "e1", "source_node_id": "n1", "target_node_id": "n2"},
            {"id": "e2", "source_node_id": "n2", "target_node_id": "n3"}
        ]
    })
    assert create_resp.status_code == 201
    wf = create_resp.json()
    assert "workflow_id" in wf
    wf_id = wf["workflow_id"]

    # 2. Execute Workflow
    exec_resp = client.post("/api/v3/lakehouse/workflows/execute", json={
        "workflow_id": wf_id,
        "inputs": {"threshold": 100.0}
    })
    assert exec_resp.status_code == 200
    res = exec_resp.json()
    assert res["status"] == "success"
    assert res["steps_executed"] == 3
    assert "trace" in res
