# --- DNK-MRH-HEADER ---
# mrh_id: "apps_api_routers_platform_deployments"
# purpose: "FastAPI Router for Zero-Downtime Blue/Green & Canary Deployments (DNK-PLATFORM-SCALE-004)"
# author: "DNK-e.com Maksym"
# license: "DNK-INTERNAL"
# canonical_source: true
# alters_files: []
# triggers_tasks: []
# status: "Active"
# version: "1.0.0"
# updated_at: "2026-08-28"
# --- END DNK-MRH-HEADER ---

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from apps.api.services.blue_green_deployment_manager import BlueGreenDeploymentManager
from apps.api.services.canary_analysis_engine import (
    CanaryAnalysisEngine,
    CanaryAnalysisInput,
    CanaryAnalysisResult,
)
from apps.api.services.health_probe_evaluator import (
    HealthProbeEvaluator,
    SLOMetricSnapshot,
)
from apps.api.services.auto_rollback_engine import AutoRollbackEngine
from apps.api.services.gitops_manifest_generator import (
    GitOpsConfig,
    GitOpsManifestGenerator,
)

router = APIRouter(
    prefix="/api/v1/platform/deployments",
    tags=["Platform Deployments & Canary Pipeline"],
)

# Global in-memory registry of deployment managers for testing & runtime orchestration
_DEPLOYMENT_REGISTRY: Dict[str, BlueGreenDeploymentManager] = {}
_ANALYSIS_ENGINE = CanaryAnalysisEngine()
_PROBE_EVALUATOR = HealthProbeEvaluator()
_AUTO_ROLLBACK = AutoRollbackEngine(
    probe_evaluator=_PROBE_EVALUATOR,
    canary_engine=_ANALYSIS_ENGINE,
)


def _get_or_create_manager(config_id: str, app_name: str = "dnk-api") -> BlueGreenDeploymentManager:
    if config_id not in _DEPLOYMENT_REGISTRY:
        _DEPLOYMENT_REGISTRY[config_id] = BlueGreenDeploymentManager(
            config_id=config_id,
            deployment_name=app_name,
            blue_service_name=f"{app_name}-blue",
            green_service_name=f"{app_name}-green",
            initial_image_tag="v1.0.0",
        )
    return _DEPLOYMENT_REGISTRY[config_id]


# Request / Response Schemas
class InitiateDeploymentRequest(BaseModel):
    deployment_id: str
    app_name: str = "dnk-api"
    image_tag: str
    target_traffic_step: int = 0
    auto_rollback_enabled: bool = True


class AdvanceCanaryRequest(BaseModel):
    triggered_by: str = "operator"


class StatisticalAnalysisRequest(BaseModel):
    blue_metrics: Dict[str, Any]
    green_metrics: Dict[str, Any]
    statistical_test: str = "mann_whitney_u"
    allowed_latency_degradation_pct: float = 10.0
    allowed_error_rate_delta: float = 0.005


class RollbackRequest(BaseModel):
    reason: str = "Manual operator rollback requested"


@router.post("/initiate", status_code=status.HTTP_201_CREATED)
def initiate_deployment(payload: InitiateDeploymentRequest) -> Dict[str, Any]:
    """
    Initiates a new deployment candidate on the idle environment (Blue or Green).
    """
    manager = _get_or_create_manager(payload.deployment_id, payload.app_name)
    manager.auto_rollback_enabled = payload.auto_rollback_enabled
    result = manager.trigger_deploy(image_tag=payload.image_tag)
    return {
        "status": "success",
        "deployment_id": payload.deployment_id,
        "details": result,
        "active_environment": manager.active_environment,
        "candidate_environment": manager.get_candidate_environment(),
    }


@router.post("/{deployment_id}/canary/start")
def start_canary_rollout(deployment_id: str) -> Dict[str, Any]:
    """
    Begins progressive canary traffic routing starting at the initial 1% tier.
    """
    if deployment_id not in _DEPLOYMENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    manager = _DEPLOYMENT_REGISTRY[deployment_id]
    result = manager.start_canary()
    return {"status": "success", "deployment_id": deployment_id, "canary_state": result}


@router.post("/{deployment_id}/canary/advance")
def advance_canary_rollout(deployment_id: str, payload: Optional[AdvanceCanaryRequest] = None) -> Dict[str, Any]:
    """
    Advances canary traffic weight to the next step (1% -> 5% -> 25% -> 50% -> 100%).
    """
    if deployment_id not in _DEPLOYMENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    manager = _DEPLOYMENT_REGISTRY[deployment_id]
    triggered_by = payload.triggered_by if payload else "operator"
    result = manager.advance_canary_step(triggered_by=triggered_by)
    return {"status": "success", "deployment_id": deployment_id, "progress": result}


