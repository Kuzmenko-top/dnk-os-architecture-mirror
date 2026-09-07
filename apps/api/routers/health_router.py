# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_health_router"
# purpose: "FastAPI REST Router for System Health Monitoring & Auto-Healing Engine (DNK-HEALTH-001 Phase 4)"
# author: "DNK-e.com Maksym & Gerych Prime"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-29"
# --- END DNK-MRH-HEADER ---

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field

from core.orchestrator.swarm_health import SwarmHealthEngine
from apps.api.db.models.auto_healing_policy import AutoHealingPolicy
from apps.api.db.models.health_metric_rule import HealthMetricRule
from apps.api.services.alert_dispatcher_service import AlertDispatcherService
from apps.api.services.auto_healing_executor import AutoHealingExecutor
from apps.api.services.health_metric_aggregator import HealthMetricAggregator
from apps.api.services.incident_detection_engine import IncidentDetectionEngine

logger = logging.getLogger("dnk.health.router")

router = APIRouter(prefix="/api/v1/health", tags=["System Health & Auto-Healing"])

# Service singletons
metric_aggregator = HealthMetricAggregator()
incident_engine = IncidentDetectionEngine(aggregator=metric_aggregator)
auto_healing_executor = AutoHealingExecutor()
alert_dispatcher = AlertDispatcherService()
swarm_health_engine = SwarmHealthEngine()


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------

class IngestMetricRequest(BaseModel):
    workspace_id: str = "ws-default"
    service_name: str
    metric_name: str
    value: float
    timestamp: Optional[float] = None


class CreateHealthRuleRequest(BaseModel):
    workspace_id: str = "ws-default"
    service_name: str
    metric_name: str
    comparator: str = ">"  # >, >=, <, <=, ==, !=
    threshold: Optional[float] = None
    warning_threshold: Optional[float] = None
    critical_threshold: Optional[float] = None
    severity: str = "HIGH"  # INFO, LOW, MEDIUM, HIGH, CRITICAL
    duration_seconds: int = 60
    description: Optional[str] = None


class CreateAutoHealingPolicyRequest(BaseModel):
    workspace_id: str = "ws-default"
    service_name: str
    incident_type: str = "ANY"
    remediation_playbook: str
    max_retries: int = 3
    cooldown_seconds: int = 300
    flap_detection_window_s: int = 600
    playbook_config: Optional[Dict[str, Any]] = None


class DispatchAlertRequest(BaseModel):
    incident_id: str
    channel: str = "WEBHOOK"  # TELEGRAM, SLACK, WEBHOOK, PAGERDUTY, EMAIL
    target: Optional[str] = None
    force: bool = False
    custom_payload: Optional[Dict[str, Any]] = None


class ResolveIncidentRequest(BaseModel):
    resolution_note: Optional[str] = "Manually resolved via API"


class SwarmHealRequest(BaseModel):
    alert_id: Optional[str] = None
    action: Optional[str] = "resolve"
    workspace_id: str = "ws-alpha-001"


# ---------------------------------------------------------------------------
# Metric Ingestion & Summaries
# ---------------------------------------------------------------------------

@router.post("/metrics/ingest", status_code=status.HTTP_201_CREATED)
def ingest_health_metric(req: IngestMetricRequest) -> Dict[str, Any]:
    """Ingests a service health metric and evaluates active threshold rules."""
    ts = datetime.fromtimestamp(req.timestamp, tz=timezone.utc) if req.timestamp else datetime.now(timezone.utc)
    metric_aggregator.record_metric(
        workspace_id=req.workspace_id,
        service_name=req.service_name,
        metric_name=req.metric_name,
        value=req.value,
        timestamp=ts,
    )
    incidents = incident_engine.evaluate_metric(
        workspace_id=req.workspace_id,
        service_name=req.service_name,
        metric_name=req.metric_name,
        observed_value=req.value,
        timestamp=ts,
    )
    return {
        "status": "ingested",
        "service_name": req.service_name,
        "metric_name": req.metric_name,
        "value": req.value,
        "triggered_incidents_count": len(incidents),
        "incidents": [inc.to_dict() for inc in incidents],
    }


@router.get("/metrics/summary")
def get_metrics_summary(
    workspace_id: str = Query(..., description="Workspace ID"),
    service_name: str = Query(..., description="Service Name"),
    metric_name: str = Query(..., description="Metric Name"),
    window_s: int = Query(300, description="Window size in seconds"),
) -> Dict[str, Any]:
    """Returns statistical aggregate summary for a service metric."""
    summary = metric_aggregator.compute_statistics(
        workspace_id=workspace_id,
        service_name=service_name,
        metric_name=metric_name,
        window_seconds=window_s,
    )
    return {
        "workspace_id": workspace_id,
        "service_name": service_name,
        "metric_name": metric_name,
        "summary": summary,
    }


