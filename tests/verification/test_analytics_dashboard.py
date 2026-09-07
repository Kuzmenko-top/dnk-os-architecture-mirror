# --- DNK-MRH-HEADER ---
# mrh_id: "test_analytics_dashboard"
# purpose: "Automated verification test suite for Analytics API endpoints and Frontend Components"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-12"
# --- END DNK-MRH-HEADER ---

import sys
import pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2] # DNK OS
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

import pytest
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)

def test_overview_endpoint():
    """1. test_overview_endpoint — загальна статистика."""
    response = client.get("/api/analytics/overview?period_days=7", headers={"X-API-Key": "dnk_secret_prod_key_2026"})
    assert response.status_code == 200
    data = response.json()
    assert "total_runs" in data
    assert "success_rate" in data
    assert "avg_duration_seconds" in data
    assert "total_errors" in data
    assert "top_error_types" in data
    assert isinstance(data["top_error_types"], list)

def test_agent_performance_endpoint():
    """2. test_agent_performance_endpoint — продуктивність агента."""
    agent_id = "c25db31a-e8f1-4dbd-8153-ba1473fb78ca"
    response = client.get(f"/api/analytics/agents/{agent_id}/performance?period_days=7", headers={"X-API-Key": "dnk_secret_prod_key_2026"})
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == agent_id
    assert "total_runs" in data
    assert "success_rate" in data
    assert "avg_duration_seconds" in data
    assert "tasks_by_type" in data
    assert "errors_by_type" in data

def test_bottlenecks_endpoint():
    """3. test_bottlenecks_endpoint — вузькі місця."""
    response = client.get("/api/analytics/bottlenecks?period_days=7", headers={"X-API-Key": "dnk_secret_prod_key_2026"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "task_type" in first
        assert "avg_duration_seconds" in first
        assert "failure_rate" in first
        assert "count" in first

def test_timeline_endpoint():
    """4. test_timeline_endpoint — таймлайн."""
    response = client.get("/api/analytics/timeline?period_days=7", headers={"X-API-Key": "dnk_secret_prod_key_2026"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "timestamp" in first
        assert "runs_count" in first
        assert "success_count" in first
        assert "error_count" in first

def test_recommendations_endpoint():
    """5. test_recommendations_endpoint — рекомендації з Knowledge Base."""
    response = client.get("/api/analytics/recommendations", headers={"X-API-Key": "dnk_secret_prod_key_2026"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    first = data[0]
    assert "category" in first
    assert "description" in first
    assert "priority" in first
    assert "estimated_impact" in first

def test_frontend_overview():
    """6. test_frontend_overview — рендер OverviewCard."""
    # Verify that the OverviewCard TSX file exists and contains core UI parameters
    path = ROOT / "apps/web/components/analytics/OverviewCard.tsx"
    assert path.exists(), f"OverviewCard file missing at: {path}"
    
    text = path.read_text(encoding="utf-8")
    assert "totalRuns" in text
    assert "successRate" in text
    assert "avgDuration" in text
    assert "totalErrors" in text
    assert "Всього Запусків" in text

def test_frontend_charts():
    """7. test_frontend_charts — рендер графіків."""
    # Verify that the TimelineChart and BottlenecksChart TSX files exist and contain rendering layout
    timeline_path = ROOT / "apps/web/components/analytics/TimelineChart.tsx"
    bottlenecks_path = ROOT / "apps/web/components/analytics/BottlenecksChart.tsx"
    
    assert timeline_path.exists(), f"TimelineChart file missing at: {timeline_path}"
    assert bottlenecks_path.exists(), f"BottlenecksChart file missing at: {bottlenecks_path}"
    
    timeline_text = timeline_path.read_text(encoding="utf-8")
    assert "runs_count" in timeline_text
    assert "success_count" in timeline_text
    assert "error_count" in timeline_text
    assert "<svg" in timeline_text
    
    bottlenecks_text = bottlenecks_path.read_text(encoding="utf-8")
    assert "task_type" in bottlenecks_text
    assert "avg_duration_seconds" in bottlenecks_text
    assert "failure_rate" in bottlenecks_text
    assert "maxDuration" in bottlenecks_text
