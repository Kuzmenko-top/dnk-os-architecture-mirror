# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_workspace_analytics_service"
# purpose: "Unified metrics collection, aggregation, percentiles computation and reporting service"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from apps.api.db.analytics_storage import (
    AnalyticsStorage,
    MetricType,
    analytics_storage,
)


class WorkspaceAnalyticsService:
    """Core analytics engine orchestrating telemetry collection, percentile calculations, and report extraction."""

    def __init__(self, storage: Optional[AnalyticsStorage] = None):
        self.storage = storage or analytics_storage

    async def record_workspace_activity(
        self,
        workspace_id: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record workspace lifecycle activity (prompt, diff, approval, commit, rollback, kill-switch)."""
        return await self.storage.record_metric(
            MetricType.WORKSPACE_ACTIVITY,
            {
                "workspace_id": workspace_id,
                "event_type": event_type,
                "user_id": user_id,
                "details": details or {},
            },
        )

    async def record_user_activity(
        self,
        user_id: str,
        event_type: str,
        workspace_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record user activity (login, workspace switch, presence join/leave)."""
        return await self.storage.record_metric(
            MetricType.USER_ACTIVITY,
            {
                "user_id": user_id,
                "event_type": event_type,
                "workspace_id": workspace_id,
                "details": details or {},
            },
        )

    async def record_performance_metric(
        self,
        endpoint: str,
        latency_ms: float,
        db_latency_ms: float = 0.0,
        redis_latency_ms: float = 0.0,
        workspace_id: Optional[str] = None,
        status_code: int = 200,
    ) -> Dict[str, Any]:
        """Record API, DB, and Redis latency telemetry."""
        return await self.storage.record_metric(
            MetricType.PERFORMANCE,
            {
                "endpoint": endpoint,
                "latency_ms": latency_ms,
                "db_latency_ms": db_latency_ms,
                "redis_latency_ms": redis_latency_ms,
                "workspace_id": workspace_id,
                "status_code": status_code,
            },
        )

    async def record_error_metric(
        self,
        error_type: str,
        status_code: int,
        message: Optional[str] = None,
        workspace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Record system, database, Redis errors or OCC conflicts."""
        # Support positional workspace_id as 3rd argument
        if workspace_id is None and message and (message.startswith("ws_") or message.startswith("ws-")):
            workspace_id = message
            message = ""

        return await self.storage.record_metric(
            MetricType.ERROR,
            {
                "error_type": error_type,
                "status_code": status_code,
                "message": message or "",
                "workspace_id": workspace_id,
                "user_id": user_id,
                "endpoint": endpoint or "",
            },
        )

    async def get_workspace_activity(
        self,
        workspace_id: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve historical workspace activity metrics."""
        return await self.storage.query_metrics(
            MetricType.WORKSPACE_ACTIVITY,
            start=start,
            end=end,
            workspace_id=workspace_id,
        )

    async def get_user_activity(
        self,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve user activity filtered by user and/or workspace."""
        return await self.storage.query_metrics(
            MetricType.USER_ACTIVITY,
            start=start,
            end=end,
            workspace_id=workspace_id,
            user_id=user_id,
        )

    async def get_performance_metrics(
        self,
        workspace_id: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve performance metrics."""
        return await self.storage.query_metrics(
            MetricType.PERFORMANCE,
            start=start,
            end=end,
            workspace_id=workspace_id,
        )

    async def get_error_metrics(
        self,
        workspace_id: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve error metrics."""
        return await self.storage.query_metrics(
            MetricType.ERROR,
            start=start,
            end=end,
            workspace_id=workspace_id,
        )

    async def get_performance_percentiles(
        self,
        endpoint: Optional[str] = None,
        workspace_id: Optional[Union[str, datetime]] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> Dict[str, float]:
        """Calculate p50, p95, p99 latencies, average duration, and throughput."""
        if isinstance(workspace_id, datetime):
            end = start
            start = workspace_id
            workspace_id = None

        metrics = await self.storage.query_metrics(
            MetricType.PERFORMANCE,
            start=start,
            end=end,
            workspace_id=workspace_id,
        )
        latencies = [
            m["data"]["latency_ms"]
            for m in metrics
            if endpoint is None or m["data"].get("endpoint") == endpoint
        ]
        if not latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "avg": 0.0, "count": 0}

        latencies.sort()
        n = len(latencies)
        return {
            "p50": round(float(latencies[int((n - 1) * 0.50)]), 2),
            "p95": round(float(latencies[int((n - 1) * 0.95)]), 2),
            "p99": round(float(latencies[int((n - 1) * 0.99)]), 2),
            "avg": round(sum(latencies) / n, 2),
            "count": n,
        }


workspace_analytics_service = WorkspaceAnalyticsService()
