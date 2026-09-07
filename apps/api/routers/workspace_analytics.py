# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_workspace_analytics"
# purpose: "FastAPI router and WebSocket live streaming for Workspace Analytics, Performance, Users, and Error metrics"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-27"
# --- END DNK-MRH-HEADER ---

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, WebSocket, WebSocketDisconnect, status
from services.dnk_analytics.telemetry_exporter import gemini_telemetry_exporter

from apps.api.db.analytics_storage import MetricType
from apps.api.middleware.tenant_authorization import require_tenant_and_workspace
from apps.api.services.auth_service import auth_service
from apps.api.services.workspace_analytics_service import workspace_analytics_service

router = APIRouter(prefix="/api/v1/analytics", tags=["Workspace Analytics"])


@router.get("/workspaces/{workspace_id}/activity")
async def get_workspace_activity(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace),
    hours: int = Query(default=24, ge=1, le=720),
):
    """Get workspace activity for time range."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    activity = await workspace_analytics_service.get_workspace_activity(
        workspace_id=workspace_id,
        start=start,
        end=end,
    )
    return {
        "workspace_id": workspace_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "activity": activity,
    }


@router.get("/workspaces/{workspace_id}/users")
async def get_workspace_users(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace),
    hours: int = Query(default=24, ge=1, le=720),
):
    """Get user activity in workspace."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    metrics = await workspace_analytics_service.storage.query_metrics(
        MetricType.USER_ACTIVITY,
        start=start,
        end=end,
        workspace_id=workspace_id,
    )
    return {
        "workspace_id": workspace_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "users": metrics,
    }


@router.get("/workspaces/{workspace_id}/performance")
async def get_workspace_performance(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace),
    hours: int = Query(default=24, ge=1, le=720),
):
    """Get performance metrics (latency percentiles)."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    all_metrics = await workspace_analytics_service.storage.query_metrics(
        MetricType.PERFORMANCE,
        start=start,
        end=end,
        workspace_id=workspace_id,
    )
    endpoints: Dict[str, List[float]] = {}
    for m in all_metrics:
        data = m.get("data", {})
        endpoint = data.get("endpoint", "unknown")
        latency = float(data.get("latency_ms", 0))
        endpoints.setdefault(endpoint, []).append(latency)

    performance = {}
    for endpoint, latencies in endpoints.items():
        latencies.sort()
        n = len(latencies)
        performance[endpoint] = {
            "p50": latencies[int(n * 0.50)] if n > 0 else 0,
            "p95": latencies[int(n * 0.95)] if n > 0 else 0,
            "p99": latencies[int(n * 0.99)] if n > 0 else 0,
            "avg": sum(latencies) / n if n > 0 else 0,
            "count": n,
        }

    return {
        "workspace_id": workspace_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "performance": performance,
    }


@router.get("/workspaces/{workspace_id}/errors")
async def get_workspace_errors(
    workspace_id: str,
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace),
    hours: int = Query(default=24, ge=1, le=720),
):
    """Get error metrics."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    errors = await workspace_analytics_service.storage.query_metrics(
        MetricType.ERROR,
        start=start,
        end=end,
        workspace_id=workspace_id,
    )
    return {
        "workspace_id": workspace_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "errors": errors,
    }


@router.get("/users/me/activity")
async def get_user_activity(
    auth_info: Dict[str, Any] = Depends(require_tenant_and_workspace),
    hours: int = Query(default=24, ge=1, le=720),
):
    """Get current user activity."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    user_id = auth_info["user_id"]
    metrics = await workspace_analytics_service.storage.query_metrics(
        MetricType.USER_ACTIVITY,
        start=start,
        end=end,
    )
    user_activity = [m for m in metrics if m.get("data", {}).get("user_id") == user_id]
    return {
        "user_id": user_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "activity": user_activity,
    }


@router.get("/drift/telemetry")
async def get_drift_telemetry() -> Dict[str, Any]:
    """Get Gemini LLM statistical drift and self-healing telemetry for DNK Visual Shell and Grafana."""
    return gemini_telemetry_exporter.export_visual_shell_telemetry()


@router.get("/drift/metrics")
async def get_drift_prometheus_metrics() -> Response:
    """Get Gemini LLM statistical drift and self-healing metrics in Prometheus exposition text format."""
    return Response(
        content=gemini_telemetry_exporter.export_prometheus_text(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.websocket("/workspaces/{workspace_id}/live")
async def get_workspace_live_metrics(
    websocket: WebSocket,
    workspace_id: str,
):
    """WebSocket for real-time metrics streaming."""
    token_str = websocket.query_params.get("token")
    if not token_str:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token_str = auth_header[7:]

    if not token_str:
        await websocket.close(code=4401)
        return

    try:
        payload = auth_service.verify_access_token(token_str)
        user_id = payload.get("sub")
        jwt_tenant_id = payload.get("tenant_id")
        if not user_id or not jwt_tenant_id:
            await websocket.close(code=4401)
            return
    except Exception:
        await websocket.close(code=4401)
        return

    if not auth_service.check_user_workspace_membership(user_id, jwt_tenant_id, workspace_id):
        await websocket.close(code=4403)
        return

    await websocket.accept()

    send_interval = 5.0
    last_send = asyncio.get_event_loop().time() - send_interval

    try:
        while True:
            # Check for client messages (ping/pong/refresh)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=0.1)
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                    elif msg.get("type") == "refresh":
                        last_send = 0.0
                except Exception:
                    pass
            except asyncio.TimeoutError:
                pass

            now = asyncio.get_event_loop().time()
            if now - last_send >= send_interval:
                end = datetime.now(timezone.utc)
                start = end - timedelta(minutes=5)

                activity = await workspace_analytics_service.get_workspace_activity(
                    workspace_id,
                    start,
                    end,
                )
                performance = await workspace_analytics_service.storage.query_metrics(
                    MetricType.PERFORMANCE,
                    start,
                    end,
                    workspace_id=workspace_id,
                )
                errors = await workspace_analytics_service.storage.query_metrics(
                    MetricType.ERROR,
                    start,
                    end,
                    workspace_id=workspace_id,
                )

                perf_latencies = [
                    float(m["data"].get("latency_ms", 0))
                    for m in performance
                    if "data" in m
                ]
                avg_lat = sum(perf_latencies) / len(perf_latencies) if perf_latencies else 0.0

                await websocket.send_json({
                    "type": "metrics_update",
                    "workspace_id": workspace_id,
                    "timestamp": end.isoformat(),
                    "activity_count": len(activity),
                    "performance": {
                        "avg_latency": round(avg_lat, 2),
                        "error_count": len(errors),
                    },
                })
                last_send = now

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
