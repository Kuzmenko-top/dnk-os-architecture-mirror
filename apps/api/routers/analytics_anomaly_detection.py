# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_analytics_anomaly_detection"
# purpose: "FastAPI REST & WebSocket Router for Real-Time Anomaly Detection & Advanced Alerting (DNK-ANALYTICS-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, Path, Body
from pydantic import BaseModel, Field

from apps.api.services.real_time_anomaly_detector import RealTimeAnomalyDetector
from apps.api.services.dynamic_threshold_calculator import DynamicThresholdCalculator
from apps.api.services.advanced_alerting_engine import AdvancedAlertingEngine
from apps.api.services.alert_channel_dispatcher import AlertChannelDispatcher

router = APIRouter(prefix="/api/v1", tags=["Analytics Anomaly Detection & Alerting"])

# Singleton service instances
anomaly_detector = RealTimeAnomalyDetector()
threshold_calculator = DynamicThresholdCalculator()
alerting_engine = AdvancedAlertingEngine()
channel_dispatcher = AlertChannelDispatcher()

# In-memory storage for active session
CONFIGS_DB: Dict[str, Dict[str, Any]] = {}
THRESHOLDS_DB: Dict[str, Dict[str, Any]] = {}
ANOMALY_EVENTS_DB: Dict[str, Dict[str, Any]] = {}
ALERT_RULES_DB: Dict[str, Dict[str, Any]] = {}
ALERT_EVENTS_DB: Dict[str, Dict[str, Any]] = {}
ALERT_CHANNELS_DB: Dict[str, Dict[str, Any]] = {}

# --- Pydantic Schemas ---
class AnomalyDetectionConfigCreate(BaseModel):
    workspace_id: str = Field(..., description="Workspace ID")
    metric_type: str = Field(..., description="e.g. latency_p95, error_rate, queue_depth, request_count")
    detector_type: str = Field("zscore", description="zscore, iqr, holt_winters, isolation_forest")
    sensitivity: float = Field(0.80, ge=0.0, le=1.0)
    rolling_window_hours: int = Field(24, ge=1, le=168)
    enabled: bool = True

class AnomalyDetectionConfigUpdate(BaseModel):
    metric_type: Optional[str] = None
    detector_type: Optional[str] = None
    sensitivity: Optional[float] = Field(None, ge=0.0, le=1.0)
    rolling_window_hours: Optional[int] = Field(None, ge=1, le=168)
    enabled: Optional[bool] = None

class AdvancedAlertRuleCreate(BaseModel):
    workspace_id: str
    rule_name: str
    composite_logic: Dict[str, Any] = Field(..., description='e.g. {"and": [{"metric": "error_rate", "operator": "gt", "value": 0.05}]}')
    severity: str = Field("warning", description="info, warning, critical")
    cooldown_seconds: int = Field(300, ge=0)
    enabled: bool = True

class AdvancedAlertRuleUpdate(BaseModel):
    rule_name: Optional[str] = None
    composite_logic: Optional[Dict[str, Any]] = None
    severity: Optional[str] = None
    cooldown_seconds: Optional[int] = None
    enabled: Optional[bool] = None

class AlertChannelConfigCreate(BaseModel):
    workspace_id: str
    channel_type: str = Field(..., description="telegram, slack, pagerduty, email")
    channel_config: Dict[str, Any] = Field(..., description="Webhook URLs, bot tokens, recipients")
    enabled: bool = True

class AlertChannelConfigUpdate(BaseModel):
    channel_type: Optional[str] = None
    channel_config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None

