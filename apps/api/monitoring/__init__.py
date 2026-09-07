# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_monitoring_init"
# purpose: "Monitoring, Health Check, Metrics & Alerting Subsystem for DNK OS"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

"""
Monitoring Subsystem for DNK OS.
Provides health diagnostics, Prometheus metrics, and multi-channel alerting.
"""

from apps.api.monitoring.health_check import (
    HealthCheckRegistry,
    HealthStatus,
    ComponentHealth,
    SystemHealthReport,
    health_registry,
)
from apps.api.monitoring.metrics import (
    MetricsRegistry,
    metrics_registry,
    CONTENT_TYPE_LATEST,
)
from apps.api.monitoring.alerts import (
    AlertManager,
    AlertNotification,
    AlertSeverity,
    alert_manager,
)

__all__ = [
    "HealthCheckRegistry",
    "HealthStatus",
    "ComponentHealth",
    "SystemHealthReport",
    "health_registry",
    "MetricsRegistry",
    "metrics_registry",
    "AlertManager",
    "AlertNotification",
    "AlertSeverity",
    "alert_manager",
]