@router.get("/metrics/snapshot")
def get_service_snapshot(
    workspace_id: str = Query(..., description="Workspace ID"),
    service_name: str = Query(..., description="Service Name"),
) -> Dict[str, Any]:
    """Returns composite health snapshot for a service."""
    active_incidents = [
        inc for inc in incident_engine.get_active_incidents(workspace_id)
        if inc.service_name == service_name
    ]
    snapshot = metric_aggregator.generate_service_snapshot(
        workspace_id=workspace_id,
        service_name=service_name,
        active_incidents_count=float(len(active_incidents)),
    )
    return {
        "workspace_id": workspace_id,
        "service_name": service_name,
        "snapshot": snapshot.to_dict(),
    }


# ---------------------------------------------------------------------------
# Health Metric Rules
# ---------------------------------------------------------------------------

@router.post("/rules", status_code=status.HTTP_201_CREATED)
def create_health_rule(req: CreateHealthRuleRequest) -> Dict[str, Any]:
    """Registers a new health metric threshold rule."""
    crit_val = req.critical_threshold if req.critical_threshold is not None else (req.threshold if req.threshold is not None else 80.0)
    warn_val = req.warning_threshold if req.warning_threshold is not None else (crit_val * 0.8)

    rule = HealthMetricRule(
        workspace_id=req.workspace_id,
        service_name=req.service_name,
        metric_name=req.metric_name,
        comparator=req.comparator,
        warning_threshold=warn_val,
        critical_threshold=crit_val,
        evaluation_window_seconds=req.duration_seconds,
        labels={"severity": req.severity, "description": req.description or ""},
    )
    rule_id = incident_engine.register_rule(rule)
    return {
        "status": "registered",
        "rule_id": rule_id,
        "rule": rule.to_dict(),
    }


@router.get("/rules")
def list_health_rules(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
) -> Dict[str, Any]:
    """Lists registered health metric threshold rules."""
    rules = incident_engine.list_rules(workspace_id)
    return {
        "total": len(rules),
        "rules": [r.to_dict() for r in rules],
    }


# ---------------------------------------------------------------------------
# System Incidents
# ---------------------------------------------------------------------------

@router.get("/incidents")
def list_incidents(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    service_name: Optional[str] = Query(None, description="Filter by service name"),
) -> Dict[str, Any]:
    """Lists active system incidents."""
    incidents = incident_engine.get_active_incidents(workspace_id=workspace_id)
    if service_name:
        incidents = [inc for inc in incidents if inc.service_name == service_name]
    return {
        "total": len(incidents),
        "incidents": [inc.to_dict() for inc in incidents],
    }


@router.post("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: str, req: ResolveIncidentRequest) -> Dict[str, Any]:
    """Manually resolves an active system incident."""
    inc = incident_engine.resolve_incident(incident_id)
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found or already resolved",
        )
    return {
        "status": "resolved",
        "incident": inc.to_dict(),
        "note": req.resolution_note,
    }


# ---------------------------------------------------------------------------
# Auto-Healing Policies & Execution
# ---------------------------------------------------------------------------

@router.post("/policies", status_code=status.HTTP_201_CREATED)
def create_auto_healing_policy(req: CreateAutoHealingPolicyRequest) -> Dict[str, Any]:
    """Creates an auto-healing policy."""
    policy = AutoHealingPolicy(
        workspace_id=req.workspace_id,
        service_name=req.service_name,
        incident_type=req.incident_type,
        remediation_playbook=req.remediation_playbook,
        max_retries=req.max_retries,
        cooldown_seconds=req.cooldown_seconds,
        flap_detection_window_s=req.flap_detection_window_s,
        playbook_config=req.playbook_config or {},
    )
    pol_id = auto_healing_executor.register_policy(policy)
    return {
        "status": "created",
        "policy_id": pol_id,
        "policy": policy.to_dict(),
    }


@router.get("/policies")
def list_auto_healing_policies(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
) -> Dict[str, Any]:
    """Lists auto-healing policies."""
    policies = auto_healing_executor.list_policies(workspace_id)
    return {
        "total": len(policies),
        "policies": [p.to_dict() for p in policies],
    }


@router.post("/remediate/{incident_id}")
def execute_remediation(incident_id: str) -> Dict[str, Any]:
    """Executes auto-healing remediation for an incident."""
    matching = [inc for inc in incident_engine.get_active_incidents() if inc.id == incident_id]
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{incident_id}' not found",
        )
    incident = matching[0]
    action = auto_healing_executor.evaluate_and_execute(incident)
    return {
        "status": action.status,
        "action": action.to_dict(),
    }