@router.post("/{deployment_id}/canary/analyze")
def run_canary_statistical_analysis(deployment_id: str, payload: StatisticalAnalysisRequest) -> Dict[str, Any]:
    """
    Executes statistical significance tests (Mann-Whitney U, Welch's T-test) on candidate metrics.
    """
    if deployment_id not in _DEPLOYMENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")

    analysis_input = CanaryAnalysisInput(
        deployment_id=deployment_id,
        blue_metrics=payload.blue_metrics,
        green_metrics=payload.green_metrics,
        statistical_test=payload.statistical_test,
        allowed_latency_degradation_pct=payload.allowed_latency_degradation_pct,
        allowed_error_rate_delta=payload.allowed_error_rate_delta,
    )
    analysis_res = _ANALYSIS_ENGINE.analyze_canary(analysis_input)
    return {"status": "success", "analysis": analysis_res.model_dump()}


@router.post("/{deployment_id}/promote")
def promote_candidate_deployment(deployment_id: str) -> Dict[str, Any]:
    """
    Promotes candidate environment to full active status (100% traffic, idle candidate).
    """
    if deployment_id not in _DEPLOYMENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    manager = _DEPLOYMENT_REGISTRY[deployment_id]
    result = manager.promote(triggered_by="operator_api")
    return {"status": "success", "deployment_id": deployment_id, "promotion": result}


@router.post("/{deployment_id}/rollback")
def rollback_deployment(deployment_id: str, payload: Optional[RollbackRequest] = None) -> Dict[str, Any]:
    """
    Executes an instantaneous zero-downtime rollback, restoring 100% traffic to the active baseline.
    """
    if deployment_id not in _DEPLOYMENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    manager = _DEPLOYMENT_REGISTRY[deployment_id]
    reason = payload.reason if payload else "Manual API trigger"
    result = manager.rollback(reason=reason, triggered_by="operator_api")
    return {"status": "success", "deployment_id": deployment_id, "rollback": result}


@router.get("/{deployment_id}/status")
def get_deployment_status(deployment_id: str) -> Dict[str, Any]:
    """
    Retrieves the real-time status and telemetry breakdown of the deployment.
    """
    if deployment_id not in _DEPLOYMENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    manager = _DEPLOYMENT_REGISTRY[deployment_id]
    return {
        "status": "success",
        "deployment_id": deployment_id,
        "active_environment": manager.active_environment,
        "candidate_environment": manager.get_candidate_environment(),
        "canary_enabled": manager.canary_enabled,
        "current_canary_step_index": manager.current_step_index,
        "environments": {
            k: {
                "environment_name": v.environment_name,
                "service_name": v.service_name,
                "status": v.status,
                "image_tag": v.image_tag,
                "traffic_percentage": v.traffic_percentage,
                "deployed_at": v.deployed_at.isoformat() if v.deployed_at else None,
            }
            for k, v in manager.environments.items()
        },
        "event_history_count": len(manager.history_events),
    }


@router.get("/{deployment_id}/manifests")
def get_deployment_gitops_manifests(
    deployment_id: str,
    provider: str = Query(default="nginx", description="Traffic routing provider: 'nginx' or 'istio'"),
) -> Dict[str, Any]:
    """
    Generates ready-to-apply ArgoCD Rollouts, Applications, and Flux CD Kustomizations.
    """
    if deployment_id not in _DEPLOYMENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    manager = _DEPLOYMENT_REGISTRY[deployment_id]

    gitops_config = GitOpsConfig(
        app_name=manager.deployment_name,
        current_tag=manager.environments[manager.get_candidate_environment()].image_tag or "v1.0.0",
        traffic_routing_provider=provider,
    )
    generator = GitOpsManifestGenerator(gitops_config)
    return {
        "status": "success",
        "deployment_id": deployment_id,
        "provider": provider,
        "argo_rollout": generator.generate_argo_rollout(),
        "argo_application": generator.generate_argo_application(),
        "flux_kustomization": generator.generate_flux_kustomization(),
        "yaml_bundle": generator.export_all_yaml(),
    }


@router.get("/metrics")
def get_deployment_prometheus_metrics() -> Response:
    """
    Exports OpenMetrics/Prometheus formatted gauge and counter metrics for all managed deployments.
    """
    lines: List[str] = [
        "# HELP dnk_platform_deployment_traffic_percentage Traffic percentage allocated per environment",
        "# TYPE dnk_platform_deployment_traffic_percentage gauge",
    ]

    for dep_id, mgr in _DEPLOYMENT_REGISTRY.items():
        for env_name, env_data in mgr.environments.items():
            lines.append(
                f'dnk_platform_deployment_traffic_percentage{{deployment_id="{dep_id}",environment="{env_name}",app="{mgr.deployment_name}"}} {env_data.traffic_percentage}'
            )

    lines.append("# HELP dnk_platform_deployment_canary_active 1 if canary traffic shifting is active, 0 otherwise")
    lines.append("# TYPE dnk_platform_deployment_canary_active gauge")
    for dep_id, mgr in _DEPLOYMENT_REGISTRY.items():
        val = 1 if mgr.canary_enabled else 0
        lines.append(
            f'dnk_platform_deployment_canary_active{{deployment_id="{dep_id}",app="{mgr.deployment_name}"}} {val}'
        )

    return Response(content="\n".join(lines) + "\n", media_type="text/plain; version=0.0.4; charset=utf-8")
