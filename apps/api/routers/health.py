# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_health"
# purpose: "FastAPI REST Router for Health Probes, Prometheus Metrics & Alert Management"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-09-05"
# --- END DNK-MRH-HEADER ---

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from apps.api.monitoring.alerts import (
    AlertDispatchResult,
    AlertNotification,
    AlertSeverity,
    alert_manager,
)
from apps.api.monitoring.health_check import (
    ComponentHealth,
    HealthStatus,
    SystemHealthReport,
    health_registry,
)
from apps.api.monitoring.metrics import (
    CONTENT_TYPE_LATEST,
    metrics_registry,
)
from core.orchestrator.swarm_health import SwarmHealthEngine

logger = logging.getLogger("dnk.routers.health")
swarm_health_engine = SwarmHealthEngine()

router = APIRouter(prefix="", tags=["Monitoring & Health"])


class TriggerAlertRequest(BaseModel):
    """Schema for manually triggering or testing an alert."""
    title: str = Field(..., description="Alert headline/summary")
    message: str = Field(..., description="Detailed description of the issue")
    severity: AlertSeverity = Field(default=AlertSeverity.WARNING, description="Alert severity level")
    service: str = Field(default="dnk_os", description="Originating service identifier")
    component: Optional[str] = Field(default="api", description="Subsystem component")
    runbook_url: Optional[str] = Field(default=None, description="Link to remediation runbook")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary diagnostic metadata")
    channels: Optional[List[str]] = Field(default=None, description="Specific channels to notify, e.g. ['slack', 'email']")


# ---------------------------------------------------------------------------
# Health Endpoints (Kubernetes & Load Balancer Probes)
# ---------------------------------------------------------------------------

@router.get(
    "/health/live",
    summary="Liveness Probe",
    description="Rapid probe verifying the web application process is responsive.",
)
@router.get("/api/v1/health/live", include_in_schema=False)
async def liveness_probe() -> Dict[str, Any]:
    return await health_registry.check_liveness()


@router.get(
    "/health/ready",
    summary="Readiness Probe",
    description="Probes readiness to accept user traffic, checking essential infrastructure.",
    response_model=SystemHealthReport,
)
@router.get("/api/v1/health/ready", include_in_schema=False)
async def readiness_probe(response: Response) -> SystemHealthReport:
    report = await health_registry.check_readiness()
    if report.status == HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif report.status == HealthStatus.DEGRADED:
        response.status_code = status.HTTP_200_OK
    return report


@router.get(
    "/health/detailed",
    summary="Detailed Diagnostic Health Report",
    description="Full diagnostic report evaluating all registered subsystem probes.",
    response_model=SystemHealthReport,
)
@router.get("/api/v1/health/detailed", include_in_schema=False)
async def detailed_health(response: Response) -> SystemHealthReport:
    report = await health_registry.check_all()
    if report.status == HealthStatus.UNHEALTHY:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return report


# ---------------------------------------------------------------------------
# Prometheus Metrics Endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/metrics",
    summary="Prometheus Metrics",
    description="Exports system and application metrics in standard Prometheus exposition text format.",
)
@router.get("/api/v1/metrics", include_in_schema=False)
async def prometheus_metrics() -> Response:
    metrics_data = metrics_registry.export_metrics()
    return Response(content=metrics_data, media_type=CONTENT_TYPE_LATEST)


# ---------------------------------------------------------------------------
# Alerting Management & Testing Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/api/v1/alerts/dispatch",
    summary="Dispatch Alert Notification",
    description="Dispatches an alert to Slack, Email, and other configured channels.",
    response_model=List[AlertDispatchResult],
)
async def dispatch_alert_endpoint(payload: TriggerAlertRequest) -> List[AlertDispatchResult]:
    alert = AlertNotification(
        title=payload.title,
        message=payload.message,
        severity=payload.severity,
        service=payload.service,
        component=payload.component,
        runbook_url=payload.runbook_url,
        metadata=payload.metadata,
    )
    results = await alert_manager.dispatch(alert, channels=payload.channels)
    return results


@router.get(
    "/api/v1/alerts/channels",
    summary="Alert Channels Status",
    description="Returns available notification channels and their configuration status.",
)
async def alert_channels_status() -> Dict[str, Any]:
    channels_info = {}
    for name, channel in alert_manager.channels.items():
        configured = True
        if name == "slack":
            configured = bool(getattr(channel, "webhook_url", None))
        elif name == "email":
            configured = bool(getattr(channel, "smtp_host", None) and getattr(channel, "to_email", None))
        channels_info[name] = {
            "type": channel.__class__.__name__,
            "configured": configured,
        }
    return {
        "channels": channels_info,
        "cooldown_seconds": alert_manager.throttle_cooldown,
    }


# ---------------------------------------------------------------------------
# Swarm Health Dashboard (Priority 4)
# ---------------------------------------------------------------------------

@router.get(
    "/health/swarm",
    summary="Swarm Health Dashboard",
    description="Unified diagnostic health status of the 14-agent swarm, sentinel alerts, accounting, and websocket bridge.",
)
@router.get("/api/v1/health/swarm", include_in_schema=False)
async def swarm_health_endpoint(
    workspace_id: str = Query("ws-alpha-001", description="Target Workspace ID"),
    details: bool = Query(True, description="Include detailed 14-agent cards"),
    spend_limit_usd: Optional[float] = Query(None, description="Override spend limit in USD"),
) -> Dict[str, Any]:
    """Unified Swarm Health & Diagnostic Endpoint."""
    return swarm_health_engine.get_health_status(
        workspace_id=workspace_id,
        include_agent_details=details,
        spend_limit_usd=spend_limit_usd,
    )


class SwarmHealRequest(BaseModel):
    alert_id: Optional[str] = None
    action: Optional[str] = "resolve"
    workspace_id: str = "ws-alpha-001"


@router.post(
    "/health/swarm/heal",
    summary="Swarm Auto-Heal & Resolve",
    description="Actively resolves Sentinel anomalies and archives self-healing plans.",
)
@router.post("/api/v1/health/swarm/heal", include_in_schema=False)
async def swarm_heal_endpoint(
    req: Optional[SwarmHealRequest] = None,
) -> Dict[str, Any]:
    """Active auto-healing endpoint."""
    alert_id = req.alert_id if req else None
    action = req.action if req and req.action else "resolve"
    workspace_id = req.workspace_id if req and req.workspace_id else "ws-alpha-001"
    return swarm_health_engine.resolve_or_heal_alert(
        alert_id=alert_id,
        action=action,
        workspace_id=workspace_id,
    )