# --- Endpoints: Anomaly Detection Configs ---
@router.post("/anomaly-detection/configs", response_model=Dict[str, Any])
def create_anomaly_config(payload: AnomalyDetectionConfigCreate):
    cfg_id = str(uuid.uuid4())
    cfg_data = {
        "id": cfg_id,
        "workspace_id": payload.workspace_id,
        "metric_type": payload.metric_type,
        "detector_type": payload.detector_type,
        "sensitivity": payload.sensitivity,
        "rolling_window_hours": payload.rolling_window_hours,
        "enabled": payload.enabled,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    CONFIGS_DB[cfg_id] = cfg_data
    return cfg_data

@router.get("/anomaly-detection/configs", response_model=List[Dict[str, Any]])
def list_anomaly_configs(workspace_id: Optional[str] = Query(None)):
    if workspace_id:
        return [c for c in CONFIGS_DB.values() if c.get("workspace_id") == workspace_id]
    return list(CONFIGS_DB.values())

@router.put("/anomaly-detection/configs/{config_id}", response_model=Dict[str, Any])
def update_anomaly_config(config_id: str, payload: AnomalyDetectionConfigUpdate):
    if config_id not in CONFIGS_DB:
        raise HTTPException(status_code=444, detail="Config not found")
    cfg = CONFIGS_DB[config_id]
    for k, v in payload.model_dump(exclude_unset=True).items():
        cfg[k] = v
    cfg["updated_at"] = datetime.now(timezone.utc).isoformat()
    return cfg

@router.delete("/anomaly-detection/configs/{config_id}", response_model=Dict[str, Any])
def delete_anomaly_config(config_id: str):
    if config_id not in CONFIGS_DB:
        raise HTTPException(status_code=404, detail="Config not found")
    removed = CONFIGS_DB.pop(config_id)
    return {"status": "deleted", "id": config_id}

# --- Endpoints: Dynamic Thresholds ---
@router.get("/anomaly-detection/thresholds", response_model=List[Dict[str, Any]])
def get_dynamic_thresholds(workspace_id: Optional[str] = Query(None)):
    if workspace_id:
        return [t for t in THRESHOLDS_DB.values() if t.get("workspace_id") == workspace_id]
    return list(THRESHOLDS_DB.values())

@router.post("/anomaly-detection/thresholds/recalculate", response_model=Dict[str, Any])
def recalculate_dynamic_thresholds(
    workspace_id: str = Query(...),
    metric_type: str = Query(...),
    historical_values: List[float] = Body(...)
):
    stats = threshold_calculator.compute_thresholds(historical_values)
    th_id = str(uuid.uuid4())
    th_data = {
        "id": th_id,
        "workspace_id": workspace_id,
        "metric_type": metric_type,
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        **stats,
    }
    THRESHOLDS_DB[th_id] = th_data
    return th_data

# --- Endpoints: Anomaly Events ---
@router.get("/anomaly-detection/events", response_model=List[Dict[str, Any]])
def list_anomaly_events(workspace_id: Optional[str] = Query(None)):
    if workspace_id:
        return [e for e in ANOMALY_EVENTS_DB.values() if e.get("workspace_id") == workspace_id]
    return list(ANOMALY_EVENTS_DB.values())

@router.get("/anomaly-detection/events/{event_id}", response_model=Dict[str, Any])
def get_anomaly_event(event_id: str):
    if event_id not in ANOMALY_EVENTS_DB:
        raise HTTPException(status_code=404, detail="Anomaly event not found")
    return ANOMALY_EVENTS_DB[event_id]

# --- Endpoints: Advanced Alert Rules ---
@router.post("/alerts/rules/advanced", response_model=Dict[str, Any])
def create_advanced_alert_rule(payload: AdvancedAlertRuleCreate):
    rule_id = str(uuid.uuid4())
    rule_data = {
        "id": rule_id,
        "workspace_id": payload.workspace_id,
        "rule_name": payload.rule_name,
        "composite_logic": payload.composite_logic,
        "severity": payload.severity,
        "cooldown_seconds": payload.cooldown_seconds,
        "enabled": payload.enabled,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    ALERT_RULES_DB[rule_id] = rule_data
    return rule_data

@router.get("/alerts/rules/advanced", response_model=List[Dict[str, Any]])
def list_advanced_alert_rules(workspace_id: Optional[str] = Query(None)):
    if workspace_id:
        return [r for r in ALERT_RULES_DB.values() if r.get("workspace_id") == workspace_id]
    return list(ALERT_RULES_DB.values())

@router.put("/alerts/rules/advanced/{rule_id}", response_model=Dict[str, Any])
def update_advanced_alert_rule(rule_id: str, payload: AdvancedAlertRuleUpdate):
    if rule_id not in ALERT_RULES_DB:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    rule = ALERT_RULES_DB[rule_id]
    for k, v in payload.model_dump(exclude_unset=True).items():
        rule[k] = v
    rule["updated_at"] = datetime.now(timezone.utc).isoformat()
    return rule

@router.delete("/alerts/rules/advanced/{rule_id}", response_model=Dict[str, Any])
def delete_advanced_alert_rule(rule_id: str):
    if rule_id not in ALERT_RULES_DB:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    ALERT_RULES_DB.pop(rule_id)
    return {"status": "deleted", "id": rule_id}

# --- Endpoints: Alert Events (Advanced) ---
@router.get("/alerts/events/advanced", response_model=List[Dict[str, Any]])
def list_advanced_alert_events(workspace_id: Optional[str] = Query(None)):
    if workspace_id:
        return [e for e in ALERT_EVENTS_DB.values() if e.get("workspace_id") == workspace_id]
    return list(ALERT_EVENTS_DB.values())

@router.post("/alerts/events/advanced/{event_id}/resolve", response_model=Dict[str, Any])
def resolve_advanced_alert_event(event_id: str, note: str = Body("Resolved manually", embed=True)):
    if event_id not in ALERT_EVENTS_DB:
        raise HTTPException(status_code=404, detail="Alert event not found")
    evt = ALERT_EVENTS_DB[event_id]
    evt["resolved_at"] = datetime.now(timezone.utc).isoformat()
    evt["resolution_note"] = note
    return evt

# --- Endpoints: Alert Channel Configs ---
@router.post("/alerts/channels", response_model=Dict[str, Any])
def create_alert_channel_config(payload: AlertChannelConfigCreate):
    ch_id = str(uuid.uuid4())
    ch_data = {
        "id": ch_id,
        "workspace_id": payload.workspace_id,
        "channel_type": payload.channel_type,
        "channel_config": payload.channel_config,
        "enabled": payload.enabled,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ALERT_CHANNELS_DB[ch_id] = ch_data
    return ch_data

@router.get("/alerts/channels", response_model=List[Dict[str, Any]])
def list_alert_channel_configs(workspace_id: Optional[str] = Query(None)):
    if workspace_id:
        return [c for c in ALERT_CHANNELS_DB.values() if c.get("workspace_id") == workspace_id]
    return list(ALERT_CHANNELS_DB.values())

@router.put("/alerts/channels/{channel_id}", response_model=Dict[str, Any])
def update_alert_channel_config(channel_id: str, payload: AlertChannelConfigUpdate):
    if channel_id not in ALERT_CHANNELS_DB:
        raise HTTPException(status_code=404, detail="Channel config not found")
    ch = ALERT_CHANNELS_DB[channel_id]
    for k, v in payload.model_dump(exclude_unset=True).items():
        ch[k] = v
    return ch

@router.delete("/alerts/channels/{channel_id}", response_model=Dict[str, Any])
def delete_alert_channel_config(channel_id: str):
    if channel_id not in ALERT_CHANNELS_DB:
        raise HTTPException(status_code=404, detail="Channel config not found")
    ALERT_CHANNELS_DB.pop(channel_id)
    return {"status": "deleted", "id": channel_id}

@router.post("/alerts/channels/{channel_id}/test", response_model=Dict[str, Any])
def test_alert_channel_delivery(channel_id: str):
    if channel_id not in ALERT_CHANNELS_DB:
        raise HTTPException(status_code=404, detail="Channel config not found")
    ch = ALERT_CHANNELS_DB[channel_id]
    dummy_alert = {
        "rule_name": "Test Alert Delivery",
        "severity": "info",
        "workspace_id": ch.get("workspace_id", "default"),
        "triggered_at": datetime.now(timezone.utc).isoformat(),
        "details": "This is a test alert notification from DNK OS.",
    }
    res = channel_dispatcher.dispatch_alert(dummy_alert, [ch])
    return {"status": "test_completed", "delivery_result": res}

# --- WebSockets ---
@router.websocket("/anomaly-detection/live")
async def websocket_anomaly_live(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "type": "anomaly_telemetry",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {
                    "latency_p95": 125.4,
                    "error_rate": 0.002,
                    "anomaly_score": 0.05,
                }
            })
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        pass

@router.websocket("/alerts/live")
async def websocket_alerts_live(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json({
                "type": "alert_stream",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "active_alerts_count": len([e for e in ALERT_EVENTS_DB.values() if not e.get("resolved_at")]),
            })
            await asyncio.sleep(3.0)
    except WebSocketDisconnect:
        pass
