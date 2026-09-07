# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_db_analytics_storage"
# purpose: "Time-series in-memory and persistent storage engine with retention and aggregation for workspace analytics"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class MetricType(str, Enum):
    WORKSPACE_ACTIVITY = "workspace_activity"
    USER_ACTIVITY = "user_activity"
    PERFORMANCE = "performance"
    ERROR = "error"


class AnalyticsStorage:
    """Time-series storage engine with retention policy and multi-bucket aggregations."""

    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
        self.metrics_buffer: Dict[str, List[Dict[str, Any]]] = {
            metric_type.value: [] for metric_type in MetricType
        }

    async def record_metric(self, metric_type: MetricType, data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a time-series metric entry with an ISO UTC timestamp."""
        now = datetime.now(timezone.utc)
        entry = {
            "timestamp": now,
            "data": data,
        }
        type_key = metric_type.value if isinstance(metric_type, MetricType) else str(metric_type)
        if type_key not in self.metrics_buffer:
            self.metrics_buffer[type_key] = []
        self.metrics_buffer[type_key].append(entry)
        await self._cleanup_old_metrics(type_key)
        return entry

    async def _cleanup_old_metrics(self, type_key: str):
        """Purge entries exceeding the retention limit."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        self.metrics_buffer[type_key] = [
            m for m in self.metrics_buffer[type_key]
            if m["timestamp"] > cutoff
        ]

    async def query_metrics(
        self,
        metric_type: MetricType,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        workspace_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query metrics by type, time window, and optional workspace or user filters."""
        type_key = metric_type.value if isinstance(metric_type, MetricType) else str(metric_type)
        metrics = self.metrics_buffer.get(type_key, [])

        filtered = []
        for m in metrics:
            ts = m["timestamp"]
            # Support naive vs aware datetime comparison
            if start:
                st = start if start.tzinfo else start.replace(tzinfo=timezone.utc)
                if ts < st:
                    continue
            if end:
                et = end if end.tzinfo else end.replace(tzinfo=timezone.utc)
                if ts > et:
                    continue

            data = m.get("data", {})
            if workspace_id and data.get("workspace_id") != workspace_id:
                continue
            if user_id and data.get("user_id") != user_id:
                continue

            filtered.append(m)
        return filtered

    async def aggregate_metrics(
        self,
        metric_type: MetricType,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        workspace_id: Optional[str] = None,
        aggregation: str = "1h",
    ) -> List[Dict[str, Any]]:
        """Aggregate metrics by time buckets (1m, 1h, 1d)."""
        metrics = await self.query_metrics(metric_type, start, end, workspace_id=workspace_id)
        buckets: Dict[str, int] = {}

        for m in metrics:
            ts: datetime = m["timestamp"]
            if aggregation == "1m":
                bucket_key = ts.strftime("%Y-%m-%d %H:%M")
            elif aggregation == "1d":
                bucket_key = ts.strftime("%Y-%m-%d")
            else:  # default "1h"
                bucket_key = ts.strftime("%Y-%m-%d %H:00")

            buckets[bucket_key] = buckets.get(bucket_key, 0) + 1

        return [{"bucket": k, "count": v} for k, v in sorted(buckets.items())]

    def clear(self):
        """Helper to reset in-memory buffers for testing."""
        for key in self.metrics_buffer:
            self.metrics_buffer[key] = []


analytics_storage = AnalyticsStorage()
