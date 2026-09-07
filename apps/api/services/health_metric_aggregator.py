# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_services_health_metric_aggregator"
# purpose: "Metric Aggregation & Statistical Analysis for Health Monitoring (DNK-HEALTH-001 Phase 2)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import math
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from apps.api.db.models.service_health_snapshot import ServiceHealthSnapshot


class HealthMetricAggregator:
    """Aggregates time-series metrics per service and computes rolling statistical aggregates."""

    def __init__(self, max_samples_per_series: int = 100):
        self.max_samples = max_samples_per_series
        # (workspace_id, service_name, metric_name) -> deque of (timestamp, float_value)
        self._series: Dict[tuple, deque] = defaultdict(lambda: deque(maxlen=self.max_samples))

    def record_metric(
        self,
        workspace_id: str,
        service_name: str,
        metric_name: str,
        value: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Records a single scalar metric observation."""
        ts = timestamp or datetime.now(timezone.utc)
        key = (workspace_id, service_name, metric_name)
        self._series[key].append((ts, float(value)))

    def get_raw_series(
        self,
        workspace_id: str,
        service_name: str,
        metric_name: str,
    ) -> List[tuple]:
        """Returns recorded time-series tuples (timestamp, value)."""
        key = (workspace_id, service_name, metric_name)
        return list(self._series.get(key, []))

    def compute_statistics(
        self,
        workspace_id: str,
        service_name: str,
        metric_name: str,
        window_seconds: Optional[int] = None,
    ) -> Dict[str, float]:
        """Computes statistical summary: count, mean, min, max, stddev, p95, p99."""
        key = (workspace_id, service_name, metric_name)
        samples = self._series.get(key, [])
        if not samples:
            return {
                "count": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "stddev": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "latest": 0.0,
            }

        now = datetime.now(timezone.utc)
        if window_seconds is not None and window_seconds > 0:
            filtered_values = [
                v for ts, v in samples
                if (now - ts).total_seconds() <= window_seconds
            ]
        else:
            filtered_values = [v for _, v in samples]

        if not filtered_values:
            filtered_values = [samples[-1][1]]

        n = len(filtered_values)
        sorted_vals = sorted(filtered_values)
        mean_val = sum(sorted_vals) / n
        min_val = sorted_vals[0]
        max_val = sorted_vals[-1]
        latest_val = samples[-1][1]

        # Standard deviation
        variance = sum((x - mean_val) ** 2 for x in sorted_vals) / n if n > 0 else 0.0
        stddev_val = math.sqrt(variance)

        # Percentiles
        p95_idx = int(math.ceil(0.95 * n)) - 1
        p99_idx = int(math.ceil(0.99 * n)) - 1
        p95_val = sorted_vals[max(0, min(n - 1, p95_idx))]
        p99_val = sorted_vals[max(0, min(n - 1, p99_idx))]

        return {
            "count": float(n),
            "mean": round(mean_val, 4),
            "min": round(min_val, 4),
            "max": round(max_val, 4),
            "stddev": round(stddev_val, 4),
            "p95": round(p95_val, 4),
            "p99": round(p99_val, 4),
            "latest": round(latest_val, 4),
        }

    def generate_service_snapshot(
        self,
        workspace_id: str,
        service_name: str,
        active_incidents_count: float = 0.0,
    ) -> ServiceHealthSnapshot:
        """Constructs a consolidated ServiceHealthSnapshot ORM object."""
        cpu_stats = self.compute_statistics(workspace_id, service_name, "cpu_usage_pct")
        mem_stats = self.compute_statistics(workspace_id, service_name, "memory_usage_pct")
        err_stats = self.compute_statistics(workspace_id, service_name, "error_rate_pct")
        lat_stats = self.compute_statistics(workspace_id, service_name, "latency_ms")

        # Determine overall status
        status = "HEALTHY"
        if active_incidents_count > 0:
            status = "UNHEALTHY"
        elif cpu_stats["mean"] > 85.0 or mem_stats["mean"] > 90.0 or err_stats["mean"] > 5.0:
            status = "DEGRADED"

        metrics_payload = {
            "cpu": cpu_stats,
            "memory": mem_stats,
            "error_rate": err_stats,
            "latency": lat_stats,
        }

        return ServiceHealthSnapshot(
            workspace_id=workspace_id,
            service_name=service_name,
            status=status,
            cpu_usage_pct=cpu_stats["latest"],
            memory_usage_pct=mem_stats["latest"],
            error_rate_pct=err_stats["latest"],
            p95_latency_ms=lat_stats["p95"],
            active_incidents_count=active_incidents_count,
            metrics_payload=metrics_payload,
        )

    def clear_history(self, workspace_id: Optional[str] = None) -> None:
        """Clears memory buffers."""
        if workspace_id is None:
            self._series.clear()
        else:
            keys_to_del = [k for k in self._series if k[0] == workspace_id]
            for k in keys_to_del:
                del self._series[k]
