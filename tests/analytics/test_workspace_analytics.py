# --- DNK-MRH-HEADER ---
# mrh_id: "tests_analytics_test_workspace_analytics"
# purpose: "Unit and integration tests for AnalyticsStorage, WorkspaceAnalyticsService, percentiles and aggregations"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import asyncio
import pytest
from datetime import datetime, timedelta, timezone

from apps.api.db.analytics_storage import (
    AnalyticsStorage,
    MetricType,
    analytics_storage,
)
from apps.api.services.workspace_analytics_service import (
    WorkspaceAnalyticsService,
    workspace_analytics_service,
)


@pytest.fixture(autouse=True)
def clean_storage():
    analytics_storage.clear()
    yield
    analytics_storage.clear()


@pytest.mark.asyncio
async def test_analytics_storage_record_and_query():
    storage = AnalyticsStorage(retention_days=30)
    
    await storage.record_metric(
        MetricType.WORKSPACE_ACTIVITY,
        {"workspace_id": "ws-123", "event_type": "workspace:prompt_submitted", "prompt": "build UI"}
    )
    await storage.record_metric(
        MetricType.WORKSPACE_ACTIVITY,
        {"workspace_id": "ws-456", "event_type": "workspace:commit_executed"}
    )
    
    all_metrics = await storage.query_metrics(MetricType.WORKSPACE_ACTIVITY)
    assert len(all_metrics) == 2
    
    ws123_metrics = await storage.query_metrics(MetricType.WORKSPACE_ACTIVITY, workspace_id="ws-123")
    assert len(ws123_metrics) == 1
    assert ws123_metrics[0]["data"]["event_type"] == "workspace:prompt_submitted"


@pytest.mark.asyncio
async def test_analytics_storage_retention_cleanup():
    storage = AnalyticsStorage(retention_days=1)
    
    old_entry = {
        "timestamp": datetime.now(timezone.utc) - timedelta(days=5),
        "data": {"workspace_id": "ws-old", "event_type": "old_event"}
    }
    storage.metrics_buffer[MetricType.WORKSPACE_ACTIVITY.value].append(old_entry)
    
    # Recording new metric triggers cleanup
    await storage.record_metric(
        MetricType.WORKSPACE_ACTIVITY,
        {"workspace_id": "ws-new", "event_type": "new_event"}
    )
    
    active_metrics = await storage.query_metrics(MetricType.WORKSPACE_ACTIVITY)
    assert len(active_metrics) == 1
    assert active_metrics[0]["data"]["workspace_id"] == "ws-new"


@pytest.mark.asyncio
async def test_analytics_storage_aggregation():
    storage = AnalyticsStorage()
    now = datetime.now(timezone.utc)
    
    for i in range(5):
        await storage.record_metric(
            MetricType.PERFORMANCE,
            {"workspace_id": "ws-1", "endpoint": "/api/v1/test", "latency_ms": 20.0 + i}
        )
    
    agg = await storage.aggregate_metrics(MetricType.PERFORMANCE, aggregation="1h", workspace_id="ws-1")
    assert len(agg) == 1
    assert agg[0]["count"] == 5


@pytest.mark.asyncio
async def test_workspace_analytics_service_percentiles():
    service = WorkspaceAnalyticsService()
    
    # Add 100 sample latency entries
    for i in range(1, 101):
        await service.record_performance_metric(
            endpoint="/api/v1/workspaces",
            latency_ms=float(i),
            workspace_id="ws-1"
        )
        
    stats = await service.get_performance_percentiles(
        endpoint="/api/v1/workspaces",
        workspace_id="ws-1"
    )
    assert stats["count"] == 100
    assert stats["p50"] == 50.0
    assert stats["p95"] == 95.0
    assert stats["p99"] == 99.0


@pytest.mark.asyncio
async def test_workspace_analytics_service_all_event_types():
    service = WorkspaceAnalyticsService()
    
    # 1. Workspace activity
    await service.record_workspace_activity("ws-1", "workspace:diff_staged", {"diff_size": 42})
    # 2. User activity
    await service.record_user_activity("user-1", "user:login", workspace_id="ws-1")
    # 3. Performance metric
    await service.record_performance_metric("/api/v1/query", latency_ms=12.5, db_latency_ms=3.1, workspace_id="ws-1")
    # 4. Error metric
    await service.record_error_metric("OCC_CONFLICT", 409, message="Conflict detected", workspace_id="ws-1")
    
    ws_act = await service.get_workspace_activity("ws-1")
    user_act = await service.get_user_activity(workspace_id="ws-1")
    perf = await service.get_performance_metrics("ws-1")
    errs = await service.get_error_metrics("ws-1")
    
    assert len(ws_act) == 1
    assert ws_act[0]["data"]["details"]["diff_size"] == 42
    assert len(user_act) == 1
    assert user_act[0]["data"]["user_id"] == "user-1"
    assert len(perf) == 1
    assert perf[0]["data"]["db_latency_ms"] == 3.1
    assert len(errs) == 1
    assert errs[0]["data"]["status_code"] == 409
