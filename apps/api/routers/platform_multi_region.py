# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_platform_multi_region"
# purpose: "FastAPI REST & WebSocket Router for Multi-Region Deployment & Edge Routing (DNK-PLATFORM-SCALE-003)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Query, Path, Body
from pydantic import BaseModel, Field

from apps.api.services.multi_region_deployer import MultiRegionDeployer
from apps.api.services.global_load_balancer import GlobalLoadBalancer
from apps.api.services.edge_routing_manager import EdgeRoutingManager
from apps.api.services.cross_region_replication import CrossRegionReplicationManager

router = APIRouter(prefix="/api/v1/platform", tags=["Platform Multi-Region"])

# Singleton service instances
deployer_service = MultiRegionDeployer()
gslb_service = GlobalLoadBalancer(deployer=deployer_service)
edge_service = EdgeRoutingManager()
replication_service = CrossRegionReplicationManager()


# --- Pydantic Schemas ---
class RegionCreateRequest(BaseModel):
    region_name: str = Field(..., description="Region name e.g. us-east-1")
    cloud_provider: str = Field(..., description="Cloud provider e.g. aws, gcp")
    health_check_endpoint: str = Field(..., description="Health check endpoint URL")
    is_primary: bool = False
    is_active: bool = True
    failover_priority: int = 0


class RegionUpdateRequest(BaseModel):
    cloud_provider: Optional[str] = None
    health_check_endpoint: Optional[str] = None
    is_primary: Optional[bool] = None
    is_active: Optional[bool] = None
    failover_priority: Optional[int] = None


class GSLBConfigUpdateRequest(BaseModel):
    dns_provider: Optional[str] = Field(None, description="DNS provider e.g. route53, cloud_dns, cloudflare")
    routing_policy: Optional[str] = Field(None, description="Routing policy e.g. latency, geolocation, weighted, failover")
    health_check_interval_seconds: Optional[int] = Field(None, description="Health check interval in seconds")
    failover_threshold: Optional[int] = Field(None, description="Failover threshold count")
    ttl_seconds: Optional[int] = Field(None, description="DNS TTL in seconds")


class EdgeRoutingRuleCreateRequest(BaseModel):
    rule_name: str = Field(..., description="Rule name")
    geo_match_type: str = Field(..., description="Geo match type: country, continent, latency")
    geo_values: List[str] = Field(..., description="Geo values list e.g. ['NA', 'US']")
    target_region: str = Field(..., description="Target region name")
    priority: int = 0
    enabled: bool = True


class EdgeRoutingRuleUpdateRequest(BaseModel):
    rule_name: Optional[str] = None
    geo_match_type: Optional[str] = None
    geo_values: Optional[List[str]] = None
    target_region: Optional[str] = None
    priority: Optional[int] = None
    enabled: Optional[bool] = None


# --- Region Management Endpoints ---
@router.post("/regions")
async def create_region(payload: RegionCreateRequest):
    region = deployer_service.register_region(
        region_name=payload.region_name,
        cloud_provider=payload.cloud_provider,
        health_check_endpoint=payload.health_check_endpoint,
        is_primary=payload.is_primary,
        is_active=payload.is_active,
        failover_priority=payload.failover_priority,
    )
    return {"status": "success", "region": region}


@router.get("/regions")
async def list_regions(active_only: bool = Query(False)):
    regions = deployer_service.list_regions(active_only=active_only)
    return {"status": "success", "regions": regions, "count": len(regions)}


@router.get("/regions/{name}")
async def get_region(name: str = Path(...)):
    region = deployer_service.get_region(name)
    if not region:
        raise HTTPException(status_code=404, detail=f"Region '{name}' not found")
    metric = deployer_service.get_latest_health_metric(name)
    return {"status": "success", "region": region, "latest_metric": metric}


@router.put("/regions/{name}")
async def update_region(name: str = Path(...), payload: RegionUpdateRequest = Body(...)):
    updates = payload.dict(exclude_unset=True)
    updated = deployer_service.update_region(name, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Region '{name}' not found")
    return {"status": "success", "region": updated}


@router.delete("/regions/{name}")
async def delete_region(name: str = Path(...)):
    deleted = deployer_service.delete_region(name)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Region '{name}' not found")
    return {"status": "success", "message": f"Region '{name}' deleted"}


@router.post("/regions/{name}/health")
async def trigger_region_health_check(name: str = Path(...)):
    result = deployer_service.trigger_liveness_check(name)
    if result.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"Region '{name}' not found")
    return {"status": "success", "health_check": result}


# --- Global Load Balancer Endpoints ---
@router.post("/gslb/config")
@router.get("/gslb/config")
async def get_gslb_config():
    config = gslb_service.get_config()
    return {"status": "success", "config": config}


@router.put("/gslb/config")
async def update_gslb_config(payload: GSLBConfigUpdateRequest):
    updates = payload.dict(exclude_unset=True)
    config = gslb_service.update_config(updates)
    return {"status": "success", "config": config}


@router.get("/gslb/route")
async def calculate_gslb_route(
    client_country: Optional[str] = Query(None),
    client_continent: Optional[str] = Query(None),
):
    target = gslb_service.calculate_routing_target(
        client_country=client_country,
        client_continent=client_continent,
    )
    return {"status": "success", "routing": target}


# --- Edge Routing Endpoints ---
@router.post("/edge-routing/rules")
async def create_edge_routing_rule(payload: EdgeRoutingRuleCreateRequest):
    rule = edge_service.create_rule(
        rule_name=payload.rule_name,
        geo_match_type=payload.geo_match_type,
        geo_values=payload.geo_values,
        target_region=payload.target_region,
        priority=payload.priority,
        enabled=payload.enabled,
    )
    return {"status": "success", "rule": rule}


@router.get("/edge-routing/rules")
async def list_edge_routing_rules(enabled_only: bool = Query(False)):
    rules = edge_service.list_rules(enabled_only=enabled_only)
    return {"status": "success", "rules": rules, "count": len(rules)}


@router.put("/edge-routing/rules/{rule_id}")
async def update_edge_routing_rule(rule_id: str = Path(...), payload: EdgeRoutingRuleUpdateRequest = Body(...)):
    updates = payload.dict(exclude_unset=True)
    updated = edge_service.update_rule(rule_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
    return {"status": "success", "rule": updated}


@router.delete("/edge-routing/rules/{rule_id}")
async def delete_edge_routing_rule(rule_id: str = Path(...)):
    deleted = edge_service.delete_rule(rule_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Rule '{rule_id}' not found")
    return {"status": "success", "message": f"Rule '{rule_id}' deleted"}


# --- Cross-Region Replication Endpoints ---
@router.get("/replication/status")
async def get_replication_status():
    streams = replication_service.list_streams()
    return {"status": "success", "streams": streams, "count": len(streams)}


@router.get("/replication/lag")
async def get_replication_lag():
    metrics = replication_service.get_aggregate_replication_lag()
    return {"status": "success", "metrics": metrics}


# --- Live Telemetry WebSocket ---
@router.websocket("/regions/live")
async def live_region_health_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            regions = deployer_service.list_regions()
            telemetry = []
            for r in regions:
                metric = deployer_service.get_latest_health_metric(r["region_name"])
                telemetry.append({
                    "region": r["region_name"],
                    "is_primary": r["is_primary"],
                    "is_active": r["is_active"],
                    "metric": metric,
                })
            await websocket.send_json({"type": "region_telemetry", "data": telemetry})
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        pass
