# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_monitoring_metrics"
# purpose: "Prometheus Metrics Engine and Collector for DNK OS"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional

try:
    import psutil
except ImportError:
    psutil = None

CONTENT_TYPE_LATEST: str = "text/plain; version=0.0.4; charset=utf-8"

# We attempt to import prometheus_client, providing a robust fallback if absent
try:
    from prometheus_client import (
        CollectorRegistry,
        Counter,
        Gauge,
        Histogram,
        generate_latest,
    )
    PROMETHEUS_CLIENT_AVAILABLE = True
except ImportError:
    PROMETHEUS_CLIENT_AVAILABLE = False
    CollectorRegistry = None  # type: ignore
    Counter = None  # type: ignore
    Gauge = None  # type: ignore
    Histogram = None  # type: ignore
    generate_latest = None  # type: ignore

logger = logging.getLogger("dnk.monitoring.metrics")


class MetricsRegistry:
    """
    Centralized Prometheus Metrics Registry for DNK OS API, Swarm & Infrastructure.
    Wraps standard Prometheus metrics with graceful fallback and helper methods.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._drift_exporters: List[Any] = []
        self.use_prom = PROMETHEUS_CLIENT_AVAILABLE
        
        if self.use_prom:
            self.registry = CollectorRegistry(auto_describe=True)
            self._init_prometheus_metrics()
        else:
            self._fallback_counters: Dict[str, float] = {}
            self._fallback_gauges: Dict[str, float] = {}

    def _init_prometheus_metrics(self) -> None:
        """Initializes core system and business metrics using prometheus_client."""
        if not self.use_prom or CollectorRegistry is None or Counter is None or Histogram is None or Gauge is None:
            return

        self.http_requests_total = Counter(
            "dnk_http_requests_total",
            "Total count of HTTP requests processed by DNK OS API",
            ["method", "endpoint", "status_code"],
            registry=self.registry,
        )

        self.http_request_duration_seconds = Histogram(
            "dnk_http_request_duration_seconds",
            "HTTP request latency in seconds",
            ["method", "endpoint"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
            registry=self.registry,
        )

        self.system_cpu_usage_ratio = Gauge(
            "dnk_system_cpu_usage_ratio",
            "Host CPU utilization ratio (0.0 to 1.0)",
            registry=self.registry,
        )

        self.system_memory_usage_bytes = Gauge(
            "dnk_system_memory_usage_bytes",
            "Host memory used in bytes",
            registry=self.registry,
        )

        self.swarm_active_tasks_total = Gauge(
            "dnk_swarm_active_tasks_total",
            "Current active tasks executing in Swarm workers",
            ["agent"],
            registry=self.registry,
        )

        self.swarm_completed_tasks_total = Counter(
            "dnk_swarm_completed_tasks_total",
            "Total tasks completed across Swarm workers",
            ["agent", "status"],
            registry=self.registry,
        )

        self.active_websocket_connections = Gauge(
            "dnk_active_websocket_connections",
            "Active real-time WebSocket client connections",
            ["workspace_id"],
            registry=self.registry,
        )

        self.alerts_dispatched_total = Counter(
            "dnk_alerts_dispatched_total",
            "Count of alerts dispatched to external channels",
            ["severity", "channel", "status"],
            registry=self.registry,
        )

    def record_request(self, method: str, endpoint: str, status_code: int, duration_seconds: float) -> None:
        """Records HTTP request telemetry: increment counter and record latency."""
        code_str = str(status_code)
        if self.use_prom:
            try:
                self.http_requests_total.labels(method=method, endpoint=endpoint, status_code=code_str).inc()
                self.http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration_seconds)
            except Exception as e:
                logger.debug("Failed recording prometheus request metric: %s", e)
        else:
            with self._lock:
                key = f"dnk_http_requests_total{{method=\"{method}\",endpoint=\"{endpoint}\",status_code=\"{code_str}\"}}"
                self._fallback_counters[key] = self._fallback_counters.get(key, 0.0) + 1.0

    def record_swarm_task(self, agent: str, status: str, duration_seconds: Optional[float] = None) -> None:
        """Records swarm task completion and status."""
        if self.use_prom:
            try:
                self.swarm_completed_tasks_total.labels(agent=agent, status=status).inc()
            except Exception as e:
                logger.debug("Failed recording prometheus swarm metric: %s", e)
        else:
            with self._lock:
                key = f"dnk_swarm_completed_tasks_total{{agent=\"{agent}\",status=\"{status}\"}}"
                self._fallback_counters[key] = self._fallback_counters.get(key, 0.0) + 1.0

    def set_swarm_active_tasks(self, agent: str, count: int) -> None:
        """Updates count of active swarm tasks for an agent."""
        if self.use_prom:
            try:
                self.swarm_active_tasks_total.labels(agent=agent).set(count)
            except Exception as e:
                logger.debug("Failed updating swarm active tasks: %s", e)
        else:
            with self._lock:
                key = f"dnk_swarm_active_tasks_total{{agent=\"{agent}\"}}"
                self._fallback_gauges[key] = float(count)

    def set_websocket_connections(self, workspace_id: str, count: int) -> None:
        """Updates active WebSocket connection count for a workspace."""
        if self.use_prom:
            try:
                self.active_websocket_connections.labels(workspace_id=workspace_id).set(count)
            except Exception as e:
                logger.debug("Failed updating websocket connections: %s", e)
        else:
            with self._lock:
                key = f"dnk_active_websocket_connections{{workspace_id=\"{workspace_id}\"}}"
                self._fallback_gauges[key] = float(count)

    def record_alert_dispatched(self, severity: str, channel: str, success: bool = True) -> None:
        """Records an alert notification dispatch attempt."""
        status = "success" if success else "failed"
        if self.use_prom:
            try:
                self.alerts_dispatched_total.labels(severity=severity, channel=channel, status=status).inc()
            except Exception as e:
                logger.debug("Failed recording alert metric: %s", e)
        else:
            with self._lock:
                key = f"dnk_alerts_dispatched_total{{severity=\"{severity}\",channel=\"{channel}\",status=\"{status}\"}}"
                self._fallback_counters[key] = self._fallback_counters.get(key, 0.0) + 1.0

    def update_system_gauges(self) -> None:
        """Collects latest host OS memory and CPU stats."""
        if psutil:
            try:
                cpu_ratio = psutil.cpu_percent(interval=None) / 100.0
                mem = psutil.virtual_memory()
                used_bytes = mem.used

                if self.use_prom:
                    self.system_cpu_usage_ratio.set(cpu_ratio)
                    self.system_memory_usage_bytes.set(used_bytes)
                else:
                    with self._lock:
                        self._fallback_gauges["dnk_system_cpu_usage_ratio"] = cpu_ratio
                        self._fallback_gauges["dnk_system_memory_usage_bytes"] = float(used_bytes)
            except Exception as exc:
                logger.debug("Unable to read psutil system gauges: %s", exc)

    def register_drift_exporter(self, exporter: Any) -> None:
        """Registers a GeminiTelemetryExporter to include its Prometheus metrics in exports."""
        with self._lock:
            if exporter not in self._drift_exporters:
                self._drift_exporters.append(exporter)

    def export_metrics(self) -> bytes:
        """
        Exports collected metrics in standard Prometheus exposition format.
        """
        self.update_system_gauges()

        base_bytes: bytes
        if self.use_prom and generate_latest is not None:
            base_bytes = generate_latest(self.registry)
        else:
            # Fallback text format generation
            lines = [
                "# HELP dnk_system_cpu_usage_ratio Host CPU utilization ratio (0.0 to 1.0)",
                "# TYPE dnk_system_cpu_usage_ratio gauge",
            ]
            with self._lock:
                for k, v in self._fallback_gauges.items():
                    lines.append(f"{k} {v}")
                for k, v in self._fallback_counters.items():
                    lines.append(f"{k} {v}")
            lines.append("")
            base_bytes = "\n".join(lines).encode("utf-8")

        drift_parts: List[bytes] = []
        with self._lock:
            exporters = list(self._drift_exporters)
        for exp in exporters:
            try:
                txt = exp.export_prometheus_text()
                if txt and txt.strip():
                    drift_parts.append(txt.encode("utf-8"))
            except Exception as exc:
                logger.debug("Failed exporting drift telemetry: %s", exc)

        if drift_parts:
            return base_bytes + b"\n" + b"\n".join(drift_parts)
        return base_bytes


# Global singleton metrics registry
metrics_registry = MetricsRegistry()

# Automatically wire default_telemetry_exporter for drift & self-healing metrics
try:
    from services.dnk_analytics.telemetry_exporter import default_telemetry_exporter
    metrics_registry.register_drift_exporter(default_telemetry_exporter)
except Exception:
    pass

__all__ = [
    "MetricsRegistry",
    "metrics_registry",
    "CONTENT_TYPE_LATEST",
]