@router.get("/remediations")
def list_remediation_actions(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    incident_id: Optional[str] = Query(None, description="Filter by incident ID"),
) -> Dict[str, Any]:
    """Lists remediation action execution history."""
    actions = auto_healing_executor.get_action_history(
        workspace_id=workspace_id,
        incident_id=incident_id,
    )
    return {
        "total": len(actions),
        "actions": [a.to_dict() for a in actions],
    }


# ---------------------------------------------------------------------------
# Alert Notifications
# ---------------------------------------------------------------------------

@router.post("/alerts/dispatch", status_code=status.HTTP_201_CREATED)
def dispatch_alert_notification(req: DispatchAlertRequest) -> Dict[str, Any]:
    """Dispatches an alert notification to a specified channel."""
    matching = [inc for inc in incident_engine.get_active_incidents() if inc.id == req.incident_id]
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{req.incident_id}' not found",
        )
    incident = matching[0]
    log = alert_dispatcher.dispatch_alert(
        incident=incident,
        channel=req.channel,
        target=req.target,
        custom_payload=req.custom_payload,
        force=req.force,
    )
    return {
        "status": log.status,
        "log": log.to_dict(),
    }


@router.get("/alerts/logs")
def list_alert_logs(
    workspace_id: Optional[str] = Query(None, description="Filter by workspace ID"),
    incident_id: Optional[str] = Query(None, description="Filter by incident ID"),
) -> Dict[str, Any]:
    """Lists alert notification audit logs."""
    logs = alert_dispatcher.get_logs(
        workspace_id=workspace_id,
        incident_id=incident_id,
    )
    return {
        "total": len(logs),
        "logs": [l.to_dict() for l in logs],
    }


# ---------------------------------------------------------------------------
# Swarm Health & Unified Cluster Diagnostics (Priority 4)
# ---------------------------------------------------------------------------

@router.get("/swarm")
def get_swarm_health(
    workspace_id: str = Query("ws-alpha-001", description="Target Workspace ID"),
    details: bool = Query(True, description="Include detailed 14-agent cards"),
    spend_limit_usd: Optional[float] = Query(None, description="Override spend limit in USD"),
) -> Dict[str, Any]:
    """
    Unified Swarm Health & Diagnostic Endpoint.
    Aggregates:
      - 14 Swarm Workers status, badges, and capabilities
      - Sentinel Watchdog anomalies and self-heal task queue
      - Accounting & SpendGuard token/budget metrics
      - Canvas Bridge WebSocket observers and event counts
      - System uptime and resource footprint
    """
    return swarm_health_engine.get_health_status(
        workspace_id=workspace_id,
        include_agent_details=details,
        spend_limit_usd=spend_limit_usd,
    )


@router.post("/swarm/heal")
def trigger_swarm_heal(req: SwarmHealRequest) -> Dict[str, Any]:
    """
    Active Auto-Healing / Resolution Endpoint.
    Resolves Sentinel Watchdog anomalies and archives completed self-healing plans.
    """
    return swarm_health_engine.resolve_or_heal_alert(
        alert_id=req.alert_id,
        action=req.action or "resolve",
        workspace_id=req.workspace_id,
    )


@router.websocket("/swarm/ws")
async def swarm_health_websocket(websocket: WebSocket):
    """
    Real-time streaming WebSocket endpoint for Swarm Health metrics.
    Clients receive an immediate diagnostic snapshot upon connection and
    can send 'refresh', 'heal', or 'ping' messages for live telemetry streaming.
    """
    await websocket.accept()
    try:
        # Initial health snapshot
        initial_status = swarm_health_engine.get_health_status()
        await websocket.send_json({
            "type": "SWARM_HEALTH_SNAPSHOT",
            "data": initial_status,
        })

        while True:
            data = await websocket.receive_json()
            action = data.get("action") or data.get("type")

            if action in ("refresh", "poll", "GET_STATUS"):
                workspace_id = data.get("workspace_id", "ws-alpha-001")
                details = data.get("details", True)
                status_data = swarm_health_engine.get_health_status(
                    workspace_id=workspace_id,
                    include_agent_details=details,
                )
                await websocket.send_json({
                    "type": "SWARM_HEALTH_UPDATE",
                    "data": status_data,
                })
            elif action in ("heal", "HEAL", "auto_heal"):
                alert_id = data.get("alert_id")
                heal_res = swarm_health_engine.resolve_or_heal_alert(alert_id=alert_id)
                new_status = swarm_health_engine.get_health_status()
                await websocket.send_json({
                    "type": "SWARM_HEAL_RESULT",
                    "result": heal_res,
                    "data": new_status,
                })
            elif action in ("ping", "PING"):
                await websocket.send_json({
                    "type": "PONG",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            else:
                await websocket.send_json({
                    "type": "ERROR",
                    "detail": f"Unknown action: {action}. Supported: refresh, heal, ping",
                })
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("Swarm health websocket error: %s", e)

