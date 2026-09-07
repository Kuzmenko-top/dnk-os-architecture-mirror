# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_analytics_alerting"
# purpose: "FastAPI router and WebSocket stream for Alerting Rules, SLO/SLA Monitoring, and Anomaly Detection"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from apps.api.middleware.tenant_authorization import require_tenant_and_workspace
from apps.api.services.analytics_alerting_service import analytics_alerting_service
from apps.api.services.anomaly_detection_service import anomaly_detection_service
from apps.api.services.slo_calculator import slo_calculator

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics Alerting & SLO"])


# ==========================
# Pydantic Schemas
# ==========================

class AlertRuleCreateRequest(BaseModel):
    workspace_id: str
    name: str
    metric_type: str = Field(description="e.g. error_rate, latency_p95, inactivity, resource")
    operator: str = Field(description="gt, lt, gte, lte, eq, neq")
    threshold_value: float
    window_seconds: int = 300
    composite_logic: Optional[Dict[str, Any]] = None
    severity: str = "warning"
    enabled: bool = True
    cooldown_seconds: int = 300
    webhook_url: Optional[str] = None


class AlertRuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    metric_type: Optional[str] = None
    operator: Optional[str] = None
    threshold_value: Optional[float] = None
    window_seconds: Optional[int] = None
    composite_logic: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    enabled: Optional[bool] = None
    cooldown_seconds: Optional[int] = None
    webhook_url: Optional[str] = None


class AlertResolveRequest(BaseModel):
    resolution_note: Optional[str] = "Resolved manually by operator"


# ==========================
# 1. Alerting Rules Endpoints
# ==========================

@router.post("/alerts/rules", status_code=status.HTTP_201_CREATED)
async def create_alert_rule(
    payload: AlertRuleCreateRequest,
):
    """Create a new threshold-based or composite alert rule."""
    rule = await analytics_alerting_service.create_rule(
        workspace_id=payload.workspace_id,
        name=payload.name,
        metric_type=payload.metric_type,
        operator=payload.operator,
        threshold_value=payload.threshold_value,
        window_seconds=payload.window_seconds,
        composite_logic=payload.composite_logic,
        severity=payload.severity,
        enabled=payload.enabled,
        cooldown_seconds=payload.cooldown_seconds,
        webhook_url=payload.webhook_url,
    )
    return rule


@router.get("/alerts/rules")
async def list_alert_rules(
    workspace_id: Optional[str] = Query(default=None),
    enabled_only: bool = Query(default=False),
):
    """List alert rules scoped by workspace."""
    rules = await analytics_alerting_service.list_rules(
        workspace_id=workspace_id,
        enabled_only=enabled_only,
    )
    return {"rules": rules, "total": len(rules)}


@router.get("/alerts/rules/{rule_id}")
async def get_alert_rule(rule_id: str):
    """Get single alert rule by ID."""
    rule = await analytics_alerting_service.get_rule(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Alert rule {rule_id} not found")
    return rule


@router.put("/alerts/rules/{rule_id}")
async def update_alert_rule(
    rule_id: str,
    payload: AlertRuleUpdateRequest,
):
    """Update an existing alert rule."""
    updates = payload.model_dump(exclude_unset=True)
    rule = await analytics_alerting_service.update_rule(rule_id, updates)
    if not rule:
        raise HTTPException(status_code=404, detail=f"Alert rule {rule_id} not found")
    return rule


@router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """Delete an alert rule."""
    deleted = await analytics_alerting_service.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Alert rule {rule_id} not found")
    return {"status": "deleted", "rule_id": rule_id}


# ==========================
# 2. Alert Events Endpoints
# ==========================

@router.get("/alerts/events")
async def list_alert_events(
    workspace_id: Optional[str] = Query(default=None),
    unresolved_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
):
    """List immutable audit log of triggered alert events."""
    events = await analytics_alerting_service.list_events(
        workspace_id=workspace_id,
        unresolved_only=unresolved_only,
        limit=limit,
    )
    return {"events": events, "total": len(events)}


@router.post("/alerts/events/{event_id}/resolve")
async def resolve_alert_event(
    event_id: str,
    payload: Optional[AlertResolveRequest] = None,
):
    """Resolve a triggered alert event."""
    note = payload.resolution_note if payload else "Resolved manually"
    event = await analytics_alerting_service.resolve_event(event_id, resolution_note=note)
    if not event:
        raise HTTPException(status_code=404, detail=f"Alert event {event_id} not found")
    return event


# ==========================
# 3. SLA / SLO Monitoring Endpoints
# ==========================

@router.get("/slo/status")
async def get_slo_status(
    workspace_id: str = Query(default="ws-alpha-001"),
):
    """Get current SLA/SLO status (Uptime %, Error Budget Remaining, Burn Rate, Latency p95)."""
    status_data = await slo_calculator.get_current_status(workspace_id)
    return status_data


@router.get("/slo/history")
async def get_slo_history(
    workspace_id: str = Query(default="ws-alpha-001"),
    limit: int = Query(default=24, ge=1, le=168),
):
    """Get rolling historical SLO snapshots."""
    history = await slo_calculator.get_history(workspace_id=workspace_id, limit=limit)
    return {"workspace_id": workspace_id, "snapshots": history, "total": len(history)}


@router.get("/slo/burn-rate")
async def get_slo_burn_rate_chart(
    workspace_id: str = Query(default="ws-alpha-001"),
    hours: int = Query(default=24, ge=1, le=72),
):
    """Get time-series error budget burn rate series for charts."""
    burn_series = await slo_calculator.get_burn_rate_series(workspace_id=workspace_id, hours=hours)
    return {"workspace_id": workspace_id, "burn_rate_chart": burn_series}


# ==========================
# 4. Anomaly Detection Endpoints
# ==========================

@router.get("/anomalies/scores")
async def get_anomaly_scores(
    workspace_id: str = Query(default="ws-alpha-001"),
    metric_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get time-series anomaly scores for heatmap rendering."""
    scores = await anomaly_detection_service.get_anomaly_scores(
        workspace_id=workspace_id,
        metric_type=metric_type,
        limit=limit,
    )
    return {"workspace_id": workspace_id, "scores": scores, "total": len(scores)}


@router.get("/anomalies/events")
async def get_anomaly_events(
    workspace_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Get detected anomaly events."""
    events = await anomaly_detection_service.get_anomaly_events(
        workspace_id=workspace_id,
        limit=limit,
    )
    return {"events": events, "total": len(events)}


# ==========================
# 5. Live WebSocket Streaming
# ==========================

@router.websocket("/alerts/stream/{workspace_id}")
async def websocket_alerts_stream(websocket: WebSocket, workspace_id: str):
    """WebSocket stream for real-time alert events and anomalies."""
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()

    def event_listener(event: Dict[str, Any]):
        if event.get("workspace_id") == workspace_id or not event.get("workspace_id"):
            queue.put_nowait(event)

    analytics_alerting_service.add_listener(event_listener)

    try:
        # Initial handshake message
        await websocket.send_json({
            "type": "connection_ack",
            "workspace_id": workspace_id,
            "status": "connected",
        })

        while True:
            # Wait for event from queue or receive ping from client
            event = await queue.get()
            await websocket.send_json(event)
    except (WebSocketDisconnect, Exception):
        pass
    finally:
        analytics_alerting_service.remove_listener(event_listener)
